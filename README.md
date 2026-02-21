# MKMChat  Mortal Kombat Mobile Assistant

> AI-powered team builder and game assistant for **Mortal Kombat Mobile**, running entirely on your local machine.

MKMChat is a full-stack application combining a Python AI backend (RAG + local LLM via Ollama) with a Laravel web interface. It helps players build optimal teams, understand game mechanics, and get strategic advice  all privately, without sending data to external services.

---

## Features

- **185+ characters** with abilities, passives, rarity, and tier data
- **280+ equipment items** across Basic, Krypt, and Tower categories
- **AI team suggestions**  get a full 3-character roster with equipment for any strategy
- **Ask anything**  free-text Q&A about mechanics, towers, synergies, and resources
- **RAG-powered search** with tier prioritization (S+ > S > A > B > C > D)
- **Query history**  review all past team builds and answers
- **Daily query limits**  optional per-user rate limiting
- **Full web UI**  MK-themed Laravel + Livewire frontend with auth
- **Local & private**  all AI inference runs via Ollama on your machine
- **MCP server**  also works as a Model Context Protocol tool server

---

## Architecture

```
Browser / MCP Client
       
       

  Laravel 12 + Livewire 3 (webapp/, port 8000)    
        
   Team        Ask a        Query History   
   Suggest     Question     + Profile       
        
                                                  
            MkmApiService (HTTP)                   

                       POST /suggest-team
                       POST /ask-question
                      

  Python HTTP Server (mkmchat, port 8080)         
         
   RAG System        Ollama LLM Client        
   (embeddings +  (llama3.2:3b or any     
    tier boost)       local model)            
         
                                                  
      
    Knowledge Base (data/)                      
    characters, equipment, passives,            
    abilities, glossary, gameplay               
      

```

---

## Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10+ | For the AI backend |
| PHP | 8.2+ | For the Laravel webapp |
| Composer | 2.x | PHP dependency manager |
| Node.js | 18+ | Asset compilation |
| Ollama | latest | [ollama.com](https://ollama.com)  runs the LLM |

---

## Quick Start

### 1. Python Backend

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -e .

# Pull a model (llama3.2:3b is a good lightweight choice)
ollama pull llama3.2:3b

# Start the HTTP server (default: port 8080)
python -m mkmchat http
```

The server exposes two endpoints at `http://localhost:8080`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/suggest-team` | POST | Returns a 3-character team with equipment |
| `/ask-question` | POST | Answers a free-text question about MK Mobile |

### 2. Laravel Web App

```bash
cd webapp

# Install PHP dependencies
composer install

# Install Node dependencies and build assets
npm install
npm run build

# Set up environment
cp .env.example .env
php artisan key:generate

# Set up the database
php artisan migrate

# Start the web server (default: port 8000)
php artisan serve
```

Open [http://localhost:8000](http://localhost:8000) in your browser, register an account, and start using the assistant.

> **Both servers must be running at the same time.**  
> The Laravel app calls the Python server at the URL configured in `MKM_API_URL` (defaults to `http://localhost:8080`).

---

## Environment Variables

The following variables can be set in `webapp/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MKM_API_URL` | `http://localhost:8080` | URL of the Python HTTP server |
| `MKM_DAILY_LIMIT` | `0` | Max queries per user per day (0 = unlimited) |
| `DB_CONNECTION` | `sqlite` | Database driver (sqlite works out of the box) |
| `APP_URL` | `http://localhost` | Public URL of the Laravel app |

---

## HTTP API Reference

Both endpoints accept JSON and return JSON.

### `POST /suggest-team`

```bash
curl -X POST http://localhost:8080/suggest-team \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "Best team for Elder Wind Tower",
    "owned_characters": "Scorpion, Sub-Zero"
  }'
```

Response:
```json
{
  "response": {
    "strategy": "...",
    "char1": {
      "name": "Scorpion",
      "rarity": "Gold",
      "passive": "...",
      "equipment": [
        {"slot": "weapon", "name": "...", "effect": "..."},
        {"slot": "armor",  "name": "...", "effect": "..."},
        {"slot": "accessory", "name": "...", "effect": "..."}
      ]
    },
    "char2": { ... },
    "char3": { ... }
  }
}
```

### `POST /ask-question`

```bash
curl -X POST http://localhost:8080/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question": "How does X-Ray work in tower challenges?"}'
```

Response:
```json
{
  "response": "X-Ray moves deal..."
}
```

---

## Project Structure

```
mkmchat-mcp/
 mkmchat/                  # Python package  AI backend
    http_server.py        # HTTP API server (/suggest-team, /ask-question)
    server.py             # MCP server (alternative to HTTP)
    data/
       loader.py         # TSV/TXT data loader
       rag.py            # RAG system with tier boosting
    llm/
       ollama.py         # Ollama LLM integration
    models/               # Pydantic models (Character, Equipment, Team)
    tools/                # MCP / HTTP tool implementations

 data/                     # Knowledge base (TSV + TXT files)
    characters.tsv        # 185+ fighters (name, class, rarity, tier)
    passives.tsv          # Character passive abilities
    abilities.tsv         # Special attacks
    equipment_basic.tsv   # Basic equipment
    equipment_krypt.tsv   # Krypt equipment
    equipment_towers.tsv  # Tower-specific equipment
    glossary.txt          # Game terminology
    gameplay.txt          # Game mechanics guide

 webapp/                   # Laravel 12 web application
    app/
       Livewire/         # Livewire components
          TeamSuggestion.php
          AskQuestion.php
          QueryHistoryList.php
       Models/           # User, QueryHistory
       Services/
           MkmApiService.php   # HTTP client for Python backend
    resources/views/
       welcome.blade.php       # MK-themed landing page
       dashboard.blade.php     # Team Suggestion page
       ask.blade.php           # Ask a Question page
       history.blade.php       # Query history
       profile.blade.php       # User profile
       layouts/                # App and guest layouts (with footer)
       components/             # Reusable Blade components
       livewire/               # Livewire component views + partials
    database/
       migrations/       # users, query_histories tables
    config/
       mkm.php           # MKM_API_URL and MKM_DAILY_LIMIT config
    tailwind.config.js    # Custom MK color palette

 tests/                    # Python tests
 pyproject.toml            # Python package config
 setup_ollama.sh           # Ollama setup helper
```

---

## Useful Commands

```bash
# Clear RAG embedding cache (force re-index)
# Windows
Remove-Item -Recurse -Force data\.rag_cache
# Linux/Mac
rm -rf data/.rag_cache

# Clear Laravel view cache after template edits
cd webapp && php artisan view:clear

# Re-build frontend assets after CSS/JS changes
cd webapp && npm run build

# Run Python tests
pytest

# Run PHP tests
cd webapp && php artisan test
```

---

## Project Status

| Component | Status |
|-----------|--------|
| Knowledge base (185+ chars, 280+ items) |  Complete |
| RAG system with tier boosting |  Complete |
| Ollama LLM integration |  Complete |
| HTTP server (`/suggest-team`) |  Complete |
| HTTP server (`/ask-question`) |  Complete |
| MCP server (tool mode) |  Complete |
| Laravel webapp  auth (register/login) |  Complete |
| Laravel webapp  Team Suggestion UI |  Complete |
| Laravel webapp  Ask a Question UI |  Complete |
| Laravel webapp  Query History |  Complete |
| Laravel webapp  User Profile & Avatar |  Complete |
| Laravel webapp  Daily query limits |  Complete |
| MK-themed dark UI |  Complete |
| Data expansion (more characters/equipment) |  Ongoing |
| Multiple LLM backend support |  Planned |
| Team comparison / meta analysis |  Planned |

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).  
Not affiliated with Warner Bros. or NetherRealm Studios.  
Made by [@hacheipe399](https://x.com/hacheipe399).