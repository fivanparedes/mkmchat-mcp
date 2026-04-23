"""HTTP Server for MK Mobile Assistant API"""

import asyncio
import hmac
import json
import logging
import os
import re
from collections import defaultdict, deque
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import monotonic
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict, Tuple, Set

from mkmchat.llm.ollama import get_ollama_assistant
from mkmchat.tools.semantic_search import get_rag_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default port
DEFAULT_PORT = 8080

_IP_REQUESTS = defaultdict(deque)
_IP_BURST_REQUESTS = defaultdict(deque)


def _get_http_timeout_seconds() -> int:
    try:
        value = int(os.getenv("MKM_HTTP_TIMEOUT_SECONDS", "120"))
        return max(10, value)
    except ValueError:
        return 120


def _debug_prompts_enabled() -> bool:
    return os.getenv("MKM_DEBUG_PROMPTS", "false").strip().lower() == "true"


def _redact_sensitive_text(text: str) -> str:
    redacted = re.sub(
        r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*([^\s\n,;]+)",
        r"\1=[REDACTED]",
        text,
    )
    redacted = re.sub(r"(?i)(bearer\s+)([A-Za-z0-9._\-]+)", r"\1[REDACTED]", redacted)
    return redacted


def _log_debug_interaction(tag: str, system_prompt: str, user_prompt: str, response_text: str):
    """Log LLM interaction for debugging purposes if enabled."""
    if not _debug_prompts_enabled():
        return

    from pathlib import Path
    from datetime import datetime

    try:
        # Use /app/debug_llm.log if possible, otherwise local dir
        log_file = Path("/app/debug_llm.log")
        if not log_file.parent.exists():
            log_file = Path(__file__).resolve().parent / "debug_llm.log"
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"TIMESTAMP: {timestamp} | TAG: {tag}\n")
            f.write(f"{'-'*80}\n")
            f.write(f"SYSTEM PROMPT:\n{_redact_sensitive_text(system_prompt)}\n")
            f.write(f"{'-'*80}\n")
            f.write(f"USER PROMPT / QUERY:\n{_redact_sensitive_text(user_prompt)}\n")
            f.write(f"{'-'*80}\n")
            f.write(f"LLM RESPONSE:\n{response_text}\n")
            f.write(f"{'='*80}\n")
        logger.info(f"Interaction ({tag}) logged to {log_file}")
    except Exception as e:
        logger.error(f"Failed to write debug log: {repr(e)}")


def _resolve_runtime_data_dir() -> "Path":
    from pathlib import Path

    package_dir = Path(__file__).resolve().parent
    repo_data_dir = package_dir.parent / "data"
    if any(repo_data_dir.glob("*.tsv")) or any(repo_data_dir.glob("*.txt")):
        return repo_data_dir
    return package_dir / "data"


def _safe_positive_int(value: str, fallback: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else fallback
    except ValueError:
        return fallback


def _sanitize_chat_messages(messages: object) -> List[Dict[str, str]]:
    if not isinstance(messages, list):
        return []

    sanitized: List[Dict[str, str]] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"}:
            continue
        if not content:
            continue
        sanitized.append({"role": role, "content": content})
    return sanitized


def _chat_query_variants(query: str) -> List[str]:
    q = (query or "").strip()
    if not q:
        return []

    variants: List[str] = [q]

    lowered = q.lower()
    if "classic" in lowered and "klassic" not in lowered:
        variants.append(re.sub(r"\bclassic\b", "klassic", q, flags=re.IGNORECASE))
    if "klassic" in lowered and "classic" not in lowered:
        variants.append(re.sub(r"\bklassic\b", "classic", q, flags=re.IGNORECASE))

    # Deduplicate while preserving order.
    dedup: List[str] = []
    seen = set()
    for v in variants:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            dedup.append(v.strip())
    return dedup


_MATCH_STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "from", "that", "this", "what", "which", "about",
    "tell", "show", "give", "does", "how", "when", "where", "why", "who", "into",
    "can", "are", "is", "was", "were", "have", "has", "had", "please", "need",
    "character", "characters", "variant", "variants",
}


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower()).strip()


def _tokenize_for_match(text: str) -> Set[str]:
    normalized = _normalize_for_match(text)
    return {
        token
        for token in normalized.split()
        if len(token) >= 3 and token not in _MATCH_STOPWORDS
    }


# ---------------------------------------------------------------------------
# Query intent classification
# ---------------------------------------------------------------------------

_INTENT_MECHANIC_PATTERNS = re.compile(
    r"\bwhat (is|are|does)\b|\bhow (does|do|to)\b|\bexplain\b|\bdefinition\b"
    r"|\bmechanic\b|\bbuff\b|\bdebuff\b|\beffect\b|\bstatus\b",
    re.IGNORECASE,
)

_INTENT_EQUIPMENT_PATTERNS = re.compile(
    r"\bequipment\b|\bweapon\b|\barmor\b|\baccessor(y|ies)\b|\bgear\b"
    r"|\bfusion\b|\bslot\b|\bbrutality\b|\bfriendship\b",
    re.IGNORECASE,
)

_INTENT_TEAM_PATTERNS = re.compile(
    r"\bteam\b|\bcomposition\b|\bsynergy\b|\bsynergies\b|\bstarter\b"
    r"|\bsupport\b|\bstrateg(y|ies)\b|\bbest.*character\b|\brecommend\b",
    re.IGNORECASE,
)

_INTENT_CHARACTER_PATTERNS = re.compile(
    r"\bcharacter\b|\bfighter\b|\bpassive\b|\brarity\b|\btier\b|\bclass\b"
    r"|\bspecial attack\b|\bsp1\b|\bsp2\b|\bxray\b|\bx-ray\b",
    re.IGNORECASE,
)


def _classify_query_intent(query: str) -> Set[str]:
    """Return the set of doc types most relevant for this query.

    Falls back to all four types when intent is ambiguous.
    The result guides which RAG sub-searches are performed so that
    irrelevant passages don't pollute the LLM prompt.
    """
    q = (query or "").strip()
    if not q:
        return {"character", "equipment", "gameplay", "glossary"}

    wants_mechanic = bool(_INTENT_MECHANIC_PATTERNS.search(q))
    wants_equipment = bool(_INTENT_EQUIPMENT_PATTERNS.search(q))
    wants_team = bool(_INTENT_TEAM_PATTERNS.search(q))
    wants_character = bool(_INTENT_CHARACTER_PATTERNS.search(q))

    intent: Set[str] = set()

    if wants_mechanic:
        intent.update({"gameplay", "glossary"})
    if wants_equipment:
        intent.update({"equipment", "gameplay"})
    if wants_team:
        intent.update({"character", "equipment", "gameplay"})
    if wants_character:
        intent.update({"character"})

    # Always include glossary for definitions, and gameplay for context
    if intent:
        intent.update({"glossary"})

    return intent if intent else {"character", "equipment", "gameplay", "glossary"}


