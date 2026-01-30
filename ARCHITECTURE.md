# System Architecture

Visual overview of the mkmchat system architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client                               │
│                   (Claude Desktop, VS Code, etc.)                │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server (server.py)                      │
│                                                                   │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐ │
│  │   Base Tools (3)  │  │  Search Tools (3) │  │ LLM Tools(4)│ │
│  │                   │  │                   │  │  (Ollama)   │ │
│  │ • character_info  │  │ • semantic_search │  │ • ask_ollama│ │
│  │ • equipment_info  │  │ • search_chars_   │  │ • compare_  │ │
│  │ • suggest_team    │  │   advanced        │  │   ollama    │ │
│  │                   │  │ • search_equip_   │  │ • suggest_  │ │
│  │                   │  │   advanced        │  │   ollama    │ │
│  │                   │  │                   │  │ • explain_  │ │
│  │                   │  │                   │  │   ollama    │ │
│  └─────────┬─────────┘  └─────────┬─────────┘  └──────┬──────┘ │
└────────────┼────────────────────────┼────────────────────┼───────┘
             │                        │                    │
             ▼                        ▼                    ▼
┌────────────────────┐   ┌────────────────────┐   ┌──────────────┐
│   Data Loader      │   │    RAG System      │   │   Ollama     │
│   (loader.py)      │   │    (rag.py)        │   │  Assistant   │
│                    │   │                    │   │  (ollama.py) │
│ • Load TSV files   │   │ • Embeddings       │   │              │
│ • Parse characters │   │ • Semantic search  │   │ • LLM queries│
│ • Parse equipment  │   │ • Cache system     │   │ • RAG context│
│ • Validate data    │   │ • Doc indexing     │   │ • Local AI   │
└─────────┬──────────┘   └──────────┬─────────┘   └───────┬──────┘
          │                         │                      │
          │                         │         ┌────────────┘
          │                         │         │
          ▼                         ▼         ▼
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ characters   │  │ abilities    │  │ passives     │  │
│  │ .tsv         │  │ .tsv         │  │ .tsv         │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ equipment    │  │ gameplay.txt │  │ glossary.txt │  │
│  │ _*.tsv       │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           .rag_cache/ (embeddings)               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Simple Query (Base Tools)
```
User Query
    │
    ▼
MCP Client → MCP Server → Base Tool → Data Loader → TSV Files
                                              │
                                              ▼
                                        Parse & Return
                                              │
                                              ▼
                  Response ← Tool ← Data Loader
```

### 2. Semantic Search (Search Tools)
```
User Query ("find fire characters")
    │
    ▼
MCP Client → MCP Server → Search Tool
                              │
                              ▼
                         RAG System
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            Check Cache          Embeddings
                    │                   │
            ┌───────┴───────┐          │
            │ Cache Hit?    │          │
            └───┬───────┬───┘          │
                │Yes    │No            │
                │       └──────────────┘
                │              │
                ▼              ▼
         Load Cache    Generate Embeddings
                │              │
                └──────┬───────┘
                       ▼
                Semantic Search (Cosine Similarity)
                       │
                       ▼
                 Top K Results (e.g., k=5)
                       │
                       ▼
                 Format Response
                       │
                       ▼
            Response ← Search Tool
```

### 3. AI Query (LLM Tools)
```
User Query ("What's best counter to freeze?")
    │
    ▼
MCP Client → MCP Server → LLM Tool
                              │
                              ▼
                      Ollama Assistant
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              RAG Context         System Prompt
                    │                   │
                    ▼                   │
            Search for relevant         │
            characters/mechanics        │
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    Ollama API (llama3.2:3b)
                              │
                              ▼
                    AI-Generated Response
                    (with game data context)
                              │
                              ▼
                      Format Response
                              │
                              ▼
                Response ← LLM Tool
```

## Component Details

### MCP Server (server.py)
**Responsibilities:**
- Register and expose 10 MCP tools
- Route requests to appropriate handlers
- Validate input/output formats
- Handle errors gracefully

**Key Functions:**
- `list_tools()` - Return available tools
- `call_tool()` - Route to tool implementation

### Data Loader (loader.py)
**Responsibilities:**
- Load TSV files from data/ directory
- Parse character, ability, passive data
- Validate data integrity
- Provide fuzzy name matching

**Data Flow:**
```
TSV Files → Parse → Validate → Pydantic Models → Return
```

### RAG System (rag.py)
**Responsibilities:**
- Index all game data into embeddings
- Perform semantic search
- Manage embedding cache
- Return ranked results

**Components:**
- `Document` class - Represents searchable content
- `RAGSystem` class - Core search engine
- Cache system - Persistent embeddings storage

**Search Pipeline:**
```
Query → Embed → Compare with Docs → Rank by Similarity → Filter → Return
```

### Ollama Assistant (ollama.py)
**Responsibilities:**
- Interface with local Ollama API
- Integrate RAG context
- Generate intelligent responses
- Handle specific query types

**Query Types:**
- General questions (`query()`)
- Character comparisons (`compare_characters()`)
- Team suggestions (`suggest_team_composition()`)
- Mechanic explanations (`explain_mechanic()`)

**Benefits:**
- 🆓 Free (no API costs)
- 🔒 Private (runs locally)
- 📴 Offline capable
- ⚡ Fast on modern CPUs

## Project Structure

```
mkmchat/
├── __init__.py
├── __main__.py
├── server.py              # MCP server (10 tools)
├── data/
│   ├── __init__.py
│   ├── loader.py          # Data loading utilities
│   └── rag.py             # RAG/embedding system
├── llm/
│   ├── __init__.py
│   └── ollama.py          # Ollama client (local AI)
├── models/
│   ├── __init__.py
│   ├── character.py
│   ├── equipment.py
│   └── team.py
└── tools/
    ├── __init__.py        # Clean exports
    ├── character_info.py  # get_character_info
    ├── equipment_info.py  # get_equipment_info
    ├── team_suggest.py    # suggest_team
    ├── semantic_search.py # semantic_search, search_*_advanced
    └── llm_tools.py       # 4 Ollama functions
```

## Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Ollama URL | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| Ollama Model | `OLLAMA_MODEL` | `llama3.2:3b` |

## Performance

- **RAG Indexing**: ~2-3s for all documents
- **Cache Load**: ~0.1s
- **Semantic Search**: ~0.01s per query
- **Ollama Response**: 10-20 tokens/sec on modern CPU
