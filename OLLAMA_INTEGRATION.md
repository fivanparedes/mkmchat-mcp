# Ollama Local LLM Integration

This document describes the Ollama integration for running local AI models without cloud API dependencies.

## Overview

Ollama enables running large language models locally on your CPU. The integration uses **Llama 3.2 3B**, a compact but capable model optimized for CPU inference.

### Benefits
- ✅ **Privacy**: All processing happens locally
- ✅ **No API Costs**: Free to use, no rate limits
- ✅ **Offline Capable**: Works without internet
- ✅ **Fast on CPU**: 10-20 tokens/sec on modern CPUs
- ✅ **Same Features**: All Gemini features available

### Requirements
- **RAM**: 6-8 GB available
- **Storage**: ~2 GB for model
- **CPU**: Multi-core processor (4+ cores recommended)
- **OS**: Linux, macOS, or Windows (WSL)

## Quick Start

### 1. Install and Setup
```bash
# Make setup script executable
chmod +x setup_ollama.sh

# Run setup (installs Ollama, pulls model, installs deps)
./setup_ollama.sh
```

### 2. Test Integration
```bash
# Run test suite
python test_ollama.py
```

### 3. Use in MCP Server
The Ollama tools are automatically available in the MCP server:
- `ask_ollama` - General questions
- `compare_characters_ollama` - Character comparisons
- `suggest_team_ollama` - Team suggestions
- `explain_mechanic_ollama` - Mechanic explanations

## Architecture

### Components
```
mkmchat/llm/ollama.py          # OllamaAssistant class
mkmchat/tools/llm_tools.py     # MCP tool implementations
setup_ollama.sh                # Automated setup script
test_ollama.py                 # Test suite
```

### Data Flow
```
User Query
    ↓
MCP Tool (ask_ollama)
    ↓
OllamaAssistant.query()
    ↓
RAG System (optional context)
    ↓
HTTP API → Ollama Server → Llama 3.2 3B
    ↓
Response
```

## Manual Ollama Usage

### Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Start Service
```bash
# Background service
ollama serve

# Or in background
nohup ollama serve > /tmp/ollama.log 2>&1 &
```

### Pull Model
```bash
ollama pull llama3.2:3b
```

### Test Model
```bash
ollama run llama3.2:3b
>>> What is Mortal Kombat?
```

### List Models
```bash
ollama list
```

### Other Models
```bash
# Faster but less capable
ollama pull gemma:2b

# Slower but more capable
ollama pull phi3:mini
ollama pull mistral:7b
```

## Python API Usage

### Basic Query
```python
from mkmchat.llm.ollama import OllamaAssistant

assistant = OllamaAssistant()

if assistant.enabled:
    response = await assistant.query(
        "What is the best team for boss battles?",
        use_rag=True
    )
    print(response)
```

### With RAG Context
```python
from mkmchat.llm.ollama import get_ollama_assistant
from mkmchat.data.rag import RAGSystem

rag = RAGSystem()
assistant = get_ollama_assistant(rag_system=rag)

response = await assistant.query(
    "Compare Scorpion's abilities",
    use_rag=True  # Uses RAG for context
)
```

### Compare Characters
```python
response = await assistant.compare_characters(
    "Klassic Scorpion",
    "Klassic Sub-Zero"
)
```

### Team Suggestions
```python
response = await assistant.suggest_team_composition(
    strategy="aggressive damage dealer",
    owned_characters=["Scorpion", "Sub-Zero", "Raiden"]
)
```

### Explain Mechanics
```python
response = await assistant.explain_mechanic("power drain")
```

## MCP Tool Integration

The Ollama tools are registered in `mkmchat/server.py`:

```python
# Tool definitions in list_tools()
Tool(
    name="ask_ollama",
    description="Ask local Ollama AI...",
    inputSchema={...}
)

# Tool handlers in call_tool()
elif name == "ask_ollama":
    return await ask_ollama(
        question=arguments["question"],
        use_context=arguments.get("use_context", True)
    )
```

## Configuration

### Environment Variables
```bash
# Optional: Override default Ollama URL
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Change Model
```python
assistant = OllamaAssistant(
    model_name="phi3:mini"  # Use different model
)
```

### Adjust Temperature
```python
response = await assistant.query(
    question="...",
    temperature=0.5,  # Lower = more deterministic
    max_tokens=500    # Shorter responses
)
```

## Troubleshooting

### Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start if not running
ollama serve
```

### Model Not Found
```bash
# List available models
ollama list

# Pull model if missing
ollama pull llama3.2:3b
```

### Slow Performance
- Close other applications to free RAM
- Use smaller model: `ollama pull gemma:2b`
- Reduce `max_tokens` parameter
- Disable RAG: `use_rag=False`

### Connection Errors
```bash
# Check Ollama logs
tail -f /tmp/ollama.log

# Restart service
pkill ollama
ollama serve
```

### Out of Memory
```bash
# Check available RAM
free -h

# Use smaller model
ollama pull gemma:2b  # Only ~1.5 GB
```

## Performance Comparison

| Model | Size | RAM Usage | Speed (tokens/sec) | Quality |
|-------|------|-----------|-------------------|---------|
| gemma:2b | 2B | ~3 GB | 20-30 | Good |
| llama3.2:3b | 3B | ~4-6 GB | 10-20 | Excellent |
| phi3:mini | 3.8B | ~4 GB | 15-25 | Very Good |
| mistral:7b | 7B | ~8-12 GB | 5-10 | Superior |

**Recommendation**: Use `llama3.2:3b` for best balance of quality and speed on CPU.

## Gemini vs Ollama Comparison

| Feature | Gemini (Cloud) | Ollama (Local) |
|---------|---------------|----------------|
| **Cost** | Paid API | Free |
| **Speed** | Very Fast | Moderate |
| **Privacy** | Cloud-based | Fully local |
| **Quality** | Excellent | Good-Excellent |
| **Offline** | ❌ No | ✅ Yes |
| **Setup** | API key only | Install + download |
| **Resource** | None | 6-8 GB RAM |

**When to Use**:
- **Gemini**: Production, speed-critical, best quality
- **Ollama**: Development, privacy, offline, no budget

## Advanced Usage

### Custom System Prompt
```python
assistant = OllamaAssistant()
assistant.system_context = "Custom game expert prompt..."
```

### Stream Responses
```python
# Modify ollama.py to use stream=True
async with httpx.AsyncClient() as client:
    async with client.stream(
        'POST',
        f"{self.base_url}/api/generate",
        json={
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }
    ) as response:
        async for line in response.aiter_lines():
            # Process streaming chunks
            ...
```

### Multiple Models
```python
# Fast model for simple queries
fast_assistant = OllamaAssistant(model_name="gemma:2b")

# Powerful model for complex analysis
powerful_assistant = OllamaAssistant(model_name="mistral:7b")
```

## Resources

- **Ollama Docs**: https://ollama.com/
- **Llama 3.2 Model Card**: https://ollama.com/library/llama3.2
- **Model Library**: https://ollama.com/library
- **GitHub**: https://github.com/ollama/ollama

## Future Improvements

- [ ] Streaming responses for real-time output
- [ ] Model auto-selection based on query complexity
- [ ] Fine-tuning on MK Mobile-specific data
- [ ] GPU acceleration support
- [ ] Batch processing for multiple queries
- [ ] Response caching for common questions