def _build_chat_retrieval_query(current_message: str, recent_messages: List[Dict[str, str]]) -> str:
    """Build a retrieval query using current message + recent user turns."""
    user_turns = [
        str(item.get("content", "")).strip()
        for item in recent_messages
        if str(item.get("role", "")).strip().lower() == "user"
    ]
    seed_parts = user_turns[-3:] + [str(current_message or "").strip()]

    dedup_parts: List[str] = []
    seen = set()
    for part in seed_parts:
        key = part.lower()
        if part and key not in seen:
            seen.add(key)
            dedup_parts.append(part)

    merged = " ".join(dedup_parts)
    return merged[:900]


def _extract_passive(doc_content: str) -> str:
    for line in doc_content.split("\n"):
        if line.startswith("Passive:"):
            return line.replace("Passive:", "").strip()
    return ""


def _search_with_variants(
    rag,
    query: str,
    *,
    doc_type: str,
    top_k_per_variant: int,
    min_similarity: float,
) -> List[Tuple[object, float]]:
    variants = _chat_query_variants(query)
    search_variants = variants or [query]
    pool: Dict[int, Tuple[object, float]] = {}

    for variant in search_variants:
        for doc, score in rag.search(
            variant,
            top_k=top_k_per_variant,
            doc_type=doc_type,
            min_similarity=min_similarity,
        ):
            key = id(doc)
            existing = pool.get(key)
            if not existing or score > existing[1]:
                pool[key] = (doc, score)

    return sorted(pool.values(), key=lambda x: x[1], reverse=True)


def _retrieve_character_items(
    rag,
    query: str,
    *,
    top_k_semantic: int,
    top_k_final: int,
    min_similarity: float,
) -> List[Tuple[object, float]]:
    character_pool: Dict[int, Tuple[object, float]] = {}

    def _upsert_character(doc: object, score: float) -> None:
        key = id(doc)
        existing = character_pool.get(key)
        if not existing or score > existing[1]:
            character_pool[key] = (doc, score)

    for doc, score in _search_with_variants(
        rag,
        query,
        doc_type="character",
        top_k_per_variant=top_k_semantic,
        min_similarity=min_similarity,
    ):
        _upsert_character(doc, score)

    search_variants = _chat_query_variants(query) or [query]
    full_query = " ".join(search_variants).strip()
    lowered_query = full_query.lower()
    query_norm = _normalize_for_match(full_query)
    query_terms = _tokenize_for_match(full_query)

    for doc in rag.documents:
        if doc.doc_type != "character":
            continue
        name = str(doc.metadata.get("name", "")).strip()
        if not name:
            continue

        name_norm = _normalize_for_match(name)
        name_terms = _tokenize_for_match(name)
        overlap = len(query_terms & name_terms) if name_terms else 0
        coverage = (overlap / len(name_terms)) if name_terms else 0.0

        lexical_score: Optional[float] = None
        if name.lower() in lowered_query or (name_norm and name_norm in query_norm):
            lexical_score = 0.995
        elif overlap >= 2 and coverage >= 0.5:
            lexical_score = 0.94 + min(0.04, overlap * 0.01)
        elif len(name_terms) <= 2 and overlap >= 1 and coverage >= 0.8:
            lexical_score = 0.93

        if lexical_score is not None:
            _upsert_character(doc, lexical_score)

    character_items: List[Tuple[object, float]] = list(character_pool.values())
    character_items.sort(key=lambda x: x[1], reverse=True)
    return character_items[:top_k_final]


def _retrieve_equipment_items(
    rag,
    query: str,
    *,
    top_k_per_variant: int,
    top_k_final: int,
    min_similarity: float,
) -> List[Tuple[object, float]]:
    """Retrieve equipment with semantic search + lexical boost + tier boost."""
    equipment_pool: Dict[int, Tuple[object, float]] = {}

    def _upsert_equipment(doc: object, score: float) -> None:
        key = id(doc)
        existing = equipment_pool.get(key)
        if not existing or score > existing[1]:
            equipment_pool[key] = (doc, score)

    # 1. Semantic search
    for doc, score in _search_with_variants(
        rag,
        query,
        doc_type="equipment",
        top_k_per_variant=top_k_per_variant,
        min_similarity=min_similarity,
    ):
        _upsert_equipment(doc, score)

    # 2. Lexical matching
    search_variants = _chat_query_variants(query) or [query]
    full_query = " ".join(search_variants).strip()
    lowered_query = full_query.lower()
    query_norm = _normalize_for_match(full_query)
    query_terms = _tokenize_for_match(full_query)

    for doc in rag.documents:
        if doc.doc_type != "equipment":
            continue
        
        name = str(doc.metadata.get("name", "")).strip()
        if not name:
            continue

        name_norm = _normalize_for_match(name)
        name_terms = _tokenize_for_match(name)
        overlap = len(query_terms & name_terms) if name_terms else 0
        coverage = (overlap / len(name_terms)) if name_terms else 0.0

        lexical_score: Optional[float] = None
        # Name match
        if name.lower() in lowered_query or (name_norm and name_norm in query_norm):
            lexical_score = 0.99
        # Strong keyword match
        elif overlap >= 2 and coverage >= 0.5:
            lexical_score = 0.92 + min(0.05, overlap * 0.01)
        # Content match (Brutality/Friendship for character)
        else:
            content_norm = _normalize_for_match(doc.content)
            content_terms = _tokenize_for_match(doc.content)
            content_overlap = len(query_terms & content_terms)
            if content_overlap >= 3:
                lexical_score = 0.85 + min(0.1, content_overlap * 0.01)

        if lexical_score is not None:
            _upsert_equipment(doc, lexical_score)

    # 3. Apply Tier Boost
    final_results = []
    # Local tier rank mapping to avoid dependency on rag.py internals
    tiers = {"D": 0, "C": 1, "B": 2, "A": 3, "S": 4, "S+": 5}
    for doc, score in equipment_pool.values():
        tier = str(doc.metadata.get("tier", "")).strip().upper()
        tier_rank = tiers.get(tier, 0)
        final_results.append((doc, score + (tier_rank * 0.1)))

    final_results.sort(key=lambda x: x[1], reverse=True)
    return final_results[:top_k_final]


def _format_retrieved_snippets(
    rag,
    query: str,
    *,
    doc_type: str,
    top_k_per_variant: int,
    min_similarity: float,
    max_items: int,
    max_chars: Optional[int],
    snippet_chars: int,
    empty_text: str,
) -> str:
    if not rag or not rag.enabled:
        return empty_text

    lines: List[str] = []
    used_chars = 0
    for doc, score in _search_with_variants(
        rag,
        query,
        doc_type=doc_type,
        top_k_per_variant=top_k_per_variant,
        min_similarity=min_similarity,
    )[:max_items]:
        content = str(getattr(doc, "content", "")).strip().replace("\n", " ")
        if not content:
            continue

        snippet = content[:snippet_chars].strip()
        line = f"- (rel={score:.2f}) {snippet}"

        if max_chars and max_chars > 0:
            projected = used_chars + len(line) + 1
            if projected > max_chars:
                break
            used_chars = projected

        lines.append(line)

    return "\n".join(lines) if lines else empty_text


