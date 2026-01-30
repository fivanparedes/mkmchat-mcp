"""HTTP Server for MK Mobile Assistant API"""

import asyncio
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict

from mkmchat.llm.ollama import get_ollama_assistant
from mkmchat.tools.semantic_search import get_rag_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default port
DEFAULT_PORT = 8080


def build_structured_context(rag, strategy: str) -> Dict[str, str]:
    """
    Build clearly structured context for the LLM to reduce hallucinations.
    
    Returns dict with separate lists for characters and equipment by type.
    """
    context = {
        "characters": "",
        "weapons": "",
        "armor": "",
        "accessories": ""
    }
    
    if not rag or not rag.enabled:
        return context
    
    # Get characters - extract names and passives clearly
    char_results = rag.search_characters(strategy, top_k=8)
    char_list = []
    for doc, score in char_results:
        name = doc.metadata.get("name", "Unknown")
        # Extract passive from content (it's in the document content)
        passive = ""
        for line in doc.content.split("\n"):
            if line.startswith("Passive:"):
                passive = line.replace("Passive:", "").strip()[:100]
                break
        char_list.append(f"- {name} | Passive: {passive}" if passive else f"- {name}")
    context["characters"] = "\n".join(char_list) if char_list else "No matches found"
    
    # Get equipment - separate by type using metadata
    equip_results = rag.search_equipment(strategy, top_k=20)
    weapons, armor, accessories = [], [], []
    
    for doc, score in equip_results:
        name = doc.metadata.get("name", "Unknown")
        equip_type = doc.metadata.get("type", "").strip()
        
        # Extract effect from content
        effect = ""
        for line in doc.content.split("\n"):
            if line.startswith("Effect:"):
                effect = line.replace("Effect:", "").strip()[:60]
                break
        
        item_str = f"{name}" + (f" ({effect})" if effect else "")
        
        # Categorize by type field from TSV
        if equip_type == "Weapon":
            weapons.append(item_str)
        elif equip_type == "Armor":
            armor.append(item_str)
        elif equip_type == "Accessory":
            accessories.append(item_str)
    
    context["weapons"] = "\n".join([f"- {w}" for w in weapons[:6]]) if weapons else "None found"
    context["armor"] = "\n".join([f"- {a}" for a in armor[:6]]) if armor else "None found"
    context["accessories"] = "\n".join([f"- {a}" for a in accessories[:8]]) if accessories else "None found"
    
    return context


async def suggest_team_json(
    strategy: str,
    owned_characters: Optional[List[str]] = None
) -> dict:
    """
    Get team composition suggestions as structured JSON
    
    Args:
        strategy: Desired strategy (e.g., "aggressive rush", "defensive tank")
        owned_characters: Optional list of characters the player owns
        
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
        
        # Build STRUCTURED context to reduce hallucinations
        context = build_structured_context(rag, strategy)
        
        owned_filter = ""
        if owned_characters:
            owned_filter = f"\nUser owns: {', '.join(owned_characters)}. Prioritize these characters."
        
        # Simplified prompt with explicit instructions and clear data separation
        prompt = f"""You are a Mortal Kombat Mobile team builder assistant.

=== AVAILABLE CHARACTERS (pick exactly 3 from this list) ===
{context['characters']}

=== AVAILABLE WEAPONS (pick 1 per character from this list) ===
{context['weapons']}

=== AVAILABLE ARMOR (pick 1 per character from this list) ===
{context['armor']}

=== AVAILABLE ACCESSORIES (pick 2 per character from this list) ===
{context['accessories']}

STRICT RULES:
1. Pick character names EXACTLY as shown in the AVAILABLE CHARACTERS list
2. Pick weapon names EXACTLY as shown in the AVAILABLE WEAPONS list
3. Pick armor names EXACTLY as shown in the AVAILABLE ARMOR list
4. Pick accessory names EXACTLY as shown in the AVAILABLE ACCESSORIES list
5. Each character gets: 1 weapon, 1 armor, 2 accessories
6. Do NOT invent or modify names
{owned_filter}

Strategy requested: {strategy}

Respond with ONLY this JSON structure (no other text):
{{
    "char1": {{"name": "<exact character name>", "passive": "<passive description>", "equipment": [{{"slot": "weapon", "name": "<exact weapon name>", "effect": "<effect>"}}, {{"slot": "armor", "name": "<exact armor name>", "effect": "<effect>"}}, {{"slot": "accessory1", "name": "<exact accessory name>", "effect": "<effect>"}}, {{"slot": "accessory2", "name": "<exact accessory name>", "effect": "<effect>"}}]}},
    "char2": {{"name": "<exact character name>", "passive": "<passive description>", "equipment": [same structure as char1]}},
    "char3": {{"name": "<exact character name>", "passive": "<passive description>", "equipment": [same structure as char1]}},
    "strategy": "<explanation of team synergy and how to use it>"
}}"""

        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{assistant.base_url}/api/generate",
                json={
                    "model": assistant.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
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


class MKMobileHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MK Mobile API"""
    
    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
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
                "version": "2.0.0",
                "endpoints": {
                    "/suggest-team": {
                        "method": "POST",
                        "description": "Get AI-powered team suggestions",
                        "body": {
                            "strategy": "string (required)",
                            "owned_characters": "array of strings (optional)"
                        }
                    }
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/suggest-team":
            self._handle_suggest_team()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def _handle_suggest_team(self):
        """Handle /suggest-team endpoint"""
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            
            if content_length == 0:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Request body required",
                    "expected": {"strategy": "string", "owned_characters": ["optional", "array"]}
                }).encode())
                return
            
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                return
            
            # Validate required fields
            strategy = data.get("strategy")
            if not strategy:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Missing required field: strategy"
                }).encode())
                return
            
            owned_characters = data.get("owned_characters")
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    suggest_team_json(strategy, owned_characters)
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
    
    def log_message(self, format, *args):
        """Override to use logging module"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(port: int = DEFAULT_PORT):
    """Run the HTTP server"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, MKMobileHTTPHandler)
    
    logger.info(f"Starting MK Mobile HTTP API server on port {port}")
    logger.info(f"API endpoint: http://localhost:{port}/suggest-team")
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
