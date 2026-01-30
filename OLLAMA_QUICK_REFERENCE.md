# Ollama Quick Reference

## Commands

```bash
# Service
ollama serve              # Start server
ollama serve &            # Background
pkill ollama              # Stop

# Models
ollama list               # List installed
ollama pull llama3.2:3b   # Download model
ollama rm llama3.2:3b     # Remove model
ollama run llama3.2:3b    # Interactive chat

# Status
curl http://localhost:11434/api/tags
```

## MCP Tool Examples

### ask_ollama
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
```json
{
  "name": "compare_characters_ollama",
  "arguments": {
    "character1": "MK11 Scorpion",
    "character2": "Klassic Scorpion"
  }
}
```

### suggest_team_ollama
```json
{
  "name": "suggest_team_ollama",
  "arguments": {
    "strategy": "high damage dealer",
    "owned_characters": ["Scorpion", "Raiden", "Liu Kang"]
  }
}
```

### explain_mechanic_ollama
```json
{
  "name": "explain_mechanic_ollama",
  "arguments": {
    "mechanic": "power drain"
  }
}
```

## Environment Variables

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:3b"
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Connection refused | Start Ollama: `ollama serve &` |
| Model not found | Pull model: `ollama pull llama3.2:3b` |
| Slow response | First query loads model, wait ~10s |
| Out of memory | Try smaller model: `gemma:2b` |