def build_chat_context(rag, question: str) -> Dict[str, str]:
    """Build focused, relevance-filtered context for chat QA."""
    context = {
        "characters": "",
        "equipment": "",
        "gameplay": "",
        "glossary": "",
    }

    if not rag or not rag.enabled:
        return context

    intent = _classify_query_intent(question)

    if "character" in intent:
        character_items = _retrieve_character_items(
            rag,
            question,
            top_k_semantic=16,
            top_k_final=12,
            min_similarity=0.20,
        )
        char_lines: List[str] = []
        for doc, score in character_items:
            name = doc.metadata.get("name", "Unknown")
            rarity = doc.metadata.get("rarity", "?")
            tier = doc.metadata.get("tier", "?")
            passive = _extract_passive(doc.content)
            score_tag = f"{score:.2f}"
            if passive:
                char_lines.append(
                    f"- (rel={score_tag}) [{tier}] {name} | Rarity: {rarity} | Passive: {passive}"
                )
            else:
                char_lines.append(f"- (rel={score_tag}) [{tier}] {name} | Rarity: {rarity}")
        context["characters"] = "\n".join(char_lines) if char_lines else "No relevant character matches found."

    if "equipment" in intent:
        equipment_items = _retrieve_equipment_items(
            rag,
            question,
            top_k_per_variant=15,
            top_k_final=10,
            min_similarity=0.22,
        )
        equip_lines: List[str] = []
        for doc, score in equipment_items:
            name = doc.metadata.get("name", "Unknown")
            equip_type = doc.metadata.get("type", "?")
            tier = doc.metadata.get("tier", "?")
            effect = ""
            for line in doc.content.split("\n"):
                if line.startswith("Effect:"):
                    effect = line.replace("Effect:", "").strip()
                    break
            suffix = f" | Effect: {effect}" if effect else ""
            equip_lines.append(f"- (rel={score:.2f}) [{tier}] {name} ({equip_type}){suffix}")
        context["equipment"] = "\n".join(equip_lines) if equip_lines else "No relevant equipment matches found."

    if "gameplay" in intent:
        context["gameplay"] = _format_retrieved_snippets(
            rag,
            question,
            doc_type="gameplay",
            top_k_per_variant=5,
            min_similarity=0.18,
            max_items=6,
            max_chars=None,
            snippet_chars=260,
            empty_text="No directly relevant gameplay snippets found.",
        )

    if "glossary" in intent:
        context["glossary"] = _format_retrieved_snippets(
            rag,
            question,
            doc_type="glossary",
            top_k_per_variant=5,
            min_similarity=0.18,
            max_items=6,
            max_chars=None,
            snippet_chars=220,
            empty_text="No directly relevant glossary snippets found.",
        )

    return context


async def _summarize_messages(
    assistant,
    use_model: str,
    existing_summary: str,
    messages_to_summarize: List[Dict[str, str]],
) -> Optional[str]:
    if not messages_to_summarize:
        return existing_summary or None

    summary_model = os.getenv("MKM_CHAT_SUMMARY_MODEL", "").strip() or use_model
    summary_prompt_lines = []
    for item in messages_to_summarize:
        prefix = "User" if item["role"] == "user" else "Assistant"
        summary_prompt_lines.append(f"{prefix}: {item['content']}")

    system_prompt = """You compact conversation history for a game assistant.

Rules:
- Keep important facts, user preferences, constraints, and unresolved questions.
- Keep named entities exactly as written.
- Omit filler and repeated phrasing.
- Return plain text only, max 250 words.
"""

    prompt = "\n".join(
        [
            "Existing summary (may be empty):",
            existing_summary.strip() or "(none)",
            "",
            "New messages to merge into summary:",
            "\n".join(summary_prompt_lines),
            "",
            "Updated compact summary:",
        ]
    )

    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{assistant.base_url}/api/chat",
            json={
                "model": summary_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500,
                },
            },
            timeout=_get_http_timeout_seconds(),
        )

    if response.status_code != 200:
        logger.warning("Chat summary request failed with status %s", response.status_code)
        return existing_summary or None

    result = response.json()
    if "error" in result:
        logger.warning("Chat summary request failed: %s", result["error"])
        return existing_summary or None
    text = str(result.get("message", {}).get("content", "")).strip()
    if not text:
        return existing_summary or None

    return text


async def _compact_chat_history(
    assistant,
    use_model: str,
    messages: List[Dict[str, str]],
    existing_summary: str,
    existing_summary_count: int,
) -> Tuple[Optional[str], int, List[Dict[str, str]]]:
    keep_recent = _safe_positive_int(os.getenv("MKM_CHAT_KEEP_RECENT_MESSAGES", "4"), 4)
    compact_trigger = _safe_positive_int(
        os.getenv("MKM_CHAT_COMPACT_TRIGGER_MESSAGES", "8"), 8
    )

    if len(messages) <= keep_recent:
        return (existing_summary or None, max(0, existing_summary_count), messages)

    if len(messages) < compact_trigger:
        return (existing_summary or None, max(0, existing_summary_count), messages)

    summarize_chunk = messages[:-keep_recent]
    recent_messages = messages[-keep_recent:]

    merged_summary = await _summarize_messages(
        assistant=assistant,
        use_model=use_model,
        existing_summary=existing_summary,
        messages_to_summarize=summarize_chunk,
    )

    new_summary_count = max(0, existing_summary_count) + len(summarize_chunk)
    return (merged_summary, new_summary_count, recent_messages)


