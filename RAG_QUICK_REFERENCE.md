# RAG Tools Quick Reference

## Overview

Three MCP tools for intelligent semantic search across MK Mobile game data.

## Tools

### 1. `semantic_search` - General Search

**Use when:** You want to explore data with natural language queries

**Parameters:**
- `query` (required): Natural language search query
- `top_k` (optional): Number of results (default: 5)
- `doc_type` (optional): Filter by type: `character`, `equipment`, `gameplay`, `glossary`
- `min_similarity` (optional): Minimum score 0-1 (default: 0.3)

**Example Queries:**
```
"characters with fire attacks and high damage"
"equipment that boosts critical hit chance"
"defensive characters with stun abilities"
"what is power generation?"
```

**Response Format:**
```json
[
  {
    "content": "Character: Scorpion\nClass: Martial Artist...",
    "type": "character",
    "metadata": {"name": "Scorpion", "class": "Martial Artist"},
    "similarity_score": 0.624
  }
]
```

---

### 2. `search_by_strategy` - Strategy-Focused Search

**Use when:** You want characters AND equipment matching a gameplay strategy

**Parameters:**
- `strategy` (required): Strategy description
- `top_k` (optional): Results per category (default: 5)

**Example Strategies:**
```
"high damage dealer"
"defensive tank"
"support healer"
"crowd control specialist"
"boss battle team"
"balanced all-rounder"
```

**Response Format:**
```json
{
  "strategy": "high damage dealer",
  "characters": [
    {
      "name": "Heavy Weapons Jax Briggs",
      "class": "Spec Ops",
      "rarity": "Gold",
      "content": "...",
      "relevance_score": 0.474
    }
  ],
  "equipment": [
    {
      "name": "Brawler Gloves",
      "type": "Accessory",
      "content": "...",
      "relevance_score": 0.389
    }
  ]
}
```

---

### 3. `explain_mechanic` - Game Mechanics Explanation

**Use when:** You need to understand game mechanics or terminology

**Parameters:**
- `mechanic_query` (required): Question about mechanics or terms

**Example Queries:**
```
"How does power drain work?"
"What is a brutality?"
"Explain tag-in mechanics"
"How do combo enders work?"
"What are damage over time effects?"
```

**Response Format:**
```json
{
  "query": "How does power drain work?",
  "gameplay_mechanics": [
    {
      "content": "Power drain reduces opponent's power bar...",
      "relevance_score": 0.356
    }
  ],
  "glossary_terms": [
    {
      "content": "Power Drain: Status effect that...",
      "relevance_score": 0.319
    }
  ]
}
```

---

## Usage Tips

### Best Practices

1. **Be Descriptive:** More detail = better results
   - ❌ "fire character"
   - ✅ "character with fire-based special attacks and high damage"

2. **Use Strategy Search for Team Building:**
   - Gets both characters and equipment in one query
   - Perfect for assembling teams

3. **Adjust `top_k` Based on Needs:**
   - 3-5: Quick focused results
   - 10+: Comprehensive exploration

4. **Filter by Type for Precision:**
   - Use `doc_type="character"` to search only characters
   - Speeds up search and improves relevance

5. **Lower `min_similarity` for Broad Exploration:**
   - Default 0.3: Good balance
   - 0.5+: Very strict, high precision
   - 0.2: More exploratory, may include noise

### Common Workflows

#### Workflow 1: Character Discovery
```
1. semantic_search("characters with poison abilities", top_k=5, doc_type="character")
2. Review results with similarity scores
3. get_character_info("Klassic Reptile")  # Deep dive on specific character
```

#### Workflow 2: Team Strategy
```
1. search_by_strategy("aggressive damage team")
2. Get character + equipment suggestions
3. suggest_team(strategy="high damage", owned_characters=[...])
```

#### Workflow 3: Learning
```
1. explain_mechanic("How does fire damage work?")
2. semantic_search("fire damage", doc_type="glossary")
3. semantic_search("fire attacks", doc_type="character")
```

