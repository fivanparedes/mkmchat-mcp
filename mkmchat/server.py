"""MCP Server for Mortal Kombat Mobile assistance"""

import asyncio
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from mkmchat.tools.character_info import get_character_info
from mkmchat.tools.equipment_info import get_equipment_info
from mkmchat.tools.team_suggest import suggest_team
from mkmchat.tools.semantic_search import (
    semantic_search, search_by_strategy, explain_mechanic,
    search_characters_advanced, search_equipment_advanced, search_glossary_term,
    search_gameplay
)
from mkmchat.tools.llm_tools import (
    ask_assistant, compare_characters_llm, suggest_team_llm, explain_mechanic_llm,
    ask_ollama, compare_characters_ollama, suggest_team_ollama, explain_mechanic_ollama
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("mkmchat")


@app.list_tools()
async def list_tools():
    """List available MCP tools"""
    return [
        Tool(
            name="get_character_info",
            description="Get detailed information about a Mortal Kombat Mobile character including stats, abilities, and strategies",
            inputSchema={
                "type": "object",
                "properties": {
                    "character_name": {
                        "type": "string",
                        "description": "Name of the character (e.g., 'Scorpion', 'Sub-Zero', 'Klassic Liu Kang')"
                    }
                },
                "required": ["character_name"]
            }
        ),
        Tool(
            name="get_equipment_info",
            description="Get information about equipment/gear including type, effects, and max fusion effects",
            inputSchema={
                "type": "object",
                "properties": {
                    "equipment_name": {
                        "type": "string",
                        "description": "Name of the equipment (e.g., 'Amulet', 'Shuriken', 'Bracers')"
                    }
                },
                "required": ["equipment_name"]
            }
        ),
        Tool(
            name="suggest_team",
            description="Assemble a custom 3-character team with equipment recommendations based on strategy. Creates optimal team compositions by analyzing character stats, abilities, and synergies. Includes equipment suggestions for each team member.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Desired strategy (e.g., 'high damage', 'tank', 'balanced', 'boss battles', 'class synergy')"
                    },
                    "owned_characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of character names the player owns (optional, filters available characters)"
                    },
                    "required_character": {
                        "type": "string",
                        "description": "A specific character that must be included as starter in the team (optional)"
                    }
                },
                "required": ["strategy"]
            }
        ),
        Tool(
            name="semantic_search",
            description="Perform intelligent semantic search across all game data (characters, equipment, gameplay, glossary). Uses AI embeddings to find relevant information based on natural language queries. Better than exact name matching for exploratory queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'characters with fire attacks', 'equipment that boosts critical hit')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by document type: 'character', 'equipment', 'gameplay', or 'glossary' (optional)",
                        "enum": ["character", "equipment", "gameplay", "glossary"]
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimum similarity score 0-1 (default: 0.3)",
                        "default": 0.3
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_by_strategy",
            description="Search for characters AND equipment that match a specific gameplay strategy. Returns combined results optimized for the strategy with relevance scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Strategy description (e.g., 'high damage dealer', 'defensive tank', 'support healer', 'crowd control')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results per category (default: 5)",
                        "default": 5
                    }
                },
                "required": ["strategy"]
            }
        ),
        Tool(
            name="explain_mechanic",
            description="Explain game mechanics, terminology, or gameplay concepts. Searches both gameplay mechanics documentation and glossary to provide comprehensive explanations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mechanic_query": {
                        "type": "string",
                        "description": "Question about game mechanics or terms (e.g., 'How does power drain work?', 'What is a brutality?', 'Explain tag-in mechanics')"
                    }
                },
                "required": ["mechanic_query"]
            }
        ),
        Tool(
            name="search_characters_advanced",
            description="Search characters by attributes like rarity, class, tier, or keywords in abilities/passives. Better than name search when you want to find 'all Diamond Martial Artists' or 'characters with fire abilities'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rarity": {
                        "type": "string",
                        "description": "Filter by rarity: Diamond, Gold, Silver, Bronze",
                        "enum": ["Diamond", "Gold", "Silver", "Bronze"]
                    },
                    "char_class": {
                        "type": "string",
                        "description": "Filter by class: Martial Artist, Spec Ops, Outworld, Netherrealm, Elder God",
                        "enum": ["Martial Artist", "Spec Ops", "Outworld", "Netherrealm", "Elder God"]
                    },
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier: S+, S, A, B, C, D",
                        "enum": ["S+", "S", "A", "B", "C", "D"]
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword in passives/abilities (e.g., 'fire', 'stun', 'bleed', 'power drain')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_equipment_advanced",
            description="Search equipment by attributes like rarity, type, tier, or keywords in effects. Better than name search when you want 'all Epic Weapons' or 'equipment with critical hit boost'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rarity": {
                        "type": "string",
                        "description": "Filter by rarity: Epic, Rare, Uncommon, Common",
                        "enum": ["Epic", "Rare", "Uncommon", "Common"]
                    },
                    "equip_type": {
                        "type": "string",
                        "description": "Filter by type: Weapon, Armor, Accessory",
                        "enum": ["Weapon", "Armor", "Accessory"]
                    },
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier: S+, S, A, B, C, D",
                        "enum": ["S+", "S", "A", "B", "C", "D"]
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword in effects (e.g., 'fire', 'critical', 'power', 'bleed')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_glossary_term",
            description="Look up specific game terms and definitions from the glossary. Returns precise definitions for buffs, debuffs, stats, and combat mechanics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Game term to look up (e.g., 'bleed', 'stun', 'power drain', 'critical hit', 'lethal hit')"
                    }
                },
                "required": ["term"]
            }
        ),
        Tool(
            name="search_gameplay",
            description="Search for specific gameplay mechanics like tag-in/tag-out, special attacks, equipment slots, rarity differences, brutalities, etc. Returns relevant gameplay information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gameplay mechanic to search for (e.g., 'tag-in', 'special attacks', 'equipment slots', 'diamond characters', 'brutality')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_assistant",
            description="Ask the AI assistant (Gemini) any question about MK Mobile. Uses RAG context and LLM reasoning for intelligent, conversational answers. Best for complex questions, strategy advice, or when you need explanations beyond raw data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the game (e.g., 'What's the best team for boss battles?', 'How do I counter power drain?', 'Explain the meta for diamond characters')"
                    },
                    "use_context": {
                        "type": "boolean",
                        "description": "Whether to use RAG context for answering (default: true)",
                        "default": True
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="compare_characters_llm",
            description="AI-powered comparison of two characters. Analyzes stats, abilities, synergies, and provides strategic recommendations on which is better for different scenarios.",
            inputSchema={
                "type": "object",
                "properties": {
                    "character1": {
                        "type": "string",
                        "description": "First character name"
                    },
                    "character2": {
                        "type": "string",
                        "description": "Second character name"
                    }
                },
                "required": ["character1", "character2"]
            }
        ),
        Tool(
            name="suggest_team_llm",
            description="AI-powered team composition suggestions. More intelligent than rule-based suggestions - considers synergies, meta strategies, and provides detailed reasoning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Desired strategy (e.g., 'aggressive rush down', 'defensive tank', 'boss killer', 'faction wars')"
                    },
                    "owned_characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of characters you own to filter suggestions"
                    }
                },
                "required": ["strategy"]
            }
        ),
        Tool(
            name="explain_mechanic_llm",
            description="AI-powered explanation of game mechanics. More comprehensive than RAG-only search - provides context, examples, and strategic implications.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mechanic": {
                        "type": "string",
                        "description": "Game mechanic to explain (e.g., 'power drain', 'tag-in attacks', 'brutalities', 'fusion')"
                    }
                },
                "required": ["mechanic"]
            }
        ),
        # Ollama local LLM tools
        Tool(
            name="ask_ollama",
            description="Ask the local Ollama AI assistant (llama3.2:3b) any question about MK Mobile. Runs locally on CPU without API costs. Best for privacy-conscious users or offline usage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the game"
                    },
                    "use_context": {
                        "type": "boolean",
                        "description": "Whether to use RAG context for answering (default: true)",
                        "default": True
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="compare_characters_ollama",
            description="Compare two characters using local Ollama AI. Provides detailed analysis without cloud API costs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "character1": {
                        "type": "string",
                        "description": "First character name"
                    },
                    "character2": {
                        "type": "string",
                        "description": "Second character name"
                    }
                },
                "required": ["character1", "character2"]
            }
        ),
        Tool(
            name="suggest_team_ollama",
            description="Get team composition suggestions from local Ollama AI. Private and offline-capable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Desired strategy (e.g., 'aggressive rush down', 'defensive tank')"
                    },
                    "owned_characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of characters you own"
                    }
                },
                "required": ["strategy"]
            }
        ),
        Tool(
            name="explain_mechanic_ollama",
            description="Explain game mechanics using local Ollama AI. Comprehensive explanations without cloud dependencies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mechanic": {
                        "type": "string",
                        "description": "Game mechanic to explain"
                    }
                },
                "required": ["mechanic"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "get_character_info":
            return await get_character_info(arguments["character_name"])
        elif name == "get_equipment_info":
            return await get_equipment_info(arguments["equipment_name"])
        elif name == "suggest_team":
            return await suggest_team(
                strategy=arguments["strategy"],
                owned_characters=arguments.get("owned_characters"),
                required_character=arguments.get("required_character")
            )
        elif name == "semantic_search":
            return await semantic_search(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5),
                doc_type=arguments.get("doc_type"),
                min_similarity=arguments.get("min_similarity", 0.3)
            )
        elif name == "search_by_strategy":
            return await search_by_strategy(
                strategy=arguments["strategy"],
                top_k=arguments.get("top_k", 5)
            )
        elif name == "explain_mechanic":
            return await explain_mechanic(
                mechanic_query=arguments["mechanic_query"]
            )
        elif name == "search_characters_advanced":
            return await search_characters_advanced(
                rarity=arguments.get("rarity"),
                char_class=arguments.get("char_class"),
                tier=arguments.get("tier"),
                keyword=arguments.get("keyword")
            )
        elif name == "search_equipment_advanced":
            return await search_equipment_advanced(
                rarity=arguments.get("rarity"),
                equip_type=arguments.get("equip_type"),
                tier=arguments.get("tier"),
                keyword=arguments.get("keyword")
            )
        elif name == "search_glossary_term":
            return await search_glossary_term(
                term=arguments["term"]
            )
        elif name == "search_gameplay":
            return await search_gameplay(
                query=arguments["query"]
            )
        elif name == "ask_assistant":
            return await ask_assistant(
                question=arguments["question"],
                use_context=arguments.get("use_context", True)
            )
        elif name == "compare_characters_llm":
            return await compare_characters_llm(
                character1=arguments["character1"],
                character2=arguments["character2"]
            )
        elif name == "suggest_team_llm":
            return await suggest_team_llm(
                strategy=arguments["strategy"],
                owned_characters=arguments.get("owned_characters")
            )
        elif name == "explain_mechanic_llm":
            return await explain_mechanic_llm(
                mechanic=arguments["mechanic"]
            )
        elif name == "ask_ollama":
            return await ask_ollama(
                question=arguments["question"],
                use_context=arguments.get("use_context", True)
            )
        elif name == "compare_characters_ollama":
            return await compare_characters_ollama(
                character1=arguments["character1"],
                character2=arguments["character2"]
            )
        elif name == "suggest_team_ollama":
            return await suggest_team_ollama(
                strategy=arguments["strategy"],
                owned_characters=arguments.get("owned_characters")
            )
        elif name == "explain_mechanic_ollama":
            return await explain_mechanic_ollama(
                mechanic=arguments["mechanic"]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }


async def main():
    """Run the MCP server"""
    logger.info("Starting MK Mobile MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
