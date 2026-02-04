# MK Mobile Assistant

AI-powered team builder for Mortal Kombat Mobile using local LLM (Ollama).

## Features

- 🎮 185+ characters with abilities and passives
- ⚔️ 280+ equipment items with effects
- 🤖 AI team suggestions via Ollama (free, local, private)
- 🔍 RAG-powered semantic search with tier prioritization (S+ > S > A > B > C > D)

## Quick Start

```bash
# Install
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .

# Setup Ollama (download from https://ollama.com)
ollama pull llama3.2:3b

# Run HTTP server
python -m mkmchat http
```

## HTTP API

```bash
curl -X POST http://localhost:8080/suggest-team \
  -H "Content-Type: application/json" \
  -d '{"strategy": "Best team for Elder Wind Tower"}'
```

Response:
```json
{
  "response": {
    "char1": {"name": "...", "passive": "...", "equipment": [...]},
    "char2": {"name": "...", "passive": "...", "equipment": [...]},
    "char3": {"name": "...", "passive": "...", "equipment": [...]},
    "strategy": "..."
  }
}
```

## Project Structure

```
mkmchat/
  http_server.py   # HTTP API server
  server.py        # MCP server
  data/
    loader.py      # TSV data loader
    rag.py         # RAG system with tier boosting
  llm/
    ollama.py      # Ollama integration
data/
  characters.tsv   # Character info (name, class, rarity, tier)
  passives.tsv     # Passive abilities
  abilities.tsv    # Special attacks
  equipment_*.tsv  # Equipment (basic, krypt, towers)
  glossary.txt     # Game terminology
  gameplay.txt     # Game mechanics
```

## Clear Cache

```bash
# Windows
Remove-Item -Recurse -Force data\.rag_cache

# Linux/Mac
rm -rf data/.rag_cache
```
