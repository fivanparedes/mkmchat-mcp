# mkmchat-mcp - Mortal Kombat Mobile Assistant

RAG system that implements MCP tools which speaks to LLM (local or cloud) to reply questions about the game Mortal Kombat Mobile. The goal of this project is to make a system that can actually make useful replies and suggestions, and for myself to learn MCP and different RAG processing paradigms.

An MCP (Model Context Protocol) server that provides intelligent assistance for Mortal Kombat Mobile players. Query character information, compare equipment, and get optimal team composition suggestions.

## Features

- 🎮 **Character Information**: Get detailed stats, abilities, and strategies for 185+ MK Mobile characters
- ⚔️ **Equipment Database**: Query 282 equipment items with effects and fusion bonuses
- 🤝 **Team Suggestions**: Rule-based team composition recommendations based on synergies
- 🔍 **Smart Search**: Fuzzy name matching, attribute filtering, and keyword search
- 🧠 **RAG-Powered Search**: Semantic search across all game data using AI embeddings
- 🤖 **Gemini AI Integration**: Cloud-based conversational AI (gemini-2.0-flash)
- 🖥️ **Ollama Local AI**: Run AI locally on CPU without API costs (dolphin-llama3:8b)
- 📚 **Game Knowledge**: Indexed glossary (buffs, debuffs, stats) and gameplay mechanics

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP Clients                                     │
│                  (Claude Desktop, VS Code, Custom Apps)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP Server (server.py)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MCP Tools (18 total)                         │    │
│  │  Data Tools          Search Tools           LLM Tools               │    │
│  │  • get_character_info • search_characters_  • ask_assistant         │    │
│  │  • get_equipment_info   advanced            • compare_characters_   │    │
│  │  • suggest_team       • search_equipment_     llm                   │    │
│  │  • get_glossary         advanced            • suggest_team_llm      │    │
│  │  • get_gameplay       • search_glossary_    • ask_ollama            │    │
│  │                         term                • (+ 4 more ollama)     │    │
│  │                       • search_gameplay                             │    │
│  │                       • semantic_search                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
         ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
         │  Data Layer  │   │  RAG System  │   │LLM Assistants│
         │  (loader.py) │   │   (rag.py)   │   │              │
         │              │   │              │   │ • Gemini     │
         │ • TSV Parser │   │ • Embeddings │   │ • Ollama     │
         │ • Fuzzy Match│   │ • Vector DB  │   │              │
         │ • Indexing   │   │ • Similarity │   │              │
         └──────────────┘   └──────────────┘   └──────────────┘
                    │
                    ▼
         ┌──────────────────────────────────────────────────┐
         │                 Data Files (data/)               │
         │  • characters.tsv (185 chars)                    │
         │  • abilities.tsv, passives.tsv                   │
         │  • equipment_basic/krypt/towers.tsv (282 items)  │
         │  • glossary.txt, gameplay.txt                    │
         └──────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or: venv\Scripts\activate on Windows

# Install dependencies
pip install -e .

# For Gemini AI features (optional)
./setup_gemini.sh
export GEMINI_API_KEY='your-api-key-here'

# For Ollama local AI (optional, no API key needed)
./setup_ollama.sh
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

### Running the Server

```bash
# Start MCP server
python -m mkmchat.server

# Or test with MCP inspector
npx @modelcontextprotocol/inspector python -m mkmchat.server
```

### Usage with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "mkmchat": {
      "command": "python",
      "args": ["-m", "mkmchat.server"],
      "cwd": "/path/to/mkmchat"
    }
  }
}
```

## Available MCP Tools

### Data Retrieval Tools

| Tool | Description |
|------|-------------|
| `get_character_info` | Get character details with fuzzy name matching |
| `get_equipment_info` | Get equipment details with fuzzy name matching |
| `suggest_team` | Get team composition suggestions (returns all 185 characters for LLM reasoning) |
| `get_glossary` | Get full game terminology glossary |
| `get_gameplay` | Get full gameplay mechanics documentation |

### Search Tools

| Tool | Description |
|------|-------------|
| `search_characters_advanced` | Filter by rarity, class, tier, or keyword in abilities |
| `search_equipment_advanced` | Filter by rarity, type, tier, or keyword in effects |
| `search_glossary_term` | Search indexed glossary terms (bleed, stun, etc.) |
| `search_gameplay` | Search gameplay mechanics by topic (tag-in, equipment, etc.) |
| `semantic_search` | RAG-powered vector similarity search |
| `search_by_strategy` | Find characters + equipment for a strategy |
| `explain_mechanic` | Explain game mechanics using RAG |

### LLM-Powered Tools

| Tool | Model | Description |
|------|-------|-------------|
| `ask_assistant` | Gemini | General questions with RAG context |
| `compare_characters_llm` | Gemini | AI-powered character comparison |
| `suggest_team_llm` | Gemini | AI team building with reasoning |
| `explain_mechanic_llm` | Gemini | Detailed mechanic explanations |
| `ask_ollama` | Ollama | Local AI questions (offline) |
| `compare_characters_ollama` | Ollama | Local character comparison |
| `suggest_team_ollama` | Ollama | Local team suggestions |
| `explain_mechanic_ollama` | Ollama | Local mechanic explanations |

## Data Statistics

| Data Type | Count | Source Files |
|-----------|-------|--------------|
| Characters | 185 | `characters.tsv`, `abilities.tsv`, `passives.tsv` |
| Equipment | 282 | `equipment_basic.tsv`, `equipment_krypt.tsv`, `equipment_towers.tsv` |
| Glossary Terms | ~50 | `glossary.txt` (indexed by term) |
| Gameplay Sections | 11 | `gameplay.txt` (indexed by topic) |

## Search Features

### Fuzzy Name Matching
Handles typos and partial names:
```
"Scorpian" → finds "MK1 Scorpion", "MK11 Scorpion", etc.
"Sub Zaro" → finds "CoS Sub-Zero"
```

### Attribute-Based Search
Filter characters/equipment by attributes:
```python
# Find all Diamond S+ tier characters
search_characters_advanced(rarity="Diamond", tier="S+")

