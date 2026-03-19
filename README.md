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

## Current Status

- Python API + Laravel webapp running in Docker Compose
- Default LLM fallback set to `llama3.2:3b`
- Ollama container auto-pulls default model on startup
- Cross-service API key auth enabled (Laravel -> Python API)
- Rate limiting enabled in Python API and Laravel web layer
- RAG cache path and package data paths stabilized for containers
- Team suggestion, ask-question, and query history flows operational

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

### 3. Docker (recommended)

```bash
# From repo root (first time)
cp .env.docker.example .env.docker
cp webapp/.env.docker.example webapp/.env.docker
```

Set these values before first run:
- `MKM_API_KEY` and `MKM_API_KEY_HEADER` (same values in both env files)
- `OLLAMA_MODEL=llama3.2:3b` (or your preferred model)
- Keep `APP_KEY=` empty in docker env unless you intentionally provide a fixed Laravel key

Start services:

```bash
docker-compose up -d --build
```

Expected endpoints:
- Laravel webapp: `http://localhost:8000`
- Python HTTP API: `http://localhost:8080`
- Ollama API: `http://localhost:11434`

Useful checks:

```bash
docker-compose ps
docker-compose exec -T ollama ollama list
docker-compose logs -f python-api
```

Notes:
- First startup can take longer while sentence-transformer files are downloaded and RAG cache is created.
- Ollama model pull is automatic through the custom image startup script.
- If you change env files, recreate affected services (`docker-compose up -d --build --force-recreate webapp python-api`).

Stop and remove containers:

```bash
docker-compose down
```

Run Python container in MCP mode on-demand:

```bash
docker-compose run --rm python-api python -m mkmchat
```

Persistent volumes are enabled for:
- Ollama model cache
- Laravel `storage/`
- Laravel `database/` (SQLite file)

---

## Environment Variables (Docker)

Core variables used by current Docker setup:

| Variable | Example | Used by | Description |
|----------|---------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | ollama, python-api | Default model to auto-pull and use as fallback |
| `MKM_API_KEY` | `change-me-in-production` | webapp, python-api | Shared API key for Laravel -> Python requests |
| `MKM_API_KEY_HEADER` | `X-API-Key` | webapp, python-api | Header name for API key auth |
| `MKM_API_URL` | `http://python-api:8080` | webapp | Internal Docker URL for Python API |
| `MKM_DAILY_LIMIT` | `0` | webapp | Per-user daily limit (0 = unlimited) |
| `MKM_WEB_RATE_LIMIT_PER_MINUTE` | `10` | webapp | Laravel-side per-minute limiter |
| `MKM_RATE_LIMIT_PER_MINUTE` | `20` | python-api | Python API per-minute limiter |
| `MKM_RATE_LIMIT_BURST` | `5` | python-api | Python API burst limiter |
| `APP_KEY` | *(empty or base64 key)* | webapp | Laravel app key; leave empty for auto-generation on first boot |

---

## HTTP API Reference

Both endpoints accept JSON and return JSON.

When API key auth is enabled, include the configured header:
- Header: `X-API-Key`
- Value: `MKM_API_KEY`

### `POST /suggest-team`

```bash
curl -X POST http://localhost:8080/suggest-team \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me-in-production" \
  -d '{
    "strategy": "Best team for Elder Wind Tower",
    "owned_characters": ["Scorpion", "Sub-Zero"]
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
  -H "X-API-Key: change-me-in-production" \
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
       characters.tsv     # 185+ fighters (name, class, rarity, tier)
       passives.tsv       # Character passive abilities
       abilities.tsv      # Special attacks
       equipment_basic.tsv # Basic equipment
       equipment_krypt.tsv # Krypt equipment
       equipment_towers.tsv # Tower-specific equipment
       glossary.txt       # Game terminology
       gameplay.txt       # Game mechanics guide
    llm/
       ollama.py         # Ollama LLM integration
    models/               # Pydantic models (Character, Equipment, Team)
    tools/                # MCP / HTTP tool implementations

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
      mkm.php           # MKM API URL/auth/limits config
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
Remove-Item -Recurse -Force mkmchat\data\.rag_cache
# Linux/Mac
rm -rf mkmchat/data/.rag_cache

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

## Troubleshooting (Docker)

### Unauthorized from webapp to Python API

1. Ensure `MKM_API_KEY` and `MKM_API_KEY_HEADER` match in both `.env.docker` and `webapp/.env.docker`.
2. Recreate containers after env changes:

```bash
docker-compose up -d --build --force-recreate webapp python-api
```

3. Verify runtime values:

```bash
docker-compose exec -T webapp sh -lc 'printenv | grep -E "^MKM_API_KEY=|^MKM_API_KEY_HEADER=|^MKM_API_URL="'
docker-compose exec -T python-api sh -lc 'printenv | grep -E "^MKM_API_KEY=|^MKM_API_KEY_HEADER="'
```

### Slow first response after restart

- Normal on cold start while embeddings/model artifacts are initialized.
- Keep containers running for better response times (`OLLAMA_KEEP_ALIVE=15m` is already configured).

---

## Roadmap Snapshot

| Area | Status |
|------|--------|
| Core data + RAG + team/ask endpoints | Stable |
| Dockerized full stack (webapp + api + ollama) | Stable |
| Security baseline (auth, route protection, rate limits) | Implemented |
| Model management/admin UX | Implemented |
| Data expansion (new characters/equipment updates) | Ongoing |
| Additional LLM backend providers | Planned |

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).  
Not affiliated with Warner Bros. or NetherRealm Studios.  
Made by [@hacheipe399](https://x.com/hacheipe399).