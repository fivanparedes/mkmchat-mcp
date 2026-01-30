"""LLM-powered tools for intelligent game querying"""

import logging
from typing import Dict, Any, Optional, List

from mkmchat.llm.ollama import get_ollama_assistant
from mkmchat.tools.semantic_search import get_rag_system

logger = logging.getLogger(__name__)


# Ollama-specific tools
async def ask_ollama(
    question: str,
    use_context: bool = True
) -> Dict[str, Any]:
    """
    Ask the Ollama local assistant a question about the game
    
    Args:
        question: Natural language question about MK Mobile
        use_context: Whether to use RAG context for answering
        
    Returns:
        MCP response with assistant's answer
    """
    try:
        rag = get_rag_system() if use_context else None
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Ollama assistant not available. Make sure Ollama is running (ollama serve) and the model is pulled (ollama pull llama3.2:3b)"
                    }
                ]
            }
        
        response = await assistant.query(question, use_rag=use_context)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Ollama Assistant Response (Model: {assistant.model_name})\n\n{response}"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in ask_ollama: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }


async def compare_characters_ollama(
    character1: str,
    character2: str
) -> Dict[str, Any]:
    """
    Compare two characters using Ollama local AI
    
    Args:
        character1: First character name
        character2: Second character name
        
    Returns:
        MCP response with comparison analysis
    """
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Ollama assistant not available."
                    }
                ]
            }
        
        response = await assistant.compare_characters(character1, character2)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Character Comparison: {character1} vs {character2}\n\n{response}"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in compare_characters_ollama: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }


async def suggest_team_ollama(
    strategy: str,
    owned_characters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get Ollama-powered team composition suggestions
    
    Args:
        strategy: Desired strategy (e.g., "aggressive rush", "defensive tank")
        owned_characters: Optional list of characters the player owns
        
    Returns:
        MCP response with team suggestions
    """
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Ollama assistant not available."
                    }
                ]
            }
        
        response = await assistant.suggest_team_composition(strategy, owned_characters)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Team Suggestion for: {strategy}\n\n{response}"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in suggest_team_ollama: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }


async def explain_mechanic_ollama(
    mechanic: str
) -> Dict[str, Any]:
    """
    Get detailed Ollama explanation of a game mechanic
    
    Args:
        mechanic: Game mechanic to explain
        
    Returns:
        MCP response with explanation
    """
    try:
        rag = get_rag_system()
        assistant = get_ollama_assistant(rag_system=rag)
        
        if not assistant.enabled:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Ollama assistant not available."
                    }
                ]
            }
        
        response = await assistant.explain_mechanic(mechanic)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Game Mechanic: {mechanic}\n\n{response}"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in explain_mechanic_ollama: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }
