# RAG (Retrieval-Augmented Generation) System

## Overview

The RAG system adds intelligent semantic search capabilities to mkmchat, allowing natural language queries across all game data. Instead of exact name matching, it uses AI embeddings to find relevant information based on meaning and context.

## Features

### 🔍 Semantic Search
- **Natural Language Queries**: Search using conversational language instead of exact matches
- **Intelligent Ranking**: Results ranked by semantic similarity (0-1 score)
- **Multi-Document Types**: Search across characters, equipment, gameplay mechanics, and glossary
- **Fast Caching**: Embeddings cached for instant subsequent searches

### 🎯 Specialized Search Tools

1. **`semantic_search`**: General-purpose semantic search
   - Search any document type with natural language
   - Filter by type (character/equipment/gameplay/glossary)
   - Adjustable result count and similarity threshold

2. **`search_by_strategy`**: Strategy-focused search
   - Find characters AND equipment matching a gameplay strategy
   - Returns combined results with relevance scores
   - Perfect for team building and loadout optimization

3. **`explain_mechanic`**: Game mechanics explanation
   - Search gameplay mechanics and glossary simultaneously
   - Comprehensive answers to "how does X work?" questions
   - Contextual learning tool for new players

## Installation

### Required Dependencies

```bash
pip install sentence-transformers numpy
```

The system automatically uses the lightweight `all-MiniLM-L6-v2` model (~80MB) which provides:
- Fast inference (< 100ms per query)
- Good semantic understanding for game data
- Low memory footprint

### Optional: GPU Support

For faster embedding generation on first run:

```bash
pip install torch  # Includes CUDA support if available
```

## Usage

### Via MCP Server

The RAG tools are automatically available in the MCP server:

```python
# Using MCP client (e.g., Claude Desktop)

# Semantic search
"Find characters with fire-based attacks and high damage output"
# Uses: semantic_search tool

# Strategy search
"Show me characters and equipment for a tanky defensive playstyle"
# Uses: search_by_strategy tool

# Explain mechanics
"How does power drain work in combat?"
# Uses: explain_mechanic tool
```

### Direct Python Usage

```python
from mkmchat.data.rag import RAGSystem
from mkmchat.tools.semantic_search import semantic_search, search_by_strategy

# Initialize and index data
rag = RAGSystem()
rag.index_data()

# Semantic search
results = await semantic_search(
    query="characters with fire attacks",
    top_k=5,
    doc_type="character",
    min_similarity=0.3
)

# Strategy search
results = await search_by_strategy(
    strategy="high damage dealer",
    top_k=5
)
```

## How It Works

### 1. Document Indexing

On first run, the system:
1. Parses all TSV data files (characters, abilities, passives, equipment)
2. Creates comprehensive text documents for each entity
3. Generates embeddings using sentence-transformers
4. Caches embeddings for future use

**Example Character Document:**
```
Character: Klassic Scorpion
Class: Martial Artist
Rarity: Gold
Synergy: Increases Fire damage
Special Attack 1: Deals X% damage + fire DoT
Special Attack 2: Teleports and deals damage
Passive: Immune to fire, gains power on enemy fire attack
```

### 2. Query Processing

When a search is performed:
1. Query is converted to embedding
2. Cosine similarity calculated against all document embeddings
3. Results filtered by type and minimum similarity
4. Top-K results returned with scores

### 3. Caching Strategy

- **Hash-Based Validation**: MD5 hash of data files
- **Automatic Invalidation**: Cache rebuilds if data changes
- **Cache Location**: `data/.rag_cache/`
- **Fast Loading**: Cached embeddings load in ~100ms

## Performance

### First Run (Building Index)
- ~150 documents indexed
- ~5-10 seconds on CPU
- ~2-3 seconds with GPU
- Cache saved for future use

### Subsequent Runs
- Cache loaded in ~100ms
- Query processing: 50-100ms per search
- Total query time: < 200ms