def build_structured_context(
    rag,
    strategy: str,
    *,
    character_limit: int = 22,
    equipment_limit: int = 24,
    passive_max_chars: Optional[int] = None,
    gameplay_max_chars: Optional[int] = 1200,
    glossary_max_chars: Optional[int] = 1200,
) -> Dict[str, str]:
    """
    Build clearly structured context for the LLM to reduce hallucinations.
    
    Returns dict with separate lists for characters and equipment by type.
    Results are already sorted by tier from RAG system (prioritize_tier=True).
    """
    context = {
        "characters": "No matches found",
        "weapons": "None found",
        "armor": "None found",
        "accessories": "None found",
        "glossary": "No relevant glossary entries found",
        "gameplay": "No relevant gameplay entries found",
    }
    
    if not rag or not rag.enabled:
        data_dir = _resolve_runtime_data_dir()
        glossary_file = data_dir / "glossary.txt"
        if glossary_file.exists():
            glossary_text = glossary_file.read_text(encoding="utf-8").strip()
            if glossary_max_chars and glossary_max_chars > 0:
                glossary_text = glossary_text[:glossary_max_chars].strip()
            context["glossary"] = glossary_text or context["glossary"]

        gameplay_file = data_dir / "gameplay.txt"
        if gameplay_file.exists():
            gameplay_text = gameplay_file.read_text(encoding="utf-8").strip()
            if gameplay_max_chars and gameplay_max_chars > 0:
                gameplay_text = gameplay_text[:gameplay_max_chars].strip()
            context["gameplay"] = gameplay_text or context["gameplay"]
        return context

    intent = _classify_query_intent(strategy)

    # Variant-aware retrieval with lexical boosting to avoid missing partial character names.
    character_limit = max(8, min(80, int(character_limit)))
    equipment_limit = max(8, min(80, int(equipment_limit)))

    if "character" in intent:
        char_results = _retrieve_character_items(
            rag,
            strategy,
            top_k_semantic=24,
            top_k_final=character_limit,
            min_similarity=0.18,
        )
        char_list = []
        for doc, score in char_results:
            name = doc.metadata.get("name", "Unknown")
            rarity = doc.metadata.get("rarity", "?")
            tier = doc.metadata.get("tier", "?")
            # Extract passive from content (it's in the document content)
            passive = ""
            for line in doc.content.split("\n"):
                if line.startswith("Passive:"):
                    passive = line.replace("Passive:", "").strip()
                    break
            if passive_max_chars and passive_max_chars > 0 and len(passive) > passive_max_chars:
                passive = passive[:passive_max_chars].rstrip() + "..."
            char_list.append(f"- [{tier}] Rarity: {rarity} | Name: {name} | Passive: {passive}" if passive else f"- [{tier}] Rarity: {rarity} | Name: {name}")
        context["characters"] = "\n".join(char_list) if char_list else context["characters"]

    if "equipment" in intent:
        # Variant-aware equipment retrieval.
        equip_results = _search_with_variants(
            rag,
            strategy,
            doc_type="equipment",
            top_k_per_variant=24,
            min_similarity=0.18,
        )[:equipment_limit]
        weapons, armor, accessories = [], [], []
        for doc, score in equip_results:
            name = doc.metadata.get("name", "Unknown")
            equip_type = doc.metadata.get("type", "").strip()
            tier = doc.metadata.get("tier", "?")
            # Extract effect from content
            effect = ""
            for line in doc.content.split("\n"):
                if line.startswith("Effect:"):
                    effect = line.replace("Effect:", "").strip()
                    break
            item_str = f"- [{tier}] {name}" + (f" ({effect})" if effect else "")
            # Categorize by type field from TSV
            if equip_type == "Weapon":
                weapons.append(item_str)
            elif equip_type == "Armor":
                armor.append(item_str)
            elif equip_type == "Accessory":
                accessories.append(item_str)
        # Items within each category maintain tier order from RAG
        context["weapons"] = "\n".join(weapons[:]) if weapons else context["weapons"]
        context["armor"] = "\n".join(armor[:]) if armor else context["armor"]
        context["accessories"] = "\n".join(accessories[:]) if accessories else context["accessories"]

    context["gameplay"] = _format_retrieved_snippets(
        rag,
        strategy,
        doc_type="gameplay",
        top_k_per_variant=_safe_positive_int(os.getenv("MKM_STRUCTURED_GAMEPLAY_TOP_K", "8"), 8),
        min_similarity=0.18,
        max_items=_safe_positive_int(os.getenv("MKM_STRUCTURED_GAMEPLAY_MAX_ITEMS", "8"), 8),
        max_chars=gameplay_max_chars,
        snippet_chars=260,
        empty_text=context["gameplay"],
    )
    context["glossary"] = _format_retrieved_snippets(
        rag,
        strategy,
        doc_type="glossary",
        top_k_per_variant=_safe_positive_int(os.getenv("MKM_STRUCTURED_GLOSSARY_TOP_K", "8"), 8),
        min_similarity=0.18,
        max_items=_safe_positive_int(os.getenv("MKM_STRUCTURED_GLOSSARY_MAX_ITEMS", "8"), 8),
        max_chars=glossary_max_chars,
        snippet_chars=240,
        empty_text=context["glossary"],
    )
    
    return context


