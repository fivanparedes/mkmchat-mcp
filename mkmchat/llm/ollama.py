"""Ollama local LLM integration for intelligent game querying"""

import hashlib
import os
import re
import logging
from typing import Optional, Dict, Any, List
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

from mkmchat.data.loader import DataLoader
from mkmchat.data.rag import RAGSystem

logger = logging.getLogger(__name__)


def _http_timeout_seconds(default: int = 120) -> int:
    try:
        value = int(os.getenv("MKM_HTTP_TIMEOUT_SECONDS", str(default)))
        return max(10, value)
    except ValueError:
        return default


class OllamaAssistant:
    """Ollama-powered assistant for MK Mobile game queries"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        data_loader: Optional[DataLoader] = None,
        rag_system: Optional[RAGSystem] = None
    ):
        """
        Initialize Ollama assistant
        
        Args:
            model_name: Model to use (llama3.2:3b, phi3:mini, mistral:7b, etc.)
            base_url: Ollama API URL (defaults to http://localhost:11434)
            data_loader: DataLoader instance for accessing game data
            rag_system: RAGSystem instance for semantic search
        """
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available. Install with: pip install httpx")
            self.enabled = False
            return
        
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.data_loader = data_loader or DataLoader()
        self.rag_system = rag_system
        
        # Check if Ollama is running
        self.enabled = self._check_ollama()
        
        if not self.enabled:
            logger.warning(
                f"Ollama not running at {self.base_url}. "
                "Start with: ollama serve"
            )
            return
        
        # Check if model is available
        self._ensure_model_available()
        
        # System context about the game
        self.system_context = self._build_system_context()
        
        logger.info(f"Ollama assistant initialized with model: {model_name}")
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    def _ensure_model_available(self) -> None:
        """Check if model is available, log warning if not"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                if self.model_name not in models:
                    logger.warning(
                        f"Model {self.model_name} not found. "
                        f"Pull it with: ollama pull {self.model_name}"
                    )
                    logger.info(f"Available models: {', '.join(models) if models else 'none'}")
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")

    def _list_available_models(self) -> List[str]:
        """Return model tags currently available in Ollama."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return []
            data = response.json()
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception as e:
            logger.debug(f"Unable to list Ollama models: {e}")
            return []

    def _resolve_model_name(self, requested_model: Optional[str]) -> str:
        """
        Resolve model names robustly:
        - trim whitespace
        - if exact tag exists, use it
        - if no tag was provided (e.g. "deepseek-r1"), resolve to available "deepseek-r1:*"
        """
        model = (requested_model or self.model_name or "").strip()
        if not model:
            return "llama3.2:3b"

        available = self._list_available_models()
        if not available:
            return model

        if model in available:
            return model

        if ":" not in model:
            prefix = f"{model}:"
            candidates = [m for m in available if m.startswith(prefix)]
            if candidates:
                latest = f"{model}:latest"
                resolved = latest if latest in candidates else candidates[0]
                logger.info("Resolved Ollama model alias %s -> %s", model, resolved)
                return resolved

        return model
    
    def _build_system_context(self) -> str:
        """Build system context about MK Mobile game"""
        context = """You are an expert assistant for Mortal Kombat Mobile, a fighting game for mobile devices.

Game Basics:
- Players build teams of 3 characters (starter + 2 support)
- Each character has: Class (Martial Artist, Spec Ops, Netherrealm, Outworld), Rarity (Bronze, Silver, Gold, Diamond)
- Characters have: Basic stats, Special Attacks (SP1, SP2, SP3/X-Ray), and Passive abilities
- Equipment: Weapons, Armor, Accessories with effects and fusion levels (Basic and Tower equipment available)
- Combat: Tag-in/tag-out mechanics, combo attacks, special attacks, blocking, power generation

Character Classes:
- Martial Artist: Balanced fighters, often with combo-focused abilities
- Spec Ops: Tactical fighters with strategic abilities
- Netherrealm: Dark/demonic characters with resurrection and curse abilities
- Outworld: Exotic fighters with unique supernatural abilities

Equipment Types:
- Basic Equipment: Common equipment available from various game modes
- Tower Equipment: Special equipment from Faction Wars and Challenge Towers, often more powerful
- Categories: Weapons (boost attack), Armor (boost defense/health), Accessories (special effects)

Key Game Mechanics:
- Power Generation: Build power bars to use special attacks
- Tag-in Attacks: Switching characters triggers attacks
- Synergies: Characters boost each other based on class/team composition
- Status Effects: Fire, Bleed, Poison, Stun, Freeze, Power Drain, etc.
- Fusion: Upgrade characters and equipment for better stats

Your Role:
- Answer questions about characters, equipment, strategies, and game mechanics
- Provide team composition suggestions based on player goals
- ALWAYS suggest specific equipment for each character in team recommendations
- Explain complex game concepts in simple terms
- Use data from the game database when available
- Be concise but informative

Always base your answers on factual game data when possible, and clearly indicate when you're making strategic recommendations vs stating facts.
"""
        return context
    
    def _get_relevant_context(self, query: str) -> str:
        """Get relevant context from RAG system and data loader"""
        context_parts = []
        
        # Try RAG search if available
        if self.rag_system and self.rag_system.enabled:
            try:
                # Search across all document types
                results = self.rag_system.search(
                    query=query,
                    top_k=15,
                    min_similarity=0.2
                )
                
                if results:
                    context_parts.append("=== Relevant Game Data ===")
                    for doc, score in results:
                        context_parts.append(f"\n[Score: {score:.2f}] {doc.content}")
                    context_parts.append("\n")
            except Exception as e:
                logger.error(f"Error in RAG search: {e}")
        
        # Add specific data if query mentions characters/equipment
        query_lower = query.lower()
        
        # Check for character mentions
        if any(word in query_lower for word in ["character", "fighter", "scorpion", "sub-zero", "raiden", "liu kang"]):
            try:
                # Get a sample of characters
                self.data_loader.load_all()
                chars = list(self.data_loader._characters.values())[:10]
                if chars:
                    context_parts.append("=== Sample Characters ===")
                    for char in chars[:5]:
                        context_parts.append(f"- {char.name} ({char.char_class}, {char.rarity})")
                    context_parts.append(f"Total characters available: {len(self.data_loader._characters)}\n")
            except Exception as e:
                logger.error(f"Error loading characters: {e}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def query(
        self,
        question: str,
        use_rag: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Query the Ollama assistant with a question about the game
        
        Args:
            question: User's question
            use_rag: Whether to use RAG for context retrieval
            temperature: Model temperature (0-1, higher = more creative)
            max_tokens: Maximum tokens in response
            
        Returns:
            Assistant's response
        """
        if not self.enabled:
            return (
                "Ollama assistant not available. "
                f"Make sure Ollama is running at {self.base_url} "
                f"and model {self.model_name} is pulled."
            )
        
        try:
            # Build prompt with context
            relevant_context = ""
            if use_rag:
                relevant_context = self._get_relevant_context(question)
            
            prompt = f"""{self.system_context}

{relevant_context}

User Question: {question}

Please provide a helpful, accurate answer based on the game data above. If you need to make assumptions or give strategic advice, make that clear.

Answer in the user's language.

Answer:"""
            
            # Generate response
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    },
                    timeout=_http_timeout_seconds()
                )
                
                if response.status_code != 200:
                    return f"Error: Ollama API returned status {response.status_code}"
                
                result = response.json()
                return result.get("response", "No response generated")
            
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return f"Error generating response: {str(e)}"
    
    async def compare_characters(
        self,
        char1: str,
        char2: str
    ) -> str:
        """Compare two characters and provide analysis"""
        if not self.enabled:
            return "Ollama assistant not available."
        
        # Get character data
        context_parts = []
        
        if self.rag_system and self.rag_system.enabled:
            for char_name in [char1, char2]:
                results = self.rag_system.search(
                    query=char_name,
                    top_k=1,
                    doc_type="character"
                )
                if results:
                    context_parts.append(f"=== {char_name} ===")
                    context_parts.append(results[0][0].content)
                    context_parts.append("")
        
        prompt = f"""{self.system_context}

{chr(10).join(context_parts)}

Please compare these two characters: {char1} vs {char2}

Provide a detailed comparison covering:
1. Stats and rarity
2. Special attacks and their effectiveness
3. Passive abilities
4. Best use cases for each
5. Which is better for different strategies (offense, defense, support)

Answer:"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=_http_timeout_seconds()
                )
                
                result = response.json()
                return result.get("response", "No response generated")
                
        except Exception as e:
            logger.error(f"Error comparing characters: {e}")
            return f"Error: {str(e)}"
    
    async def suggest_team_composition(
        self,
        strategy: str,
        owned_characters: Optional[List[str]] = None
    ) -> str:
        """Suggest team composition based on strategy"""
        if not self.enabled:
            return "Ollama assistant not available."
        
        # Get relevant characters from RAG
        context = ""
        if self.rag_system and self.rag_system.enabled:
            # Search for characters
            char_results = self.rag_system.search_characters(strategy, top_k=10)
            if char_results:
                context = "=== Available Characters for Strategy ===\n"
                for doc, score in char_results:
                    context += f"\n[Score: {score:.2f}]\n{doc.content}\n"
            
            # Search for equipment that matches the strategy
            equip_results = self.rag_system.search_equipment(strategy, top_k=15)
            if equip_results:
                context += "\n=== Available Equipment for Strategy ===\n"
                for doc, score in equip_results:
                    context += f"\n[Score: {score:.2f}]\n{doc.content}\n"
        
        owned_filter = ""
        if owned_characters:
            owned_filter = f"\nNote: User owns these characters: {', '.join(owned_characters)}"
        
        prompt = f"""{self.system_context}

{context}

Strategy: {strategy}
{owned_filter}

Please suggest an optimal 3-character team for this strategy. Include:
1. Team composition (starter + 2 support)
2. Reasoning for each character choice
3. Synergies between team members
4. REQUIRED: Recommended equipment for EACH character (weapon, armor, accessory)
5. Explain how the equipment enhances each character
6. Gameplay tips for this team

IMPORTANT: You MUST suggest specific equipment items from the available equipment list for each character.

Answer:"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=_http_timeout_seconds()
                )
                
                result = response.json()
                return result.get("response", "No response generated")
                
        except Exception as e:
            logger.error(f"Error suggesting team: {e}")
            return f"Error: {str(e)}"
    
    def _build_mechanic_rag_context(self, mechanic: str) -> str:
        """Semantic search across all document types with context budget safeguards."""
        if not self.rag_system or not self.rag_system.enabled:
            return ""

        try:
            top_k = int(os.getenv("MKM_MECHANIC_RAG_TOP_K", "16"))
        except ValueError:
            top_k = 16
        top_k = max(6, min(28, top_k))

        try:
            max_passages = int(os.getenv("MKM_MECHANIC_RAG_MAX_PASSAGES", "8"))
        except ValueError:
            max_passages = 8
        max_passages = max(3, min(16, max_passages))

        try:
            max_chars = int(os.getenv("MKM_MECHANIC_RAG_MAX_CHARS", "3600"))
        except ValueError:
            max_chars = 3600
        max_chars = max(1200, min(18000, max_chars))

        variants = [mechanic.strip()] if mechanic and mechanic.strip() else []
        lowered = mechanic.lower() if mechanic else ""
        if "classic" in lowered and "klassic" not in lowered:
            variants.append(re.sub(r"\bclassic\b", "klassic", mechanic, flags=re.IGNORECASE))
        if "klassic" in lowered and "classic" not in lowered:
            variants.append(re.sub(r"\bklassic\b", "classic", mechanic, flags=re.IGNORECASE))

        dedup_variants: List[str] = []
        seen_variants: set[str] = set()
        for v in variants:
            key = v.strip().lower()
            if key and key not in seen_variants:
                seen_variants.add(key)
                dedup_variants.append(v.strip())

        type_priorities = {
            "gameplay": 0,
            "glossary": 0,
            "character": 1,
            "equipment": 1,
        }
        per_type_top_k = {
            "gameplay": top_k,
            "glossary": top_k,
            "character": max(6, top_k // 2),
            "equipment": max(6, top_k // 2),
        }
        per_type_min_similarity = {
            "gameplay": 0.18,
            "glossary": 0.18,
            "character": 0.20,
            "equipment": 0.20,
        }

        results_pool: Dict[str, Tuple[object, float]] = {}
        for variant in (dedup_variants or [mechanic]):
            for doc_type in ["gameplay", "glossary", "character", "equipment"]:
                for doc, score in self.rag_system.search(
                    variant,
                    top_k=per_type_top_k[doc_type],
                    doc_type=doc_type,
                    min_similarity=per_type_min_similarity[doc_type],
                ):
                    digest = hashlib.sha256(doc.content.strip().encode("utf-8")).hexdigest()
                    key = f"{doc.doc_type}:{digest}"
                    existing = results_pool.get(key)
                    if not existing or score > existing[1]:
                        results_pool[key] = (doc, score)

        results = sorted(
            results_pool.values(),
            key=lambda x: (type_priorities.get(x[0].doc_type, 2), -x[1]),
        )
        seen_hashes: set[str] = set()
        parts: List[str] = []
        used_chars = 0
        for doc, score in results:
            digest = hashlib.sha256(doc.content.strip().encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                continue

            candidate = doc.content.strip()
            if not candidate:
                continue

            seen_hashes.add(digest)
            meta = json.dumps(doc.metadata, ensure_ascii=False) if doc.metadata else "{}"
            snippet = (
                f"### [{doc.doc_type}] (score {score:.3f}) metadata={meta}\n{doc.content}\n"
            )
            if used_chars + len(snippet) > max_chars:
                # Preserve passage integrity: skip passages that do not fit instead of clipping.
                continue

            parts.append(snippet)
            used_chars += len(snippet)

            if len(parts) >= max_passages or used_chars >= max_chars:
                break

        if not parts:
            return "=== RAG ===\nNo indexed passages matched strongly enough. Use general MK Mobile knowledge and say so if uncertain.\n"
        return "=== RAG (prioritized: gameplay/glossary, then characters/equipment) ===\n" + "\n".join(parts)

    @staticmethod
    def _strip_json_fences(text: str) -> str:
        t = text.strip()
        if not t.startswith("```"):
            return t
        lines = t.split("\n")
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _coerce_mechanic_value(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, str):
            return val.strip()
        if isinstance(val, (int, float, bool)):
            return str(val)
        if isinstance(val, list):
            return "\n".join(OllamaAssistant._coerce_mechanic_value(x) for x in val).strip()
        if isinstance(val, dict):
            try:
                return json.dumps(val, ensure_ascii=False)
            except Exception:
                return str(val).strip()
        return str(val).strip()

    def _dict_to_definition_recommendations(self, data: Any) -> Optional[Dict[str, str]]:
        if not isinstance(data, dict):
            logger.debug("_dict_to_definition_recommendations: parsed payload is not a dict")
            return None
        d_raw = data.get("definition")
        if d_raw is None:
            d_raw = data.get("Definition")
        r_raw = data.get("recommendations")
        if r_raw is None:
            r_raw = data.get("Recommendations")
        if r_raw is None:
            r_raw = data.get("recommendation") or data.get("Recommendation")

        d = self._coerce_mechanic_value(d_raw)
        r = self._coerce_mechanic_value(r_raw)

        d = d.strip()
        r = r.strip()

        if not d and not r:
            logger.debug(
                "_dict_to_definition_recommendations: dict present but mechanic keys empty; keys=%s",
                list(data.keys()),
            )
            return None
        return {"definition": d, "recommendations": r}

    def _parse_mechanic_json_object(self, text: str) -> Optional[Dict[str, str]]:
        """Try strict JSON, then JSONDecoder.raw_decode from first '{'."""
        t = self._strip_json_fences(text)
        if not t:
            logger.debug("_parse_mechanic_json_object: empty content after stripping fences")
            return None
        try:
            data = json.loads(t)
            out = self._dict_to_definition_recommendations(data)
            if out is not None:
                logger.debug("_parse_mechanic_json_object: parsed with json.loads")
                return out
        except json.JSONDecodeError as e:
            logger.debug("_parse_mechanic_json_object: json.loads failed: %s", e)
        brace = t.find("{")
        if brace != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(t[brace:])
                out = self._dict_to_definition_recommendations(obj)
                if out is not None:
                    logger.debug("_parse_mechanic_json_object: parsed with raw_decode")
                    return out
            except json.JSONDecodeError as e:
                logger.debug("_parse_mechanic_json_object: raw_decode failed: %s", e)
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(t[start : end + 1])
                out = self._dict_to_definition_recommendations(data)
                if out is not None:
                    logger.debug("_parse_mechanic_json_object: parsed with brace slicing")
                    return out
            except json.JSONDecodeError as e:
                logger.debug("_parse_mechanic_json_object: brace-slice parse failed: %s", e)
        return None

    def _parse_mechanic_fallback_sections(self, text: str) -> Optional[Dict[str, str]]:
        """When JSON is broken (unescaped quotes, etc.), split on Markdown-style headings."""
        t = (text or "").strip()
        if len(t) < 20:
            return None

        split_patterns = [
            r"(?is)\n\s*#{1,3}\s*recommendations\s*\n",
            r"(?is)^\s*#{1,3}\s*recommendations\s*\n",
            r"(?is)\n\s*\*{0,2}\s*recommendations\s*\*{0,2}\s*\n",
            r"(?is)\n\s*recommendations\s*:\s*\n",
            r"(?is)\n\s*---+\s*\n\s*recommendations\s*\n",
        ]
        for pat in split_patterns:
            m = re.search(pat, t)
            if m:
                left = t[: m.start()].strip()
                right = t[m.end() :].strip()
                left = re.sub(
                    r"(?is)^\s*#{1,3}\s*definition\s*\n",
                    "",
                    left,
                )
                left = re.sub(r"(?is)^\s*\*{0,2}\s*definition\s*\*{0,2}\s*\n", "", left)
                left = left.strip()
                if left or right:
                    return {"definition": left, "recommendations": right}

        one_block = self._strip_json_fences(t)
        if len(one_block) > 80 and "{" not in one_block[:200]:
            logger.warning(
                "explain_mechanic: using full text as definition (no JSON and no section split)"
            )
            return {"definition": one_block, "recommendations": ""}

        return None

    def _parse_mechanic_json(self, response_text: str) -> Optional[Dict[str, str]]:
        """Parse model output: JSON first, then Markdown section split, then plain prose."""
        text = (response_text or "").strip()
        if not text:
            return None

        parsed = self._parse_mechanic_json_object(text)
        if parsed is not None:
            return parsed

        fallback = self._parse_mechanic_fallback_sections(text)
        if fallback is not None:
            logger.warning("explain_mechanic: recovered using non-JSON fallback parse")
        return fallback

    async def explain_mechanic(
        self,
        mechanic: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Explain a game mechanic using broad RAG context and structured JSON from the model.

        Returns:
            On success: {"definition": str, "recommendations": str}
            On failure: {"error": str}
        """
        if not self.enabled:
            return {"error": "Ollama assistant not available."}

        use_model = self._resolve_model_name(model)
        context = self._build_mechanic_rag_context(mechanic)

        system_prompt = f"""{self.system_context}

You explain Mortal Kombat Mobile mechanics using the RAG context below when relevant.

=== RULES ===
- "definition": What the mechanic is, how it works in combat/modes, and how it interacts with other systems. Ground this in the RAG passages when possible.
- "recommendations": Practical tips: team ideas, equipment that synergizes, counters, and mode-specific advice. Keep this separate from the neutral definition.
- Use Markdown inside the JSON string values (headings, bullets) where helpful.
- Inside JSON strings, escape any double-quote character as \\" and use \\n for newlines so the output is valid JSON.
- If RAG is thin, say what is unknown and avoid inventing specific card or gear names not supported by context.

Respond with ONLY valid JSON (no markdown code fences, no text before or after the object) in this exact shape:
{{"definition": "...", "recommendations": "..."}}"""

        user_prompt = f"""RAG context for mechanic: "{mechanic}"

{context}

Produce the JSON for this mechanic."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": use_model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False,
                        "format": "json",
                        "keep_alive": 0,
                        "options": {
                            "temperature": 0.25,
                            "num_predict": int(os.getenv("MKM_MECHANIC_NUM_PREDICT", "1200")),
                        },
                    },
                    timeout=_http_timeout_seconds(),
                )

                if response.status_code != 200:
                    detail = ""
                    try:
                        detail = str(response.json().get("error", "")).strip()
                    except Exception:
                        detail = (response.text or "").strip()
                    detail = re.sub(r"\s+", " ", detail)[:300]
                    if detail:
                        return {
                            "error": f"Ollama API returned status {response.status_code}: {detail}"
                        }
                    return {"error": f"Ollama API returned status {response.status_code}"}

                result = response.json()
                raw = (result.get("response") or "").strip()
                parsed = self._parse_mechanic_json(raw)
                if parsed is None:
                    preview = re.sub(r"\s+", " ", raw[:300]) if raw else ""
                    logger.warning(
                        "explain_mechanic: parse failed for model=%s, raw_preview=%s",
                        use_model,
                        preview,
                    )
                    return {
                        "error": "Model response could not be parsed into mechanic sections.",
                    }

                parsed["definition"] = parsed["definition"].strip()
                parsed["recommendations"] = parsed["recommendations"].strip()

                if not parsed["definition"] and not parsed["recommendations"]:
                    return {"error": "Empty definition and recommendations from model"}

                return parsed

        except Exception as e:
            if HTTPX_AVAILABLE and isinstance(
                e,
                (
                    httpx.ReadTimeout,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                    httpx.HTTPError,
                ),
            ):
                logger.error("Error explaining mechanic (transport): %s", e)
                return {
                    "error": "Connection to Ollama failed while generating mechanic explanation. Please retry.",
                }
            logger.error(f"Error explaining mechanic: {e}")
            return {"error": str(e)}


# Singleton instance
_ollama_assistant: Optional[OllamaAssistant] = None


def get_ollama_assistant(
    rag_system: Optional[RAGSystem] = None
) -> OllamaAssistant:
    """Get or create Ollama assistant singleton"""
    global _ollama_assistant
    if _ollama_assistant is None:
        _ollama_assistant = OllamaAssistant(rag_system=rag_system)
    return _ollama_assistant
