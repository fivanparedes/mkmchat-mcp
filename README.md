# MKMChat (Mortal Kombat Mobile Assistant)

Local-first AI assistant for Mortal Kombat Mobile.

MKMChat combines:
- a Python backend (RAG + Ollama),
- an HTTP API + MCP server,
- a Laravel + Livewire web app.

All inference runs locally through Ollama.

## Main features

- Team suggestions with character + equipment recommendations
- Free-text Q&A about mechanics, strategy, and game systems
- Explain Mechanic flow (definition + practical recommendations)
- RAG retrieval over bundled MKM knowledge files
- Query history in the web app
- MCP-compatible tool server mode

## Architecture

- `mkmchat/`: Python package (HTTP API + MCP + RAG + LLM integration)
- `webapp/`: Laravel web UI that calls the Python API through `MkmApiService`
- `docker-compose.yml`: full local stack (`ollama`, `python-api`, `webapp`)

## Run with Docker (recommended)

### 1) Prepare environment files

From project root:

```bash
cp .env.docker.example .env.docker
cp webapp/.env.docker.example webapp/.env.docker
```

### 2) Set required values

At minimum, ensure these match where required:

- `MKM_API_KEY` (same strong random value in `.env.docker` and `webapp/.env.docker`; do not use placeholders)
- `MKM_API_KEY_HEADER` (same value in both files)
- `OLLAMA_MODEL` (for example `llama3.2:3b`)
- `APP_ENV` / `APP_DEBUG` (`production` + `false` for safest default)

### 3) Start the stack

```bash
docker compose up -d --build
```

### 4) Endpoints

- Web app: `http://localhost:8000`
- Ollama: `http://localhost:11434`

Security default: the Python API is internal-only inside the Docker network and is not published to the host.

### 5) Useful commands

```bash
docker compose ps
docker compose logs -f python-api
docker compose logs -f webapp
docker compose logs -f ollama
```

Stop everything:

```bash
docker compose down
```

## Run without Docker

### Python API

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -e .
ollama pull llama3.2:3b
python -m mkmchat http
```

### Laravel web app

```bash
cd webapp
cp .env.example .env
composer install
npm install
npm run build
php artisan key:generate
php artisan migrate
php artisan serve
```

## Environment variables

### Root Docker env (`.env.docker`)

These are documented in `.env.docker.example`.

Core runtime/auth:
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `MKM_HTTP_HOST`
- `MKM_API_KEY`
- `MKM_API_KEY_HEADER`
- `MKM_CORS_ORIGINS`

Python API limits:
- `MKM_MAX_REQUEST_SIZE`
- `MKM_MAX_STRATEGY_LENGTH`
- `MKM_MAX_QUESTION_LENGTH`
- `MKM_MAX_MECHANIC_LENGTH` (optional override)
- `MKM_RATE_LIMIT_ENABLED`
- `MKM_RATE_LIMIT_PER_MINUTE`
- `MKM_RATE_LIMIT_BURST`
- `MKM_RATE_LIMIT_BURST_WINDOW_SECONDS`
- `MKM_HTTP_TIMEOUT_SECONDS`
- `MKM_DEBUG_PROMPTS` (`false` by default; when `true`, prompt debug logs are written with basic redaction)

Explain Mechanic tuning (new):
- `MKM_MECHANIC_RAG_TOP_K`
- `MKM_MECHANIC_RAG_MAX_PASSAGES`
- `MKM_MECHANIC_RAG_MAX_CHARS`
- `MKM_MECHANIC_NUM_PREDICT`

Ollama process tuning:
- `OLLAMA_KEEP_ALIVE`
- `OLLAMA_MAX_LOADED_MODELS`
- `OLLAMA_NUM_PARALLEL`

Laravel-side values (also present in root env for compose interpolation):
- `APP_ENV`, `APP_DEBUG`, `APP_URL`, `DB_CONNECTION`, `APP_KEY`
- `MKM_API_URL`
- `MKM_DAILY_LIMIT`
- `MKM_WEB_RATE_LIMIT_PER_MINUTE`
- `MKM_HTTP_TIMEOUT_SECONDS`

### Webapp env examples

- `webapp/.env.example` is for non-Docker Laravel usage.
- `webapp/.env.docker.example` is for container runtime.

Both now include:
- `MKM_API_URL`
- `MKM_API_KEY`
- `MKM_API_KEY_HEADER`
- `MKM_HTTP_TIMEOUT_SECONDS`
- `MKM_DAILY_LIMIT`
- `MKM_WEB_RATE_LIMIT_PER_MINUTE`

## Quick API smoke test (secure default)

```bash
docker compose exec webapp curl -X POST http://python-api:8080/explain-mechanic \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-strong-api-key>" \
  -d '{"mechanic":"power drain","model":"llama3.2:3b"}'
```

If you explicitly need host access to the Python API for debugging, add a temporary port mapping to `python-api` in `docker-compose.yml`, then remove it after testing.

## Health endpoint note

`/health` is protected by API key auth. Query it from inside the Docker network, for example:

```bash
docker compose exec webapp curl http://python-api:8080/health \
  -H "X-API-Key: <your-strong-api-key>"
```

## License

GNU GPL v3. See `LICENSE`.
