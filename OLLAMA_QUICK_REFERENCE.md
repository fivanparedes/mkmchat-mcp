# Ollama Quick Reference

## Installation & Setup

```bash
# One-line setup
./setup_ollama.sh

# Manual setup
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2:3b
pip install httpx
```

## Service Management

```bash
# Start Ollama
ollama serve

# Background mode
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Stop Ollama
pkill ollama

# Check status
curl http://localhost:11434/api/tags
```

## Model Management

```bash
# List models
ollama list

# Pull new model
ollama pull llama3.2:3b

# Remove model
ollama rm llama3.2:3b

# Interactive chat
ollama run llama3.2:3b
```

## MCP Tools

### ask_ollama
Ask general questions about the game.

```json
{
  "name": "ask_ollama",
  "arguments": {
    "question": "What is the best strategy for boss battles?",
    "use_context": true
  }
}
```

### compare_characters_ollama
Compare two characters with AI analysis.

```json
{
  "name": "compare_characters_ollama",
  "arguments": {
    "character1": "Scorpion",
    "character2": "Sub-Zero"
  }
}
```

### suggest_team_ollama
Get team composition suggestions.

```json
{
  "name": "suggest_team_ollama",
  "arguments": {
    "strategy": "aggressive damage dealer",
    "owned_characters": ["Scorpion", "Raiden", "Liu Kang"]
  }
}
```

### explain_mechanic_ollama
Explain game mechanics in detail.

```json
{
  "name": "explain_mechanic_ollama",
  "arguments": {
    "mechanic": "power drain"
  }
}
```

## Python API

```python
from mkmchat.llm.ollama import OllamaAssistant, get_ollama_assistant
from mkmchat.data.rag import RAGSystem

# Basic usage
assistant = OllamaAssistant()
response = await assistant.query("What is Mortal Kombat Mobile?")

# With RAG
rag = RAGSystem()
assistant = get_ollama_assistant(rag_system=rag)
response = await assistant.query("Tell me about Scorpion", use_rag=True)

# Character comparison
response = await assistant.compare_characters("Scorpion", "Sub-Zero")

# Team suggestion
response = await assistant.suggest_team_composition(
    strategy="high damage",
    owned_characters=["Scorpion", "Raiden"]
)

# Explain mechanic
response = await assistant.explain_mechanic("power drain")
```

## Configuration

```python
# Change model
assistant = OllamaAssistant(model_name="phi3:mini")

# Custom URL
assistant = OllamaAssistant(base_url="http://192.168.1.100:11434")

# Adjust generation params
response = await assistant.query(
    question="...",
    temperature=0.5,  # 0-1 (lower = more deterministic)
    max_tokens=500    # Limit response length
)
```

## Recommended Models

| Model | Command | Size | Use Case |
|-------|---------|------|----------|
| Llama 3.2 3B | `ollama pull llama3.2:3b` | ~2 GB | **Recommended** - Best balance |
| Gemma 2B | `ollama pull gemma:2b` | ~1.5 GB | Fastest, good quality |
| Phi-3 Mini | `ollama pull phi3:mini` | ~2.3 GB | Very efficient |
| Mistral 7B | `ollama pull mistral:7b` | ~4.1 GB | Best quality (slower) |

## Troubleshooting

### Connection Failed
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart service
pkill ollama
ollama serve
```

### Model Not Found
```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.2:3b
```

### Slow Performance
- Close other applications
- Use smaller model: `ollama pull gemma:2b`
- Disable RAG: `use_rag=False`
- Reduce `max_tokens`

### Out of Memory
```bash
# Check RAM
free -h

# Use 2B model instead of 3B
ollama pull gemma:2b
```

## Testing

```bash
# Run test suite
python test_ollama.py

# Test MCP server
python -m mkmchat.server
# Then use MCP inspector or client to test tools
```

## Environment Variables

```bash
# Override Ollama URL (optional)
export OLLAMA_BASE_URL="http://localhost:11434"
```

## Performance Tips

1. **First query is slow**: Model loads into memory (~10s)
2. **Subsequent queries are fast**: Model stays in memory
3. **Keep Ollama running**: Avoid restart overhead
4. **Use appropriate model**: Bigger ≠ always better for simple tasks
5. **Limit context**: Use `top_k` parameter in RAG search

## Comparison: Gemini vs Ollama

| Feature | Gemini | Ollama |
|---------|--------|--------|
| Cost | API charges | Free |
| Speed | Very fast | Moderate |
| Privacy | Cloud | Local |
| Offline | No | Yes |
| Setup | API key | Install + model |
| Quality | Excellent | Good-Very Good |

## Resources

- Ollama Website: https://ollama.com
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- Full Docs: See `OLLAMA_INTEGRATION.md`
