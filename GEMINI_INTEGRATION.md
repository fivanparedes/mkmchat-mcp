# Gemini LLM Integration

## Overview

The mkmchat project now includes Gemini AI integration, providing intelligent, conversational assistance for Mortal Kombat Mobile. The LLM combines RAG (semantic search) with Google's Gemini model for comprehensive, context-aware answers.

## Features

### 🤖 AI-Powered Tools

1. **`ask_assistant`**: General Q&A about the game
2. **`compare_characters_llm`**: Intelligent character comparisons
3. **`suggest_team_llm`**: AI-powered team building
4. **`explain_mechanic_llm`**: Detailed mechanic explanations

### 🎯 Capabilities

- **Conversational**: Natural language understanding
- **Context-Aware**: Uses RAG to ground answers in game data
- **Strategic Analysis**: Provides reasoning and recommendations
- **Comprehensive**: Combines multiple data sources

## Setup

### 1. Install Dependencies

```bash
pip install google-generativeai
```

### 2. Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy your API key

### 3. Configure Environment

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: .env File**
Create `.env` in project root:
```
GEMINI_API_KEY=your-api-key-here
```

## Usage

### Via MCP (Claude Desktop)

The AI tools are automatically available in Claude Desktop:

```
"What's the best counter to power drain teams?"
→ Uses: ask_assistant

"Compare Klassic Scorpion vs Inferno Scorpion"
→ Uses: compare_characters_llm

"Build me a team for boss battles with high damage"
→ Uses: suggest_team_llm

"Explain how fusion works and why it matters"
→ Uses: explain_mechanic_llm
```

### Direct Python Usage

```python
from mkmchat.llm.gemini import GeminiAssistant
from mkmchat.data.rag import RAGSystem

# Initialize
rag = RAGSystem()
rag.index_data()

assistant = GeminiAssistant(
    api_key="your-key",  # or use env var
    rag_system=rag
)

# Ask questions
response = await assistant.query("What's the meta for diamond characters?")
print(response)

# Compare characters
comparison = await assistant.compare_characters("Scorpion", "Sub-Zero")
print(comparison)

# Get team suggestions
team = await assistant.suggest_team_composition(
    strategy="aggressive rush down",
    owned_characters=["Scorpion", "Liu Kang", "Raiden"]
)
print(team)

# Explain mechanics
explanation = await assistant.explain_mechanic("power drain")
print(explanation)
```

### Via MCP Tools

```python
from mkmchat.tools.llm_tools import (
    ask_assistant,
    compare_characters_llm,
    suggest_team_llm,
    explain_mechanic_llm
)

# General question
response = await ask_assistant(
    question="How do I build a defensive team?",
    use_context=True
)

# Character comparison
comparison = await compare_characters_llm(
    character1="Klassic Liu Kang",
    character2="Hellspawn Scorpion"
)

# Team suggestion
team = await suggest_team_llm(
    strategy="boss killer",
    owned_characters=["Scorpion", "Sub-Zero", "Raiden"]
)

# Mechanic explanation
explanation = await explain_mechanic_llm(
    mechanic="tag-in attacks"
)
```

## Configuration

### Model Selection

Change the Gemini model in [`mkmchat/llm/gemini.py`](mkmchat/llm/gemini.py):

```python
assistant = GeminiAssistant(
    model_name="gemini-1.5-flash"  # Fast, good for most queries
    # model_name="gemini-1.5-pro"  # More powerful, slower
    # model_name="gemini-pro"      # Older model
)
```

**Model Comparison:**
| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| gemini-1.5-flash | Fast | Good | Low | General Q&A, quick lookups |
| gemini-1.5-pro | Medium | Excellent | Medium | Complex analysis, strategy |
| gemini-pro | Fast | Good | Low | Basic questions |

### Temperature Settings

Adjust creativity vs consistency:

```python
response = await assistant.query(
    question="...",
    temperature=0.7  # 0 = deterministic, 1 = creative
)
```

**Guidelines:**
- **0.0-0.3**: Factual queries (stats, mechanics)
- **0.5-0.7**: Strategic advice (team building)
- **0.8-1.0**: Creative suggestions (playstyles)

### RAG Integration

Control context usage:

```python
# With RAG context (recommended)
response = await assistant.query(question, use_rag=True)

# Without RAG (pure LLM knowledge)
response = await assistant.query(question, use_rag=False)
```

## How It Works

### Architecture

```
User Query
    ↓
RAG System → [Semantic Search] → Relevant Game Data
    ↓
Gemini LLM → [Context + Query] → Intelligent Response
    ↓
Formatted Answer
```

### Context Building

The assistant automatically:
1. **Searches RAG**: Finds relevant characters/equipment/mechanics
2. **Loads Data**: Fetches specific game information
3. **Builds Prompt**: Combines system context + RAG results + user query
4. **Generates**: Uses Gemini to synthesize an answer

### Example Flow

**Query:** "What's the best fire damage team?"