---

## Query Examples by Category

### Character Searches
```
"characters that heal themselves"
"martial artist class with stun abilities"
"diamond rarity netherrealm characters"
"characters immune to bleed"
"support characters for team buffs"
```

### Equipment Searches
```
"weapon that increases attack speed"
"armor with health regeneration"
"accessory that boosts power generation"
"equipment for critical hit builds"
"defensive gear with resistance"
```

### Strategy Searches
```
"glass cannon high risk high reward"
"safe defensive slow but steady"
"rush down aggressive playstyle"
"counter-attack reactive defense"
"sustain and outlast endurance team"
```

### Mechanic Questions
```
"What is the difference between stun and freeze?"
"How do tag-in attacks work?"
"Explain fusion mechanics"
"What are fatal blows?"
"How does regeneration stack?"
```

---

## Performance Notes

- **First query:** 5-10 seconds (builds index, then cached)
- **Subsequent queries:** <200ms
- **Cache location:** `data/.rag_cache/`
- **Auto-refresh:** Cache updates when data files change

---

## Troubleshooting

### "RAG system not available"
**Solution:** Install dependencies
```bash
pip install sentence-transformers
```

### No results found
**Solutions:**
- Lower `min_similarity` (try 0.2)
- Rephrase query with different terms
- Remove `doc_type` filter
- Increase `top_k`

### Slow first query
**Expected:** Building embeddings takes time
**Solution:** Be patient, subsequent queries are fast

### Results not relevant
**Solutions:**
- Be more specific in query
- Add context: "character with X that does Y"
- Use `search_by_strategy` for team building queries
- Increase `min_similarity` for stricter matching

---

## Integration with LLMs

When using with Claude or other LLMs via MCP:

**Natural Language Prompts:**
```
"Find me fire damage characters"
→ Calls semantic_search tool

"I need a defensive team"
→ Calls search_by_strategy tool

"How does stunning work?"
→ Calls explain_mechanic tool
```

The tools are designed to work seamlessly with LLM tool calling - just use natural language!

---

## Comparison with Other Tools

| Tool | Use Case | Speed | Precision |
|------|----------|-------|-----------|
| `semantic_search` | Exploration, discovery | Fast | Good |
| `get_character_info` | Known character lookup | Instant | Exact |
| `search_by_strategy` | Team building | Fast | Good |
| `suggest_team` | Full team assembly | Instant | Rule-based |
| `explain_mechanic` | Learning, education | Fast | Good |

**Recommendation:** Use semantic tools for discovery, then exact tools for details.

---

## Advanced Usage

### Combining Tools

```python
# 1. Discover characters
results = semantic_search("fire damage", doc_type="character", top_k=10)

# 2. Extract character names
char_names = [r['metadata']['name'] for r in results]

# 3. Build team with discovered characters
team = suggest_team(
    strategy="high damage",
    owned_characters=char_names,
    required_character="Scorpion"
)
```

### Iterative Refinement

```python
# Start broad
results1 = semantic_search("damage character", top_k=20, min_similarity=0.2)

# Refine based on results
results2 = semantic_search("fire damage martial artist", top_k=5, min_similarity=0.4)

# Get specific info
char_info = get_character_info("Klassic Liu Kang")
```

---

## Quick Start

**Test the system:**
```bash
source venv/bin/activate
python tests/test_rag.py
```

**Use in MCP:**
```
Add to Claude Desktop config and ask:
"Find characters with freeze abilities"
"Build me a tank team"
"What does power drain do?"
```

**Direct Python:**
```python
from mkmchat.tools.semantic_search import semantic_search
import asyncio

results = asyncio.run(semantic_search("fire characters", top_k=5))
print(results)
```

---

That's it! The RAG tools make exploring MK Mobile data intuitive and powerful. 🎮🔥