# Find all Epic Weapons with "fire" in effect
search_equipment_advanced(rarity="Epic", equip_type="Weapon", keyword="fire")
```

### Indexed Glossary
Search specific game terms instead of loading full document:
```python
search_glossary_term("bleed")  # Returns: [DEBUFFS] Deals damage over time.
search_glossary_term("stun")   # Returns: [DEBUFFS] Temporarily prevents attacking...
```

### Indexed Gameplay
Search gameplay mechanics by topic:
```python
search_gameplay("tag-in")       # Returns tag-in/tag-out mechanics
search_gameplay("equipment")    # Returns equipment slot information
search_gameplay("brutality")    # Returns brutality/friendship info
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black mkmchat tests

# Lint
ruff check mkmchat tests
```

## Project Structure

```
mkmchat/
├── data/                    # Game data files
│   ├── characters.tsv       # Character base info (name, class, rarity, tier)
│   ├── abilities.tsv        # Special attacks (SP1, SP2, SP3, X-Ray)
│   ├── passives.tsv         # Passive abilities
│   ├── equipment_basic.tsv  # Basic equipment (97 items)
│   ├── equipment_krypt.tsv  # Krypt equipment (42 items)
│   ├── equipment_towers.tsv # Tower equipment (143 items)
│   ├── glossary.txt         # Game terminology (buffs, debuffs, stats)
│   ├── gameplay.txt         # Gameplay mechanics
│   └── .rag_cache/          # RAG embeddings cache (auto-generated)
├── mkmchat/                 # Main package
│   ├── server.py            # MCP server entry point
│   ├── tools/               # MCP tool implementations
│   │   ├── character_info.py
│   │   ├── equipment_info.py
│   │   ├── team_suggest.py
│   │   ├── semantic_search.py
│   │   └── llm_tools.py
│   ├── llm/                 # LLM integrations
│   │   ├── gemini.py        # Google Gemini (gemini-2.0-flash)
│   │   └── ollama.py        # Local Ollama (dolphin-llama3:8b)
│   ├── data/                # Data loading and querying
│   │   ├── loader.py        # DataLoader with fuzzy search
│   │   └── rag.py           # RAG system with embeddings
│   └── models/              # Pydantic data models
│       ├── character.py
│       ├── equipment.py
│       └── team.py
└── tests/                   # Test suite
```

## AI Assistants

### Gemini AI (Cloud-based)
Cloud-based AI using `gemini-2.0-flash` for best quality responses.

**Setup:**
```bash
export GEMINI_API_KEY="your-api-key-here"
pip install google-generativeai
```

**Model:** `gemini-2.0-flash`

### Ollama Local AI (CPU-only)
Run AI locally without API costs using `dolphin-llama3:8b`.

**Setup:**
```bash
./setup_ollama.sh  # Installs Ollama + model
```

**Model:** `dolphin-llama3:8b` (configurable)

**Benefits:**
- ✅ Free (no API costs)
- ✅ Private (runs locally)
- ✅ Offline capable
- ✅ Fast on modern CPUs (10-20 tokens/sec)

## Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Gemini API Key | `GEMINI_API_KEY` | Required for Gemini tools |
| Ollama URL | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| Gemini Model | (code) | `gemini-2.0-flash` |
| Ollama Model | (code) | `dolphin-llama3:8b` |

## Adding Data

### Characters
Add new characters to `data/characters.tsv` (tab-separated):
```tsv
name	class	rarity	tier	synergy
New Character	Martial Artist	Diamond	S	Fire damage
```

Then add abilities to `data/abilities.tsv`:
```tsv
character	sp1	sp2	sp3	xray
New Character	Fire punch dealing damage	Fire combo attack	(optional)	(optional)
```

And passive to `data/passives.tsv`:
```tsv
character	description
New Character	Gains 20% attack boost when teammate uses fire attack.
```

### Equipment
Add equipment to `data/equipment_basic.tsv`:
```tsv
name	rarity	type	effect	max_fusion_effect	tier
New Weapon	Epic	Weapon	+20% attack boost	+50% attack boost	A
```

## Documentation

- [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - Gemini AI setup guide
- [OLLAMA_INTEGRATION.md](OLLAMA_INTEGRATION.md) - Ollama local AI setup
- [RAG_SYSTEM.md](RAG_SYSTEM.md) - RAG system documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture docs

## License

GNU GPL v3.0 - See [LICENSE](LICENSE) file for details.
