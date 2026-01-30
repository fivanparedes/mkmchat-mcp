"""MCP tools for MK Mobile assistance - 10 tools total"""

from mkmchat.tools.character_info import get_character_info
from mkmchat.tools.equipment_info import get_equipment_info
from mkmchat.tools.team_suggest import suggest_team
from mkmchat.tools.semantic_search import (
    semantic_search,
    search_characters_advanced,
    search_equipment_advanced,
    get_rag_system,
)
from mkmchat.tools.llm_tools import (
    ask_ollama,
    compare_characters_ollama,
    suggest_team_ollama,
    explain_mechanic_ollama,
)

__all__ = [
    # Data retrieval (3)
    "get_character_info",
    "get_equipment_info",
    "suggest_team",
    # Search (3)
    "semantic_search",
    "search_characters_advanced",
    "search_equipment_advanced",
    # LLM/Ollama (4)
    "ask_ollama",
    "compare_characters_ollama",
    "suggest_team_ollama",
    "explain_mechanic_ollama",
    # Utilities
    "get_rag_system",
]
