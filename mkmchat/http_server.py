"""HTTP Server for MK Mobile Assistant API"""

import asyncio
import hmac
import json
import logging
import os
from collections import defaultdict, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import monotonic
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict

from mkmchat.llm.ollama import get_ollama_assistant
from mkmchat.tools.semantic_search import get_rag_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default port
DEFAULT_PORT = 8080

_IP_REQUESTS = defaultdict(deque)
_IP_BURST_REQUESTS = defaultdict(deque)


def build_structured_context(rag, strategy: str) -> Dict[str, str]:
    """
    Build clearly structured context for the LLM to reduce hallucinations.
    
    Returns dict with separate lists for characters and equipment by type.
    Results are already sorted by tier from RAG system (prioritize_tier=True).
    """
    from pathlib import Path
    
    context = {
        "characters": "",
        "weapons": "",
        "armor": "",
        "accessories": "",
        "glossary": "",
        "gameplay": ""
    }

    package_dir = Path(__file__).resolve().parent
    data_dir = package_dir / "data"
    
    # Load glossary from file
    glossary_file = data_dir / "glossary.txt"
    if glossary_file.exists():
        context["glossary"] = glossary_file.read_text(encoding='utf-8').strip()
    
    # Load gameplay from file
    gameplay_file = data_dir / "gameplay.txt"
    if gameplay_file.exists():
        context["gameplay"] = gameplay_file.read_text(encoding='utf-8').strip()
    
    if not rag or not rag.enabled:
        return context
    
    # Get characters - already sorted by tier in RAG (prioritize_tier=True by default)
    char_results = rag.search_characters(strategy, top_k=60)
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
        char_list.append(f"- [{tier}] Rarity: {rarity} | Name: {name} | Passive: {passive}" if passive else f"- [{tier}] Rarity: {rarity} | Name: {name}")
    
    context["characters"] = "\n".join(char_list) if char_list else "No matches found"
    
    # Get equipment - already sorted by tier in RAG, separate by type for display
    equip_results = rag.search_equipment(strategy, top_k=40)
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
    context["weapons"] = "\n".join(weapons[:]) if weapons else "None found"
    context["armor"] = "\n".join(armor[:]) if armor else "None found"
    context["accessories"] = "\n".join(accessories[:]) if accessories else "None found"
    
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
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "error": "Ollama assistant not available. Make sure Ollama is running."
            }
        
        # Use the requested model or fall back to the assistant's default
        use_model = model or assistant.model_name
        
        # Build STRUCTURED context to reduce hallucinations
        context = build_structured_context(rag, strategy)
        
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

        # Log prompt and context to file (overwrite each call)
        from pathlib import Path
        log_file = Path(__file__).resolve().parent / "prompt_debug.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== SYSTEM PROMPT ===\n{system_prompt}\n\n")
            f.write(f"=== USER PROMPT ===\n{user_prompt}\n")
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
                timeout=None
            )
            
            if response.status_code != 200:
                return {"error": f"Ollama API returned status {response.status_code}"}
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Try to parse the JSON response
            try:
                team_data = json.loads(response_text)
                return {"response": team_data}
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response
                logger.warning(f"Failed to parse JSON directly: {e}")
                
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx + 1]
                    try:
                        team_data = json.loads(json_str)
                        return {"response": team_data}
                    except json.JSONDecodeError:
                        pass
                
                # Return raw response if JSON parsing fails
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": response_text
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

        # Use the requested model or fall back to the assistant's default
        use_model = model or assistant.model_name

        context = build_structured_context(rag, question)

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
                timeout=None
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
                    "/health": {
                        "method": "GET",
                        "description": "Detailed health / status of RAG system, LLM, and data cache"
                    }
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        elif parsed_path.path == "/health":
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
        except Exception as e:
            logger.error(f"Error handling /health: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"status": "error", "detail": str(e)}).encode())
    
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

    def log_message(self, format, *args):
        """Override to use logging module"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(port: int = DEFAULT_PORT):
    """Run the HTTP server"""
    host = os.getenv("MKM_HTTP_HOST", "127.0.0.1")
    server_address = (host, port)
    httpd = HTTPServer(server_address, MKMobileHTTPHandler)
    
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
