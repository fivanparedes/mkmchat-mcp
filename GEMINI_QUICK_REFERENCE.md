# Gemini LLM Quick Reference

## 🚀 Quick Start

```bash
# 1. Set API key
export GEMINI_API_KEY='your-api-key-here'

# 2. Test integration
python tests/test_gemini.py

# 3. Start MCP server
python -m mkmchat
```

## 📚 Available Tools

### 1. `ask_assistant`
**Purpose**: Ask any natural language question about MK Mobile

**Examples**:
```python
# Via Python
from mkmchat.tools.llm_tools import ask_assistant
response = await ask_assistant("What's the best counter to power drain teams?")
```

```json
// Via MCP
{
  "tool": "ask_assistant",
  "arguments": {
    "question": "What's the best counter to power drain teams?"
  }
}
```

### 2. `compare_characters_llm`
**Purpose**: Compare two characters with AI analysis

**Examples**:
```python
# Via Python
from mkmchat.tools.llm_tools import compare_characters_llm
response = await compare_characters_llm("Klassic Scorpion", "Inferno Scorpion")
```

```json
// Via MCP
{
  "tool": "compare_characters_llm",
  "arguments": {
    "character1": "Klassic Scorpion",
    "character2": "Inferno Scorpion"
  }
}
```

### 3. `suggest_team_llm`
**Purpose**: Get AI-powered team composition suggestions

**Examples**:
```python
# Via Python
from mkmchat.tools.llm_tools import suggest_team_llm
response = await suggest_team_llm(
    strategy="aggressive fire damage",
    focus_character="Hellspawn Scorpion"
)
```

```json
// Via MCP
{
  "tool": "suggest_team_llm",
  "arguments": {
    "strategy": "aggressive fire damage",
    "focus_character": "Hellspawn Scorpion"
  }
}
```

### 4. `explain_mechanic_llm`
**Purpose**: Get detailed explanations of game mechanics

**Examples**:
```python
# Via Python
from mkmchat.tools.llm_tools import explain_mechanic_llm
response = await explain_mechanic_llm("power drain")
```

```json
// Via MCP
{
  "tool": "explain_mechanic_llm",
  "arguments": {
    "mechanic": "power drain"
  }
}
```

## 🎯 Example Use Cases

### Beginner Questions
```python
await ask_assistant("What are the main character classes?")
await ask_assistant("How does the fusion system work?")
await explain_mechanic_llm("blocking")
```

### Team Building
```python
await suggest_team_llm("defensive tank team")
await suggest_team_llm("boss battle team", "Klassic Liu Kang")
await ask_assistant("What's a good synergy for Scorpion characters?")
```

### Character Analysis
```python
await compare_characters_llm("Scorpion", "Sub-Zero")
await ask_assistant("What makes Klassic Liu Kang strong?")
await ask_assistant("Best equipment for Scorpion?")
```

### Strategy & Counters
```python
await ask_assistant("How to counter freeze teams?")
await ask_assistant("Best strategy against boss battles?")
await explain_mechanic_llm("tag-in attacks")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
export GEMINI_API_KEY='your-api-key-here'

# Optional (defaults shown)
export GEMINI_MODEL='gemini-1.5-flash'
```

### Python API
```python
from mkmchat.llm.gemini import GeminiAssistant
from mkmchat.data.rag import RAGSystem

# Initialize with custom settings
rag = RAGSystem()
rag.index_data()

assistant = GeminiAssistant(
    api_key="your-key",  # or uses GEMINI_API_KEY env var
    model_name="gemini-1.5-flash",  # or gemini-1.5-pro for better quality
    rag_system=rag
)

# Ask questions
response = await assistant.query(
    question="What's the best team?",
    use_rag=True  # Use RAG context for better answers
)
```

## 🔍 RAG Integration

The Gemini assistant automatically uses RAG (Retrieval-Augmented Generation) to:
1. Search your data folder for relevant context
2. Include character/equipment/gameplay info in responses
3. Provide accurate, data-backed answers

**RAG is automatically enabled** when:
- sentence-transformers is installed
- Data has been indexed (happens on first use)
- `use_rag=True` in query (default)

## 📊 Testing

### Full Test Suite
```bash
python tests/test_gemini.py
```

### Quick Test
```python
import asyncio
from mkmchat.llm.gemini import get_gemini_assistant

async def test():
    assistant = get_gemini_assistant()
    response = await assistant.query("What classes exist?")
    print(response)

asyncio.run(test())
```

### MCP Inspector
```bash
npx @modelcontextprotocol/inspector python -m mkmchat
```

Then test tools in the web UI at http://localhost:5173

## 🐛 Troubleshooting

### API Key Issues
```bash
# Check if key is set
echo $GEMINI_API_KEY

# Set temporarily
export GEMINI_API_KEY='your-key'

# Set permanently (add to ~/.zshrc)
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### Import Errors
```bash
# Ensure google-generativeai is installed
pip install google-generativeai

# Or reinstall everything
pip install -e .
```

### Rate Limiting
If you hit rate limits:
1. Wait a few seconds between requests
2. Use `gemini-1.5-flash` (lower rate limits than Pro)
3. Upgrade your API quota at https://makersuite.google.com

### No RAG Context
If responses lack game-specific details:
```python
# Force RAG indexing
from mkmchat.data.rag import RAGSystem
rag = RAGSystem()
rag.index_data()
print(f"Indexed {len(rag.documents)} documents")
```

## 💡 Best Practices

1. **Use Specific Questions**: "What's Scorpion's passive?" vs "Tell me about Scorpion"
2. **Provide Context**: "Best team for boss battles" vs "Best team"
3. **Use Focused Characters**: Include character names for better team suggestions
4. **Check RAG**: Ensure RAG is enabled for accurate game data
5. **Batch Questions**: Ask multiple related questions in one query for better context

## 📖 More Information

- **Full Guide**: See `GEMINI_INTEGRATION.md`
- **RAG System**: See `RAG_SYSTEM.md`
- **API Docs**: https://ai.google.dev/docs
- **MCP Protocol**: https://modelcontextprotocol.io