async def suggest_team_json(
    strategy: str,
    owned_characters: Optional[List[str]] = None,
    model: Optional[str] = None
) -> dict:
    """
    Get team composition suggestions as structured JSON
    
    Args:
        strategy: Desired strategy (e.g., "aggressive rush", "defensive tank")
        owned_characters: Optional list of characters the player owns
        model: Optional Ollama model tag to use (e.g., "llama3.2:3b")
        
    Returns:
        Structured JSON with team suggestion
    """
    def _clean_llm_json(text: str) -> str:
        """Strip thinking tags, markdown wrappers, and trailing debris."""
        if not text:
            return ""
        # Remove thinking tags (even if unclosed due to truncation)
        import re
        text = re.sub(r'<think>.*?(?:</think>|$)', '', text, flags=re.DOTALL)
        # Find first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1:
            if end != -1 and end > start:
                return text[start:end+1]
            return text[start:] # Return from start of JSON even if truncated
        return text.strip()

    def _normalize_team_payload(payload: object) -> Dict[str, object]:
        def _to_effect_text(item: object) -> str:
            if isinstance(item, str):
                return item.strip()
            if isinstance(item, dict):
                # Check multiple possible keys
                for k in ["effect", "description", "passive", "text"]:
                    val = item.get(k)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            return ""

        def _normalize_char(char_obj: object) -> Dict[str, object]:
            if not isinstance(char_obj, dict):
                return {}

            char = dict(char_obj)
            # Ensure passive is a string
            passive_val = char.get("passive")
            if isinstance(passive_val, dict):
                char["passive"] = _to_effect_text(passive_val)
            elif not isinstance(passive_val, str):
                char["passive"] = ""

            # Ensure rarity is a string
            rarity_val = char.get("rarity")
            if not isinstance(rarity_val, str):
                char["rarity"] = "?"

            equipment = char.get("equipment")
            if not isinstance(equipment, list):
                # Try translation from dict-based slots or weapons/armor/accessories lists
                built_equipment: List[Dict[str, str]] = []
                for src_key in ["weapon", "armor", "accessory", "extra", "weapons", "armor", "accessories"]:
                    source = char.get(src_key)
                    if not source:
                        continue
                    items = source if isinstance(source, list) else [source]
                    for item in items:
                        if isinstance(item, dict):
                            name = str(item.get("name", "")).strip()
                            effect = _to_effect_text(item)
                        else:
                            name = str(item).strip()
                            effect = ""
                        if name:
                            slot = src_key.rstrip('s')
                            if slot == "extra": slot = "accessory" # treat extra as accessory
                            built_equipment.append({"slot": slot, "name": name, "effect": effect})
                char["equipment"] = built_equipment
            else:
                # Clean existing list
                normalized_equipment: List[Dict[str, str]] = []
                for item in equipment:
                    if isinstance(item, dict):
                        slot = str(item.get("slot", "")).strip().lower() or "accessory"
                        name = str(item.get("name", "")).strip()
                        if name:
                            normalized_equipment.append({
                                "slot": slot,
                                "name": name,
                                "effect": _to_effect_text(item)
                            })
                    elif isinstance(item, str) and item.strip():
                        normalized_equipment.append({
                            "slot": "accessory",
                            "name": item.strip(),
                            "effect": ""
                        })
                char["equipment"] = normalized_equipment

            return char

        if not isinstance(payload, dict):
            return {}

        team = dict(payload)
        # Pull from "response" or "team" nested keys if present
        for k in ["response", "team", "data"]:
            nested = team.get(k)
            if isinstance(nested, dict):
                # Merge nested into top level
                for nk, nv in nested.items():
                    if nk not in team or not team[nk]:
                        team[nk] = nv

        if "strategy" not in team and isinstance(team.get("text"), str):
            team["strategy"] = str(team.get("text", "")).strip()

        # Alternate schema: single character object at top-level.
        if "char1" not in team and isinstance(team.get("name"), str):
            team["char1"] = dict(team)

        # Handle "characters": [...] list
        chars_list = team.get("characters")
        if isinstance(chars_list, list):
            for idx, item in enumerate(chars_list[:3], start=1):
                key = f"char{idx}"
                if key not in team or not team[key]:
                    team[key] = item

        # Final pass over char1, char2, char3
        for idx in range(1, 4):
            key = f"char{idx}"
            if key in team:
                team[key] = _normalize_char(team[key])
            else:
                team[key] = {"name": "Placeholder", "rarity": "Gold", "passive": "", "equipment": []}

        if not team.get("strategy"):
            team["strategy"] = "Optimized team based on your request."

        return team

    def _enforce_team_output_format(team: Dict[str, object]) -> Optional[Dict[str, object]]:
        """Permissive enforcer: ensures key fields exist, but doesn't crash on partial data."""
        if not isinstance(team, dict):
            return None

        # We must at least have char1 and strategy
        if not team.get("char1") or not isinstance(team["char1"], dict):
            return None
        
        # Ensure name exists for all characters
        for idx in range(1, 4):
            key = f"char{idx}"
            char = team.get(key)
            if not isinstance(char, dict) or not char.get("name"):
                # If char2 or char3 is missing, we fill with empty instead of failing
                team[key] = {"name": "Unknown", "rarity": "Gold", "passive": "", "equipment": []}
            
            # Ensure equipment is a list
            if not isinstance(team[key].get("equipment"), list):
                team[key]["equipment"] = []

        return team

    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "error": "Ollama assistant not available. Make sure Ollama is running."
            }
        
        # Use a resolved model tag for consistency with other endpoints.
        use_model = assistant._resolve_model_name(model)
        
        # Build endpoint-tuned context for stable JSON output.
        # Reduced limits for 3B models to decrease context pressure and prevent truncation.
        context = build_structured_context(
            rag,
            strategy,
            character_limit=_safe_positive_int(os.getenv("MKM_TEAM_CHAR_LIMIT", "12"), 12),
            equipment_limit=_safe_positive_int(os.getenv("MKM_TEAM_EQUIP_LIMIT", "15"), 15),
            passive_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_PASSIVE_MAX_CHARS", "420"), 420),
            gameplay_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_GAMEPLAY_MAX_CHARS", "1000"), 1000),
            glossary_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_GLOSSARY_MAX_CHARS", "1000"), 1000),
        )
        
        owned_filter = ""
        if owned_characters:
            owned_filter = f"User owns: {', '.join(owned_characters)}. Prioritize these characters.\n"
        
        # System prompt: static rules and reference data (reset each call with keep_alive=0)
        system_prompt = f"""You are a Mortal Kombat Mobile team builder assistant.
    
=== GAMEPLAY MECHANICS ===
{context['gameplay']}

=== GAME GLOSSARY ===
{context['glossary']}

=== RULES ===
- Suggest EXACTLY 3 characters from the AVAILABLE CHARACTERS list.
- Each character gets: 1 weapon, 1 armor, 1 accessory. Diamond characters get 1 extra slot (any type).
- COPY all names and descriptions VERBATIM from the lists. Do NOT shorten or paraphrase.
- Do NOT repeat characters or equipment.
- If equipment pieces have character-specific effects, prioritize characters that benefit from them only if they are in the AVAILABLE CHARACTERS list. Equip them accordingly.
- TIER RANKING (best to worst): S+ > S > A > B > C > D. Prefer higher tiers but consider synergy.

=== OUTPUT FORMAT ===
Respond with ONLY this JSON structure:
{{
    "char1": {{"name": "<character name>", "rarity":"<character rarity>" ,"passive": "<passive text>", "equipment": [{{"slot": "weapon", "name": "<name>", "effect": "<effect>"}}, {{"slot": "armor", "name": "<name>", "effect": "<effect>"}}, {{"slot": "accessory", "name": "<name>", "effect": "<effect>"}}]}},
    "char2": {{"name": "<character name>", "rarity":"<character rarity>" ,"passive": "<passive text>", "equipment": [{{"slot": "weapon", "name": "<name>", "effect": "<effect>"}}, {{"slot": "armor", "name": "<name>", "effect": "<effect>"}}, {{"slot": "accessory", "name": "<name>", "effect": "<effect>"}}]}},
    "char3": {{"name": "<character name>", "rarity":"<character rarity>" ,"passive": "<passive text>", "equipment": [{{"slot": "weapon", "name": "<name>", "effect": "<effect>"}}, {{"slot": "armor", "name": "<name>", "effect": "<effect>"}}, {{"slot": "accessory", "name": "<name>", "effect": "<effect>"}}]}},
    "strategy": "<explanation of team synergy>"
}}

IMPORTANT: You MUST generate JSON for exactly 3 characters (char1, char2, char3). Do not stop after the first character."""

        # User prompt: the specific request with available items
        user_prompt = f"""{owned_filter}Build a team for: {strategy}

=== AVAILABLE CHARACTERS ===
{context['characters']}

=== AVAILABLE WEAPONS ===
{context['weapons']}

=== AVAILABLE ARMOR ===
{context['armor']}

=== AVAILABLE ACCESSORIES ===
{context['accessories']}"""

        # Detect if we should use higher limits for reasoning models (DeepSeek-R1, o1, etc.)
        is_reasoning_model = any(kw in use_model.lower() for kw in ["r1", "o1", "thought", "reasoning"])
        num_predict = 4000 if is_reasoning_model else 2500
        num_ctx = 8192 if is_reasoning_model else 4096

        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/chat",
                json={
                    "model": use_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "format": "json",
                    "keep_alive": "10m", # Keep in memory for 10 mins
                    "options": {
                        "temperature": 0.3 if is_reasoning_model else 0.1, # Slightly higher for reasoning depth
                        "num_predict": num_predict,
                        "num_ctx": num_ctx
                    }
                },
                timeout=_get_http_timeout_seconds()
            )
            
            if response.status_code != 200:
                err_msg = f"HTTP {response.status_code}"
                try:
                    err_msg += f": {response.text[:200]}"
                except Exception:
                    pass
                _log_debug_interaction("SUGGEST_TEAM_ERR", system_prompt, user_prompt, err_msg)
                return {"error": f"Ollama API returned status {response.status_code}"}
            
            result = response.json()
            if "error" in result:
                return {"error": f"Ollama Error: {result['error']}"}
            response_text = result.get("message", {}).get("content", "")
            _log_debug_interaction("SUGGEST_TEAM", system_prompt, user_prompt, response_text)
            
            # 1. Clean and parse JSON
            cleaned_json = _clean_llm_json(response_text)
            team_data = None
            
            try:
                team_data = json.loads(cleaned_json)
            except json.JSONDecodeError:
                # 2. Try Python literal eval if JSON fails
                try:
                    import ast
                    team_data = ast.literal_eval(cleaned_json)
                except Exception:
                    pass

            if team_data:
                # 3. Normalize and Enforce (permissive)
                team_data = _normalize_team_payload(team_data)
                final_team = _enforce_team_output_format(team_data)
                if final_team:
                    return {"response": final_team}

            # 4. Final fallback logic if parsing failed
            # If we have a strategy but failed on characters, we return a fallback response
            if isinstance(team_data, dict) and team_data.get("strategy"):
                 return {
                    "response": {
                        "strategy": team_data["strategy"],
                        "char1": {"name": "Retrieval Success", "rarity": "Diamond", "passive": "Model response was partially malformed. Please try again.", "equipment": []},
                        "char2": {"name": "Parsing Issue", "rarity": "Diamond", "passive": "", "equipment": []},
                        "char3": {"name": "Structure Refinement", "rarity": "Diamond", "passive": "", "equipment": []}
                    }
                }

            return {
                "error": "Failed to parse model output into required team JSON schema",
                "raw_response": response_text,
                "cleaned_attempt": cleaned_json
            }
                
    except Exception as e:
        logger.error(f"Error in suggest_team_json: {e}")
        return {"error": str(e)}


