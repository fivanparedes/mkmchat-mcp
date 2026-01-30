"""MCP Server for Mortal Kombat Mobile assistance"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from mkmchat.tools import (
    get_character_info,
    get_equipment_info,
    suggest_team,
    semantic_search,
    search_characters_advanced,
    search_equipment_advanced,
    ask_ollama,
    compare_characters_ollama,
    suggest_team_ollama,
    explain_mechanic_ollama,
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
    ] # type: ignore


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