1. **RAG Search**: Finds fire-based characters (Scorpion variants, Liu Kang, etc.)
2. **Context Assembly**: Gathers abilities, passives, synergies
3. **LLM Analysis**: Gemini analyzes data and recommends team
4. **Response**: Detailed team with reasoning

## Advantages Over Rule-Based Tools

| Feature | Rule-Based (`suggest_team`) | LLM-Powered (`suggest_team_llm`) |
|---------|----------------------------|----------------------------------|
| Flexibility | Fixed logic | Adaptive reasoning |
| Explanations | Templated | Natural language |
| Complex Questions | Limited | Comprehensive |
| Strategy Depth | Basic | Advanced |
| Learning | Static | Can incorporate new patterns |

## Example Queries

### General Questions
```
"How does the power generation system work?"
"What's the difference between Gold and Diamond rarity?"
"Explain the meta for faction wars"
"How do I counter freeze teams?"
```

### Character Comparisons
```
"Compare Klassic Scorpion vs Hellspawn Scorpion for boss battles"
"Who's better for beginners: Scorpion or Sub-Zero?"
"Which Triborg variation is strongest?"
```

### Team Building
```
"Build me a tank team with crowd control"
"What's the best team for 3 Minute Towers?"
"Suggest a team using Martial Artist class synergy"
"I have Scorpion, Raiden, and Sub-Zero - what's optimal?"
```

### Mechanics
```
"Explain how resurrection works and which characters have it"
"What are the best ways to generate power quickly?"
"How does the tag-in system affect combos?"
"Explain fusion and when I should fuse characters"
```

## Cost & Limits

### Gemini API Pricing

**Free Tier:**
- 60 requests per minute
- 1,500 requests per day
- Sufficient for personal use

**Paid Tier (if needed):**
- Higher rate limits
- See: https://ai.google.dev/pricing

### Rate Limiting

The assistant doesn't implement rate limiting by default. For production:

```python
import asyncio
from datetime import datetime, timedelta

class RateLimitedAssistant(GeminiAssistant):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests = []
        self.max_per_minute = 60
    
    async def query(self, *args, **kwargs):
        # Clean old requests
        now = datetime.now()
        self.requests = [r for r in self.requests if now - r < timedelta(minutes=1)]
        
        # Check limit
        if len(self.requests) >= self.max_per_minute:
            wait = 60 - (now - self.requests[0]).seconds
            await asyncio.sleep(wait)
        
        # Make request
        self.requests.append(now)
        return await super().query(*args, **kwargs)
```

## Troubleshooting

### "Gemini assistant not available"

**Solution:** Set API key
```bash
export GEMINI_API_KEY="your-key-here"
```

### "API key invalid"

**Solutions:**
1. Verify key at https://makersuite.google.com/app/apikey
2. Check for typos or whitespace
3. Ensure key has proper permissions

### "Rate limit exceeded"

**Solutions:**
1. Wait for rate limit to reset (1 minute/1 day)
2. Implement rate limiting (see above)
3. Upgrade to paid tier

### Slow responses

**Solutions:**
1. Use `gemini-1.5-flash` instead of `pro`
2. Reduce `max_tokens` parameter
3. Disable RAG with `use_rag=False` for simple queries

### Inaccurate answers

**Solutions:**
1. Ensure RAG system is initialized and indexed
2. Use lower temperature (0.3-0.5) for factual queries
3. Phrase questions more specifically
4. Check that game data is up-to-date

## Best Practices

### 1. Use RAG for Grounding

Always enable RAG context for factual queries:
```python
response = await assistant.query(question, use_rag=True)
```

### 2. Specific Questions

❌ "Tell me about Scorpion"
✅ "What makes Klassic Scorpion good for boss battles?"

### 3. Combine Tools

Use rule-based tools for simple lookups, LLM for analysis:
```python
# Simple lookup → use exact tool
char_info = await get_character_info("Scorpion")

# Complex analysis → use LLM
comparison = await compare_characters_llm("Scorpion", "Sub-Zero")
```

### 4. Cache Results

For repeated queries, cache responses:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(question):
    return assistant.query(question)
```

## Future Enhancements

Potential improvements:
- [ ] **Function Calling**: Let LLM directly use tools
- [ ] **Conversation History**: Multi-turn conversations
- [ ] **Fine-tuning**: Train on MK Mobile data
- [ ] **Streaming**: Real-time response generation
- [ ] **Multi-modal**: Image analysis for character cards

## Security

### API Key Safety

**DO:**
✅ Use environment variables
✅ Add `.env` to `.gitignore`
✅ Use secrets management in production
✅ Rotate keys periodically

**DON'T:**
❌ Commit keys to Git
❌ Share keys publicly
❌ Hardcode keys in source

### Example .gitignore

```
.env
*.key
secrets/
GEMINI_API_KEY
```

## License

Same as mkmchat project.

## Support

- Gemini API Docs: https://ai.google.dev/docs
- Get API Key: https://makersuite.google.com/app/apikey
- Pricing: https://ai.google.dev/pricing
- Rate Limits: https://ai.google.dev/models/gemini#rate-limits
