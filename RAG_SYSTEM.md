# RAG System

Retrieval-Augmented Generation for intelligent semantic search across MK Mobile game data.

## Features

- **Semantic Search**: Natural language queries instead of exact matches
- **Intelligent Ranking**: Results ranked by similarity score (0-1)
- **Multi-Type Search**: Characters, equipment, gameplay, glossary
- **Fast Caching**: Embeddings cached for instant subsequent searches

## Installation

```bash
pip install sentence-transformers numpy
```

Model: `all-MiniLM-L6-v2` (~80MB, <100ms per query)

## MCP Tool: semantic_search

Search across all indexed game data.

**Parameters:**
- `query` (required): Natural language search query
- `top_k` (optional): Number of results (default: 5)
- `doc_type` (optional): Filter by type
- `min_similarity` (optional): Minimum score 0-1 (default: 0.3)

**Document Types:**
- `character` - Characters with abilities and passives
- `equipment` - Weapons, armor, accessories
- `gameplay` - Game mechanics
- `glossary` - Terminology (buffs, debuffs, stats)

**Examples:**
```python
# Find fire characters
semantic_search(query="characters with fire attacks", doc_type="character")

# Find critical hit equipment
semantic_search(query="equipment that boosts critical hit", doc_type="equipment")

# Search glossary
semantic_search(query="what is bleed damage", doc_type="glossary")
```

## Python Usage

```python
from mkmchat.data.rag import RAGSystem

# Initialize
rag = RAGSystem()
rag.index_data()  # Indexes all TSV/TXT files

# Search
results = rag.search("fire damage characters", top_k=5, doc_type="character")

for doc, score in results:
    print(f"{doc.metadata['name']}: {score:.2f}")
```

## Data Indexed

| Source | Documents | Content |
|--------|-----------|---------|
| characters.tsv | 185 | Name, class, rarity, synergy |
| abilities.tsv | 185 | SP1, SP2, SP3, X-Ray attacks |
| passives.tsv | 185 | Passive ability descriptions |
| equipment_*.tsv | 280+ | Name, type, effect, fusion effect |
| gameplay.txt | ~11 | Game mechanics sections |
| glossary.txt | ~50 | Term definitions |

## Cache

Embeddings are cached in `data/.rag_cache/`:
- `embeddings.pkl` - Serialized document embeddings
- `data_hash.txt` - Hash for cache validation

Cache is automatically invalidated when data files change.

## Performance

| Operation | Time |
|-----------|------|
| First index | ~30-60s |
| Cache load | ~100ms |
| Search query | ~50-100ms |
