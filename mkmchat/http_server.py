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

    search_variants = _chat_query_variants(question) or [question]
    character_items = _retrieve_character_items(
        rag,
        question,
        top_k_semantic=12,
        top_k_final=8,
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

    equipment_items = _search_with_variants(
        rag,
        question,
        doc_type="equipment",
        top_k_per_variant=10,
        min_similarity=0.22,
    )
    equip_lines: List[str] = []
    for doc, score in equipment_items[:10]:
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

    context["gameplay"] = _format_retrieved_snippets(
        rag,
        question,
        doc_type="gameplay",
        top_k_per_variant=5,
        min_similarity=0.18,
        max_items=4,
        max_chars=None,
        snippet_chars=260,
        empty_text="No directly relevant gameplay snippets found.",
    )
    context["glossary"] = _format_retrieved_snippets(
        rag,
        question,
        doc_type="glossary",
        top_k_per_variant=5,
        min_similarity=0.18,
        max_items=4,
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
            f"{assistant.base_url}/api/generate",
            json={
                "model": summary_model,
                "system": system_prompt,
                "prompt": prompt,
                "stream": False,
                "keep_alive": 0,
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
    text = str(result.get("response", "")).strip()
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
    keep_recent = _safe_positive_int(os.getenv("MKM_CHAT_KEEP_RECENT_MESSAGES", "10"), 10)
    compact_trigger = _safe_positive_int(
        os.getenv("MKM_CHAT_COMPACT_TRIGGER_MESSAGES", "24"), 24
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
    
    # Variant-aware retrieval with lexical boosting to avoid missing partial character names.
    character_limit = max(8, min(80, int(character_limit)))
    equipment_limit = max(8, min(80, int(equipment_limit)))

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
    def _normalize_team_payload(payload: object) -> Dict[str, object]:
        def _to_effect_text(item: object) -> str:
            if isinstance(item, str):
                return item.strip()
            if isinstance(item, dict):
                if isinstance(item.get("effect"), str):
                    return str(item.get("effect", "")).strip()
                if isinstance(item.get("description"), str):
                    return str(item.get("description", "")).strip()
            return ""

        def _normalize_char(char_obj: object) -> Dict[str, object]:
            if not isinstance(char_obj, dict):
                return {}

            char = dict(char_obj)
            passive_val = char.get("passive")
            if isinstance(passive_val, dict):
                desc = passive_val.get("description")
                if isinstance(desc, str):
                    char["passive"] = desc.strip()

            equipment = char.get("equipment")
            if isinstance(equipment, list):
                normalized_equipment: List[Dict[str, str]] = []
                for item in equipment:
                    if not isinstance(item, dict):
                        continue
                    slot = str(item.get("slot", "")).strip().lower()
                    name = str(item.get("name", "")).strip()
                    effect = _to_effect_text(item)
                    if slot and name:
                        normalized_equipment.append({"slot": slot, "name": name, "effect": effect})
                if normalized_equipment:
                    char["equipment"] = normalized_equipment

            # Alternate schema support: weapons/armor/accessories arrays -> equipment[]
            if not isinstance(char.get("equipment"), list):
                built_equipment: List[Dict[str, str]] = []
                for src_key, slot in [("weapons", "weapon"), ("armor", "armor"), ("accessories", "accessory")]:
                    source = char.get(src_key)
                    if not isinstance(source, list) or not source:
                        continue
                    first = source[0]
                    if isinstance(first, dict):
                        name = str(first.get("name", "")).strip()
                        effect = _to_effect_text(first)
                    else:
                        name = str(first).strip()
                        effect = ""
                    if name:
                        built_equipment.append({"slot": slot, "name": name, "effect": effect})
                if built_equipment:
                    char["equipment"] = built_equipment

            return char

        if not isinstance(payload, dict):
            return {}

        team = dict(payload)
        nested = team.get("response")
        if isinstance(nested, dict):
            team = dict(nested)

        if "strategy" not in team and isinstance(team.get("text"), str):
            team["strategy"] = str(team.get("text", "")).strip()

        # Alternate schema: single character object at top-level.
        if "char1" not in team and isinstance(team.get("name"), str):
            team["char1"] = dict(team)
            if "strategy" not in team:
                team["strategy"] = "Team generated from available candidate data."

        for source_key in ["team", "characters"]:
            source = team.get(source_key)
            if isinstance(source, list):
                for idx, item in enumerate(source[:3], start=1):
                    if isinstance(item, dict):
                        team[f"char{idx}"] = _normalize_char(item)

        for idx in range(1, 4):
            key = f"char{idx}"
            if key in team:
                team[key] = _normalize_char(team[key])

        return team

    def _enforce_team_output_format(team: Dict[str, object]) -> Optional[Dict[str, object]]:
        if not isinstance(team, dict):
            return None

        strategy_text = str(team.get("strategy", "")).strip()
        if not strategy_text:
            return None

        normalized_team: Dict[str, object] = {"strategy": strategy_text}

        for idx in range(1, 4):
            key = f"char{idx}"
            raw_char = team.get(key)
            if not isinstance(raw_char, dict):
                return None

            name = str(raw_char.get("name", "")).strip()
            if not name:
                return None

            rarity = str(raw_char.get("rarity", "")).strip()
            passive = str(raw_char.get("passive", "")).strip()

            raw_equipment = raw_char.get("equipment")
            if not isinstance(raw_equipment, list):
                return None

            by_slot: Dict[str, Dict[str, str]] = {}
            for item in raw_equipment:
                if not isinstance(item, dict):
                    continue
                slot = str(item.get("slot", "")).strip().lower()
                if slot not in {"weapon", "armor", "accessory"}:
                    continue
                if slot in by_slot:
                    continue

                eq_name = str(item.get("name", "")).strip()
                if not eq_name:
                    continue
                effect = str(item.get("effect", "")).strip()
                by_slot[slot] = {"slot": slot, "name": eq_name, "effect": effect}

            if set(by_slot.keys()) != {"weapon", "armor", "accessory"}:
                return None

            normalized_team[key] = {
                "name": name,
                "rarity": rarity,
                "passive": passive,
                "equipment": [
                    by_slot["weapon"],
                    by_slot["armor"],
                    by_slot["accessory"],
                ],
            }

        return normalized_team

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
        context = build_structured_context(
            rag,
            strategy,
            character_limit=_safe_positive_int(os.getenv("MKM_TEAM_CHAR_LIMIT", "22"), 22),
            equipment_limit=_safe_positive_int(os.getenv("MKM_TEAM_EQUIP_LIMIT", "24"), 24),
            passive_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_PASSIVE_MAX_CHARS", "420"), 420),
            gameplay_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_GAMEPLAY_MAX_CHARS", "1200"), 1200),
            glossary_max_chars=_safe_positive_int(os.getenv("MKM_TEAM_GLOSSARY_MAX_CHARS", "1200"), 1200),
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
    "char2": {{"name": "<character name>", "rarity":"<character rarity>" ,"passive": "<passive text>", "equipment": [same structure]}},
    "char3": {{"name": "<character name>", "rarity":"<character rarity>" ,"passive": "<passive text>", "equipment": [same structure]}},
    "strategy": "<explanation of team synergy>"
}}"""

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

        if _debug_prompts_enabled():
            from pathlib import Path

            log_file = Path(__file__).resolve().parent / "prompt_debug.log"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== SYSTEM PROMPT ===\n{_redact_sensitive_text(system_prompt)}\n\n")
                f.write(f"=== USER PROMPT ===\n{_redact_sensitive_text(user_prompt)}\n")
            logger.info(f"Prompt debug log written to: {log_file}")

        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/generate",
                json={
                    "model": use_model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "format": "json",
                    "keep_alive": 0,  # Unload model after request to reset context
                    "options": {
                        "temperature": 0.1,  # Very low temperature for consistent output
                        "num_predict": 2000
                    }
                },
                timeout=_get_http_timeout_seconds()
            )
            
            if response.status_code != 200:
                return {"error": f"Ollama API returned status {response.status_code}"}
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Try to parse the JSON response
            try:
                team_data = json.loads(response_text)
                team_data = _normalize_team_payload(team_data)
                team_data = _enforce_team_output_format(team_data)
                if team_data:
                    return {"response": team_data}
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response
                logger.warning(f"Failed to parse JSON directly: {e}")

                # Try Python-literal dict/list outputs (single quotes etc.).
                try:
                    import ast

                    py_obj = ast.literal_eval(response_text)
                    team_data = _normalize_team_payload(py_obj)
                    team_data = _enforce_team_output_format(team_data)
                    if team_data:
                        return {"response": team_data}
                except Exception:
                    pass
                
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx + 1]
                    try:
                        team_data = json.loads(json_str)
                        team_data = _normalize_team_payload(team_data)
                        team_data = _enforce_team_output_format(team_data)
                        if team_data:
                            return {"response": team_data}
                    except json.JSONDecodeError:
                        try:
                            import ast

                            py_obj = ast.literal_eval(json_str)
                            team_data = _normalize_team_payload(py_obj)
                            team_data = _enforce_team_output_format(team_data)
                            if team_data:
                                return {"response": team_data}
                        except Exception:
                            pass

                return {
                    "error": "Failed to parse model output into required team JSON schema",
                    "raw_response": response_text
                }

            return {
                "error": "Model returned JSON but not in required team schema.",
                "raw_response": response_text,
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
                f"{assistant.base_url}/api/generate",
                json={
                    "model": use_model,
                    "system": system_prompt,
                    "prompt": question,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1500
                    }
                },
                timeout=_get_http_timeout_seconds()
            )

            if response.status_code != 200:
                return {"error": f"Ollama API returned status {response.status_code}"}

            result = response.json()
            response_text = result.get("response", "").strip()

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

        system_prompt = f"""You are a Mortal Kombat Mobile assistant.

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
    - Prefer precise facts over broad claims.
    - For character-specific answers, quote the exact character name from evidence.
    - If evidence includes variant lists (e.g., colon-separated forms), enumerate them in bullets.
    - Do NOT invent passives, skills, stats, or lore not present in evidence.
    - If no strong character evidence exists, answer with: "I don't have enough indexed data about that character yet." and suggest a close known name if available.
    - Keep answers concise, practical, and formatted in Markdown.
    """

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/generate",
                json={
                    "model": use_model,
                    "system": system_prompt,
                    "prompt": message,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1800,
                    },
                },
                timeout=_get_http_timeout_seconds(),
            )

        if response.status_code != 200:
            return {"error": f"Ollama API returned status {response.status_code}"}

        result = response.json()
        response_text = str(result.get("response", "")).strip()
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
