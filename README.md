# mkmchat-mcp - Mortal Kombat Mobile Assistant

A RAG-powered MCP server and HTTP API for Mortal Kombat Mobile. Get AI-powered team suggestions, character comparisons, and game mechanic explanations using local LLM (Ollama).

## Features

- 🎮 **Character Database**: 185+ MK Mobile characters with abilities and passives
- ⚔️ **Equipment Database**: 280+ equipment items with effects and fusion bonuses
- 🤝 **Team Suggestions**: AI-powered team composition based on strategy
- 🔍 **Semantic Search**: RAG-powered natural language search across all game data
- 🖥️ **Local AI**: Ollama integration (llama3.2:3b) - free, private, offline-capable
- 🌐 **HTTP API**: REST endpoint for team suggestions with structured JSON output

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Setup Ollama (local AI)
./setup_ollama.sh
```

### Running

```bash
# Option 1: MCP Server (for Claude Desktop, VS Code, etc.)
python -m mkmchat

# Option 2: HTTP API Server
python -m mkmchat http
python -m mkmchat http 9000  # Custom port
```

### HTTP API Usage

```bash
# Get team suggestion
curl -X POST http://localhost:8080/suggest-team \
  -H "Content-Type: application/json" \
  -d '{"strategy": "fire damage team"}'

# Response format:
{
  "response": {
    "char1": {"name": "...", "passive": "...", "equipment": [...]},
    "char2": {"name": "...", "passive": "...", "equipment": [...]},
    "char3": {"name": "...", "passive": "...", "equipment": [...]},
    "strategy": "explanation..."
  }
}
```

### MCP Client Configuration

Add to Claude Desktop config (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mkmchat": {
      "command": "python",
      "args": ["-m", "mkmchat"],
      "cwd": "/path/to/mkmchat-mcp"
    }
  }
}
```

## Available Tools

### Data Tools (3)
| Tool | Description |
|------|-------------|
| `get_character_info` | Character details with fuzzy name matching |
| `get_equipment_info` | Equipment details with fuzzy name matching |
| `suggest_team` | Rule-based team suggestions |

### Search Tools (3)
| Tool | Description |
|------|-------------|
| `semantic_search` | RAG-powered search across all game data |
| `search_characters_advanced` | Filter by rarity, class, tier, keyword |
| `search_equipment_advanced` | Filter by rarity, type, tier, keyword |

### LLM Tools - Ollama (4)
| Tool | Description |
|------|-------------|
| `ask_ollama` | General questions with RAG context |
| `compare_characters_ollama` | AI character comparison |
| `suggest_team_ollama` | AI team composition suggestions |
| `explain_mechanic_ollama` | AI game mechanic explanations |

## Project Structure

```
mkmchat-mcp/
├── data/                    # Game data (TSV files)
│   ├── characters.tsv       # 185 characters
│   ├── abilities.tsv        # Special attacks
│   ├── passives.tsv         # Passive abilities
│   ├── equipment_*.tsv      # 280+ equipment items
│   ├── glossary.txt         # Game terminology
│   └── gameplay.txt         # Game mechanics
├── mkmchat/
│   ├── server.py            # MCP server
│   ├── http_server.py       # HTTP API server
│   ├── data/
│   │   ├── loader.py        # Data loading + fuzzy search
│   │   └── rag.py           # RAG system (embeddings)
│   ├── llm/
│   │   └── ollama.py        # Ollama LLM assistant
│   ├── tools/               # MCP tool implementations
│   └── models/              # Pydantic data models
└── tests/                   # Test suite
```

## Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Ollama URL | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| Ollama Model | `OLLAMA_MODEL` | `llama3.2:3b` |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture diagrams
- [OLLAMA_INTEGRATION.md](OLLAMA_INTEGRATION.md) - Local AI setup guide
- [OLLAMA_QUICK_REFERENCE.md](OLLAMA_QUICK_REFERENCE.md) - Ollama commands
- [RAG_SYSTEM.md](RAG_SYSTEM.md) - RAG system documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Development

```bash
pip install -e ".[dev]"
pytest                    # Run tests
black mkmchat tests       # Format code
ruff check mkmchat tests  # Lint
```

## License

GNU GPL v3.0 - See [LICENSE](LICENSE)
