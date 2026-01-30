# Ollama Local LLM Integration

Run AI locally without API costs using Ollama with Llama 3.2.

## Benefits

- ✅ **Free** - No API costs or rate limits
- ✅ **Private** - All processing happens locally
- ✅ **Offline** - Works without internet
- ✅ **Fast** - 10-20 tokens/sec on modern CPUs

## Requirements

- **RAM**: 6-8 GB available
- **Storage**: ~2 GB for model
- **CPU**: 4+ cores recommended

## Quick Start

```bash
# Automated setup
./setup_ollama.sh

# Or manual:
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2:3b
```

## Service Management

```bash
# Start
ollama serve

# Background
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Stop
pkill ollama

# Check status
curl http://localhost:11434/api/tags
```

## MCP Tools

All 4 Ollama tools use RAG for context-aware responses:

### ask_ollama
General questions about the game.
```json
{"question": "What's the best team for boss battles?", "use_context": true}
```

### compare_characters_ollama
Compare two characters.
```json
{"character1": "MK11 Scorpion", "character2": "MK11 Sub-Zero"}
```

### suggest_team_ollama
Get team composition suggestions.
```json
{"strategy": "fire damage", "owned_characters": ["Scorpion", "Raiden"]}
```

### explain_mechanic_ollama
Explain game mechanics.
```json
{"mechanic": "power drain"}
```

## Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Base URL | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| Model | `OLLAMA_MODEL` | `llama3.2:3b` |

## Alternative Models

```bash
# Faster but less capable
ollama pull gemma:2b

# Slower but more capable (requires 8GB+ RAM)
ollama pull llama3.2:7b
ollama pull mistral:7b
```

## Python Usage

```python
from mkmchat.llm.ollama import get_ollama_assistant

assistant = get_ollama_assistant()

if assistant.enabled:
    response = await assistant.query(
        "What's the best fire damage team?",
        use_rag=True
    )
    print(response)
```

## Troubleshooting

### Ollama not responding
```bash
# Check if running
pgrep -f ollama

# Restart
pkill ollama && ollama serve &
```

### Model not found
```bash
# List installed models
ollama list

# Pull model
ollama pull llama3.2:3b
```

### Slow responses
- Close other applications to free RAM
- Try a smaller model: `ollama pull gemma:2b`
- First query loads model (~10s), subsequent queries are faster