async def ask_question_json(question: str, model: Optional[str] = None) -> dict:
    """Answer a free-form question with RAG context, returning Markdown text."""
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)

        if not assistant.enabled:
            return {"error": "Ollama assistant not available. Make sure Ollama is running."}

        # Use a resolved model tag for consistency with other endpoints.
        use_model = assistant._resolve_model_name(model)

        context = build_structured_context(
            rag,
            question,
            character_limit=_safe_positive_int(os.getenv("MKM_ASK_CHAR_LIMIT", "22"), 22),
            equipment_limit=_safe_positive_int(os.getenv("MKM_ASK_EQUIP_LIMIT", "24"), 24),
            passive_max_chars=_safe_positive_int(os.getenv("MKM_ASK_PASSIVE_MAX_CHARS", "420"), 420),
            gameplay_max_chars=_safe_positive_int(os.getenv("MKM_ASK_GAMEPLAY_MAX_CHARS", "1200"), 1200),
            glossary_max_chars=_safe_positive_int(os.getenv("MKM_ASK_GLOSSARY_MAX_CHARS", "1200"), 1200),
        )

        system_prompt = f"""You are a knowledgeable Mortal Kombat Mobile game assistant.

=== GAMEPLAY MECHANICS ===
{context['gameplay']}

=== GAME GLOSSARY ===
{context['glossary']}

=== RELEVANT CHARACTERS ===
{context['characters']}

=== RELEVANT WEAPONS ===
{context['weapons']}

=== RELEVANT ARMOR ===
{context['armor']}

=== RELEVANT ACCESSORIES ===
{context['accessories']}

=== RULES ===
- Answer clearly and accurately using the context above.
- Use Markdown formatting: headings (##), bold (**text**), bullet lists (- item), numbered lists, and code blocks if relevant.
- If a question cannot be answered from the provided context, say so honestly.
- Be concise but thorough."""

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/chat",
                json={
                    "model": use_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "stream": False,
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1500
                    }
                },
                timeout=_get_http_timeout_seconds()
            )

            if response.status_code != 200:
                err_msg = f"HTTP {response.status_code}"
                try:
                    err_msg += f": {response.text[:200]}"
                except Exception:
                    pass
                _log_debug_interaction("ASK_QUESTION_ERR", system_prompt, question, err_msg)
                return {"error": f"Ollama API returned status {response.status_code}"}

            result = response.json()
            if "error" in result:
                return {"error": f"Ollama Error: {result['error']}"}
            response_text = result.get("message", {}).get("content", "").strip()
            _log_debug_interaction("ASK_QUESTION", system_prompt, question, response_text)

            if not response_text:
                return {"error": "Empty response from LLM"}

            return {"response": response_text}

    except Exception as e:
        logger.error(f"Error in ask_question_json: {e}")
        return {"error": str(e)}


async def explain_mechanic_json(mechanic: str, model: Optional[str] = None) -> dict:
    """Explain a mechanic with RAG and return definition + recommendations as JSON-shaped dict."""
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)

        if not assistant.enabled:
            return {"error": "Ollama assistant not available. Make sure Ollama is running."}

        result = await assistant.explain_mechanic(mechanic, model=model)

        if isinstance(result, dict) and result.get("error"):
            raw = result.get("raw_response")
            if raw is not None:
                preview = str(raw).replace("\n", " ")[:300]
                logger.warning("explain_mechanic_json: parse failure raw preview=%s", preview)
            return {"error": str(result["error"])}

        if not isinstance(result, dict):
            return {"error": "Unexpected response from explain_mechanic"}

        definition = str(result.get("definition", "")).strip()
        recommendations = str(result.get("recommendations", "")).strip()
        if not definition and not recommendations:
            return {"error": "Empty definition and recommendations from model"}

        return {
            "response": {
                "definition": definition,
                "recommendations": recommendations,
            }
        }

    except Exception as e:
        logger.error(f"Error in explain_mechanic_json: {e}")
        return {"error": str(e)}


async def chat_json(
    message: str,
    messages: Optional[List[Dict[str, str]]] = None,
    summary_text: Optional[str] = None,
    summary_message_count: int = 0,
    model: Optional[str] = None,
) -> dict:
    """Answer a chat message using RAG context and compacted conversation history."""
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)

        if not assistant.enabled:
            return {"error": "Ollama assistant not available. Make sure Ollama is running."}

        use_model = assistant._resolve_model_name(model)
        normalized_messages = _sanitize_chat_messages(messages or [])
        normalized_summary_text = (summary_text or "").strip()
        normalized_summary_count = max(0, int(summary_message_count or 0))

        compacted_summary, compacted_summary_count, recent_messages = await _compact_chat_history(
            assistant=assistant,
            use_model=use_model,
            messages=normalized_messages,
            existing_summary=normalized_summary_text,
            existing_summary_count=normalized_summary_count,
        )

        retrieval_query = _build_chat_retrieval_query(message, recent_messages)
        context = build_chat_context(rag, retrieval_query)

        history_lines = []
        for item in recent_messages:
            speaker = "User" if item["role"] == "user" else "Assistant"
            history_lines.append(f"{speaker}: {item['content']}")

        history_block = "\n".join(history_lines).strip() or "(no previous turns)"
        summary_block = compacted_summary or "(none)"

        system_prompt = f"""You are a Mortal Kombat Mobile tactical coach and roster expert.

    You must answer using ONLY evidence from the RAG snippets and conversation context below.
    If the evidence is insufficient, explicitly say you do not have enough indexed data.

    Name normalization rule:
    - In this game data, users may ask for "Classic" while data uses "Klassic". Treat them as the same concept.

    === RAG: RELEVANT CHARACTERS ===
    {context['characters']}

    === RAG: RELEVANT EQUIPMENT ===
    {context['equipment']}

    === RAG: RELEVANT GAMEPLAY ===
    {context['gameplay']}

    === RAG: RELEVANT GLOSSARY ===
    {context['glossary']}

    === COMPACT CONVERSATION SUMMARY ===
    {summary_block}

    === RECENT CONVERSATION TURNS ===
    {history_block}

    === RESPONSE RULES ===
    - SYNTHESIS OVER RECITATION: Do not just copy-paste passives. Explain *how* they work together in an actual match.
    - SYNERGY FOCUS: Always look for and highlight class-based buffs (e.g., Martial Artist, Outworld) or debuff synergies (Fire, Bleed, Snare) found in the text.
    - READABILITY: Use **bold text** for all character and equipment names. Use bullet points for easy scanning of strategies. Reply format should be in MARKDOWN.
    - HALLUCINATIONS: Do NOT invent stats, combo enders, or passives not provided in the context. 
    - MISSING DATA: If the evidence does not cover the specific character, honestly say your database doesn't have their exact stats yet, but provide related strategic advice based on what IS in the context.
    - TONE: Keep your tone encouraging, concise, and highly tactical.
    """

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/chat",
                json={
                    "model": use_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "stream": False,
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0.45,
                        "num_predict": 1800,
                        "num_ctx": 8192,
                    },
                },
                timeout=_get_http_timeout_seconds(),
            )

        if response.status_code != 200:
            err_msg = f"HTTP {response.status_code}"
            try:
                err_msg += f": {response.text[:200]}"
            except Exception:
                pass
            _log_debug_interaction("CHAT_ERR", system_prompt, message, err_msg)
            return {"error": f"Ollama API returned status {response.status_code}"}

        result = response.json()
        if "error" in result:
            return {"error": f"Ollama Error: {result['error']}"}
        response_text = str(result.get("message", {}).get("content", "")).strip()
        _log_debug_interaction("CHAT", system_prompt, message, response_text)
        if not response_text:
            return {"error": "Empty response from LLM"}

        return {
            "response": {
                "text": response_text,
                "summary_text": compacted_summary,
                "summary_message_count": compacted_summary_count,
            }
        }

    except Exception as e:
        logger.error(f"Error in chat_json: {e}")
        # Capture error in debug log if possible
        try:
             _log_debug_interaction("CHAT_EXCEPTION", "N/A", message, f"EXCEPTION: {repr(e)}")
        except Exception:
             pass
        return {"error": str(e)}


class MKMobileHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MK Mobile API"""
    
    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)

        origin = self.headers.get("Origin", "")
        configured_origins = os.getenv("MKM_CORS_ORIGINS", "*").strip()
        if not configured_origins or configured_origins == "*":
            allow_origin = "*"
        else:
            allowed = [item.strip() for item in configured_origins.split(",") if item.strip()]
            allow_origin = origin if origin in allowed else (allowed[0] if allowed else "*")

        api_key_header = os.getenv("MKM_API_KEY_HEADER", "X-API-Key")

        self.send_header("Access-Control-Allow-Origin", allow_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", f"Content-Type, {api_key_header}")
        self.end_headers()

    @staticmethod
    def _get_int_env(name: str, default: int) -> int:
        try:
            value = int(os.getenv(name, str(default)))
            return value if value > 0 else default
        except ValueError:
            return default

    def _client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _check_api_auth(self) -> bool:
        expected_key = os.getenv("MKM_API_KEY", "").strip()
        if not expected_key:
            return True

        header_name = os.getenv("MKM_API_KEY_HEADER", "X-API-Key")
        provided_key = self.headers.get(header_name, "")

        if not provided_key or not hmac.compare_digest(provided_key, expected_key):
            logger.warning("Unauthorized API request from %s", self._client_ip())
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return False

        return True

    def _check_rate_limit(self) -> bool:
        enabled = os.getenv("MKM_RATE_LIMIT_ENABLED", "true").lower() == "true"
        if not enabled:
            return True

        per_minute_limit = self._get_int_env("MKM_RATE_LIMIT_PER_MINUTE", 20)
        burst_limit = self._get_int_env("MKM_RATE_LIMIT_BURST", 5)
        burst_window = self._get_int_env("MKM_RATE_LIMIT_BURST_WINDOW_SECONDS", 10)

        now = monotonic()
        ip = self._client_ip()

        minute_queue = _IP_REQUESTS[ip]
        while minute_queue and now - minute_queue[0] > 60:
            minute_queue.popleft()

        burst_queue = _IP_BURST_REQUESTS[ip]
        while burst_queue and now - burst_queue[0] > burst_window:
            burst_queue.popleft()

        if len(minute_queue) >= per_minute_limit or len(burst_queue) >= burst_limit:
            logger.warning("Rate limit exceeded for %s", ip)
            self._set_headers(429)
            self.wfile.write(json.dumps({"error": "Too many requests"}).encode())
            return False

        minute_queue.append(now)
        burst_queue.append(now)
        return True

    def _read_json_body(self, expected_payload: dict) -> Optional[dict]:
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length == 0:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                "error": "Request body required",
                "expected": expected_payload,
            }).encode())
            return None

        max_request_size = self._get_int_env("MKM_MAX_REQUEST_SIZE", 1048576)
        if content_length > max_request_size:
            self._set_headers(413)
            self.wfile.write(json.dumps({"error": "Request body too large"}).encode())
            return None

        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return None
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._set_headers(200)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/":
            # Health check / info endpoint
            self._set_headers(200)
            response = {
                "service": "MK Mobile Assistant API",
                "version": "2.3.0",
                "endpoints": {
                    "/suggest-team": {
                        "method": "POST",
                        "description": "Get AI-powered team suggestions",
                        "body": {
                            "strategy": "string (required)",
                            "owned_characters": "array of strings (optional)",
                            "model": "string (optional, Ollama model tag e.g. 'llama3.2:3b')"
                        }
                    },
                    "/ask-question": {
                        "method": "POST",
                        "description": "Ask any question about MK Mobile, returns Markdown text",
                        "body": {
                            "question": "string (required)",
                            "model": "string (optional, Ollama model tag)"
                        }
                    },
                    "/explain-mechanic": {
                        "method": "POST",
                        "description": "Explain a game mechanic using RAG + local LLM",
                        "body": {
                            "mechanic": "string (required)",
                            "model": "string (optional, Ollama model tag)"
                        }
                    },
                    "/chat": {
                        "method": "POST",
                        "description": "Persistent chat turn with RAG + compact history context",
                        "body": {
                            "message": "string (required)",
                            "messages": "array of {role, content} (required)",
                            "summary_text": "string (optional)",
                            "summary_message_count": "integer (optional)",
                            "model": "string (optional, Ollama model tag)"
                        }
                    },
                    "/health": {
                        "method": "GET",
                        "description": "Detailed health / status of RAG system, LLM, and data cache"
                    }
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        elif parsed_path.path == "/health":
            if not self._check_api_auth():
                return
            self._handle_health()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)

        if not self._check_rate_limit():
            return

        if not self._check_api_auth():
            return
        
        if parsed_path.path == "/suggest-team":
            self._handle_suggest_team()
        elif parsed_path.path == "/ask-question":
            self._handle_ask_question()
        elif parsed_path.path == "/explain-mechanic":
            self._handle_explain_mechanic()
        elif parsed_path.path == "/chat":
            self._handle_chat()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    # ------------------------------------------------------------------
    # GET /health
    # ------------------------------------------------------------------

    def _handle_health(self):
        """Return detailed health / observability information."""
        try:
            rag = get_rag_system()
            rag_status = rag.get_status() if rag.enabled else {"enabled": False}

            # Check Ollama reachability (quick connect test)
            from mkmchat.llm.ollama import get_ollama_assistant
            assistant = get_ollama_assistant(rag_system=rag)
            llm_status = {
                "enabled": assistant.enabled,
                "model": getattr(assistant, "model_name", None),
                "base_url": getattr(assistant, "base_url", None),
            }

            # Document-type breakdown
            doc_breakdown = {}
            if rag.enabled:
                for doc in rag.documents:
                    doc_breakdown[doc.doc_type] = doc_breakdown.get(doc.doc_type, 0) + 1

            health = {
                "status": "ok" if rag.enabled and assistant.enabled else "degraded",
                "rag": {**rag_status, "documents_by_type": doc_breakdown},
                "llm": llm_status,
            }

            self._set_headers(200)
            self.wfile.write(json.dumps(health, indent=2).encode())
        except BrokenPipeError:
            logger.warning("Client disconnected before /health response could be written")
        except Exception as e:
            logger.error(f"Error handling /health: {e}")
            try:
                self._set_headers(500)
                self.wfile.write(json.dumps({"status": "error", "detail": str(e)}).encode())
            except BrokenPipeError:
                logger.warning("Client disconnected before /health error response could be written")
    
    def _handle_suggest_team(self):
        """Handle /suggest-team endpoint"""
        try:
            data = self._read_json_body({"strategy": "string", "owned_characters": ["optional", "array"]})
            if data is None:
                return
            
            # Validate required fields
            strategy = data.get("strategy")
            if not isinstance(strategy, str) or not strategy.strip():
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Missing required field: strategy"
                }).encode())
                return

            max_strategy_length = self._get_int_env("MKM_MAX_STRATEGY_LENGTH", 2000)
            if len(strategy) > max_strategy_length:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": f"Strategy exceeds {max_strategy_length} characters"
                }).encode())
                return
            
            owned_characters = data.get("owned_characters")
            if owned_characters is not None and not isinstance(owned_characters, list):
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "owned_characters must be an array of strings"
                }).encode())
                return
            model = data.get("model")  # optional model override
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    suggest_team_json(strategy, owned_characters, model=model)
                )
            finally:
                loop.close()
            
            # Check for errors
            if "error" in result and "response" not in result:
                self._set_headers(500)
            else:
                self._set_headers(200)
            
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Error handling suggest-team: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def _handle_ask_question(self):
        """Handle /ask-question endpoint"""
        try:
            data = self._read_json_body({"question": "string"})
            if data is None:
                return

            question = data.get("question")
            if not isinstance(question, str) or not question.strip():
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Missing required field: question"
                }).encode())
                return

            max_question_length = self._get_int_env("MKM_MAX_QUESTION_LENGTH", 2000)
            if len(question) > max_question_length:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": f"Question exceeds {max_question_length} characters"
                }).encode())
                return

            model = data.get("model")  # optional model override

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(ask_question_json(question, model=model))
            finally:
                loop.close()

            if "error" in result and "response" not in result:
                self._set_headers(500)
            else:
                self._set_headers(200)

            self.wfile.write(json.dumps(result, indent=2).encode())

        except Exception as e:
            logger.error(f"Error handling ask-question: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_explain_mechanic(self):
        """Handle /explain-mechanic endpoint"""
        try:
            data = self._read_json_body({"mechanic": "string"})
            if data is None:
                return

            mechanic = data.get("mechanic")
            if not isinstance(mechanic, str) or not mechanic.strip():
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Missing required field: mechanic"
                }).encode())
                return

            mechanic = mechanic.strip()
            max_len = self._get_int_env("MKM_MAX_MECHANIC_LENGTH", self._get_int_env("MKM_MAX_QUESTION_LENGTH", 2000))
            if len(mechanic) > max_len:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": f"Mechanic exceeds {max_len} characters"
                }).encode())
                return

            model = data.get("model")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(explain_mechanic_json(mechanic, model=model))
            finally:
                loop.close()

            if "error" in result and "response" not in result:
                self._set_headers(500)
            else:
                self._set_headers(200)

            try:
                self.wfile.write(json.dumps(result, indent=2).encode())
            except BrokenPipeError:
                logger.warning("Client disconnected before /explain-mechanic response could be written")

        except BrokenPipeError:
            logger.warning("Client disconnected during /explain-mechanic handling")

        except Exception as e:
            logger.error(f"Error handling explain-mechanic: {e}")
            try:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            except BrokenPipeError:
                logger.warning("Client disconnected before /explain-mechanic error response could be written")

    def _handle_chat(self):
        """Handle /chat endpoint"""
        try:
            data = self._read_json_body(
                {
                    "message": "string",
                    "messages": "array of {role, content}",
                    "summary_text": "string (optional)",
                    "summary_message_count": "integer (optional)",
                    "model": "string (optional)",
                }
            )
            if data is None:
                return

            message = data.get("message")
            if not isinstance(message, str) or not message.strip():
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing required field: message"}).encode())
                return

            max_question_length = self._get_int_env("MKM_MAX_QUESTION_LENGTH", 2000)
            if len(message) > max_question_length:
                self._set_headers(400)
                self.wfile.write(
                    json.dumps({"error": f"Message exceeds {max_question_length} characters"}).encode()
                )
                return

            messages = data.get("messages")
            if not isinstance(messages, list):
                self._set_headers(400)
                self.wfile.write(
                    json.dumps({"error": "messages must be an array of {role, content}"}).encode()
                )
                return

            summary_text = data.get("summary_text")
            if summary_text is not None and not isinstance(summary_text, str):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "summary_text must be a string"}).encode())
                return

            raw_summary_count = data.get("summary_message_count", 0)
            try:
                summary_message_count = int(raw_summary_count)
            except (TypeError, ValueError):
                self._set_headers(400)
                self.wfile.write(
                    json.dumps({"error": "summary_message_count must be an integer"}).encode()
                )
                return

            model = data.get("model")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    chat_json(
                        message=message.strip(),
                        messages=messages,
                        summary_text=summary_text,
                        summary_message_count=summary_message_count,
                        model=model,
                    )
                )
            finally:
                loop.close()

            if "error" in result and "response" not in result:
                self._set_headers(500)
            else:
                self._set_headers(200)

            self.wfile.write(json.dumps(result, indent=2).encode())

        except Exception as e:
            logger.error(f"Error handling chat: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        """Override to use logging module"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(port: int = DEFAULT_PORT):
    """Run the HTTP server"""
    host = os.getenv("MKM_HTTP_HOST", "127.0.0.1")
    api_key = os.getenv("MKM_API_KEY", "").strip()
    if not api_key or api_key in {"change-me-in-production", "replace-with-long-random-secret"}:
        raise RuntimeError("Refusing to start: set MKM_API_KEY to a strong non-placeholder value")

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, MKMobileHTTPHandler)
    httpd.daemon_threads = True
    
    logger.info(f"Starting MK Mobile HTTP API server on {host}:{port}")
    logger.info(f"API endpoint: http://{host}:{port}/suggest-team")
    logger.info("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    import sys
    
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    run_server(port)