### Memory Usage
- Model: ~250MB RAM
- Embeddings: ~10MB RAM
- Total: ~300MB additional memory

## Configuration

### Embedding Model

Change the model in `mkmchat/data/rag.py`:

```python
rag = RAGSystem(model_name="all-MiniLM-L6-v2")  # Default (fast, small)
# Or use more powerful models:
# rag = RAGSystem(model_name="all-mpnet-base-v2")  # Better accuracy, slower
```

### Cache Management

```python
# Force rebuild cache
rag.index_data(force_rebuild=True)

# Clear cache manually
import shutil
shutil.rmtree("data/.rag_cache")
```

## Examples

### Example 1: Find Characters by Ability Type

```python
query = "characters that can heal or regenerate health"
results = await semantic_search(query, doc_type="character", top_k=5)
```

**Results might include:**
- Characters with passive healing
- Characters with life drain attacks
- Characters with regeneration buffs

### Example 2: Build a Team Strategy

```python
strategy = "defensive tank with crowd control"
results = await search_by_strategy(strategy, top_k=5)
```

**Returns:**
- **Characters**: High health, defensive passives, stun/freeze abilities
- **Equipment**: Defense boosts, health regeneration, resistance gear

### Example 3: Learn Game Mechanics

```python
query = "How do I maximize damage with special attacks?"
results = await explain_mechanic(query)
```

**Returns:**
- Gameplay mechanics about special attacks
- Glossary terms for damage types, combos, power generation

## Advantages Over Traditional Search

| Feature | Traditional | RAG System |
|---------|------------|------------|
| Query Type | Exact match | Natural language |
| Typo Tolerance | ❌ | ✅ |
| Conceptual Search | ❌ | ✅ (e.g., "tank" finds defensive characters) |
| Multi-field | Complex filters | Automatic semantic matching |
| Ranking | Alphabetical | Relevance-based |
| New Player Friendly | ❌ | ✅ (understands intent) |

## Troubleshooting

### RAG system not available

```bash
pip install sentence-transformers numpy
```

### Slow first run

- Normal! Building embeddings takes 5-10s on CPU
- Subsequent runs use cache (~100ms)
- Optional: Install PyTorch with CUDA for GPU acceleration

### Cache not updating after data changes

- Cache automatically invalidates when data files change
- Manual clear: `rm -rf data/.rag_cache`

### Out of memory

- Default model uses ~300MB RAM
- Reduce batch size in `rag.py` if needed
- Use swap space or GPU memory

## Future Enhancements

- [ ] **Hybrid Search**: Combine semantic + keyword search
- [ ] **Query Expansion**: Automatically expand queries with synonyms
- [ ] **Contextual Re-ranking**: Use character synergies for better results
- [ ] **Multi-lingual Support**: Support non-English queries
- [ ] **Fine-tuned Model**: Train on MK-specific terminology

## Technical Details

### Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Architecture**: Transformer-based (6 layers)
- **Training**: Contrastive learning on semantic similarity tasks

### Similarity Metric
- **Method**: Cosine similarity
- **Range**: -1 (opposite) to 1 (identical)
- **Typical Range**: 0.3-0.8 for relevant results

### Document Structure
```python
class Document:
    content: str          # Text content for embedding
    metadata: dict        # Structured data (name, type, etc.)
    doc_type: str         # category: character/equipment/gameplay/glossary
    embedding: ndarray    # 384-dim vector
```

## Contributing

To add new data sources to RAG:

1. Add indexing method to `mkmchat/data/rag.py`:
```python
def _index_new_data(self):
    # Parse your data
    # Create Document objects
    # Append to self.documents
```

2. Call in `index_data()`:
```python
def index_data(self):
    # ... existing code ...
    self._index_new_data()
```

3. Rebuild cache with `force_rebuild=True`

## License

Same as mkmchat project license.
