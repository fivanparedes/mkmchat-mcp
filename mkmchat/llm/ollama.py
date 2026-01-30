"""Ollama local LLM integration for intelligent game querying"""

import os
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


class OllamaAssistant:
    """Ollama-powered assistant for MK Mobile game queries"""
    
    def __init__(
        self,
        model_name: str = "llama3.2:3b",
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
        self.model_name = model_name
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
                    timeout=None  # No timeout - wait for response
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
                    timeout=None  # No timeout - wait for response
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
                    timeout=None  # No timeout - wait for response
                )
                
                result = response.json()
                return result.get("response", "No response generated")
                
        except Exception as e:
            logger.error(f"Error suggesting team: {e}")
            return f"Error: {str(e)}"
    
    async def explain_mechanic(
        self,
        mechanic: str
    ) -> str:
        """Explain a game mechanic in detail"""
        if not self.enabled:
            return "Ollama assistant not available."
        
        # Get relevant context from RAG
        context = ""
        if self.rag_system and self.rag_system.enabled:
            gameplay_results = self.rag_system.search_gameplay(mechanic, top_k=3)
            glossary_results = self.rag_system.search_glossary(mechanic, top_k=3)
            
            if gameplay_results:
                context += "=== Gameplay Information ===\n"
                for doc, score in gameplay_results:
                    context += f"\n{doc.content}\n"
            
            if glossary_results:
                context += "\n=== Glossary ===\n"
                for doc, score in glossary_results:
                    context += f"\n{doc.content}\n"
        
        prompt = f"""{self.system_context}

{context}

Please explain this game mechanic: {mechanic}

Include:
1. What it is and how it works
2. Which characters/equipment use it
3. Strategic implications
4. Tips for using or countering it

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
                    timeout=None  # No timeout - wait for response
                )
                
                result = response.json()
                return result.get("response", "No response generated")
                
        except Exception as e:
            logger.error(f"Error explaining mechanic: {e}")
            return f"Error: {str(e)}"


# Singleton instance
_ollama_assistant: Optional[OllamaAssistant] = None


def get_ollama_assistant(
    rag_system: Optional[RAGSystem] = None
) -> OllamaAssistant:
    """Get or create Ollama assistant singleton"""
    global _ollama_assistant
    if _ollama_assistant is None:
        _ollama_assistant = OllamaAssistant(rag_system=rag_system, model_name='dolphin-llama3:8b')
    return _ollama_assistant
