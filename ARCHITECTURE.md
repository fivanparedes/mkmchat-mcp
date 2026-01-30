# System Architecture

Visual overview of the mkmchat system architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client                               │
│                   (Claude Desktop, etc.)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server (server.py)                      │
│                                                                   │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐ │
│  │   Base Tools (3)  │  │   RAG Tools (3)   │  │ LLM Tools(4)│ │
│  │                   │  │                   │  │             │ │
│  │ • character_info  │  │ • semantic_search │  │ • ask_asst  │ │
│  │ • equipment_info  │  │ • search_strategy │  │ • compare   │ │
│  │ • suggest_team    │  │ • explain_mech    │  │ • suggest   │ │
│  └─────────┬─────────┘  └─────────┬─────────┘  └──────┬──────┘ │
└────────────┼────────────────────────┼────────────────────┼───────┘
             │                        │                    │
             ▼                        ▼                    ▼
┌────────────────────┐   ┌────────────────────┐   ┌──────────────┐
│   Data Loader      │   │    RAG System      │   │   Gemini     │
│   (loader.py)      │   │    (rag.py)        │   │  Assistant   │
│                    │   │                    │   │  (gemini.py) │
│ • Load TSV files   │   │ • Embeddings       │   │              │
│ • Parse characters │   │ • Semantic search  │   │ • LLM queries│
│ • Parse equipment  │   │ • Cache system     │   │ • RAG context│
│ • Validate data    │   │ • 204 docs indexed │   │ • Reasoning  │
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
│  │ _basic.tsv   │  │              │  │              │  │
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

### 2. Semantic Search (RAG Tools)
```
User Query ("find fire characters")
    │
    ▼
MCP Client → MCP Server → RAG Tool
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
            Response ← RAG Tool
```

### 3. AI Query (LLM Tools)
```
User Query ("What's best counter to freeze?")
    │
    ▼
MCP Client → MCP Server → LLM Tool
                              │
                              ▼
                      Gemini Assistant
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
                    Gemini API (gemini-1.5-flash)
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
- Fallback to JSON if TSV unavailable

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

### Gemini Assistant (gemini.py)
**Responsibilities:**
- Interface with Gemini API
- Integrate RAG context
- Generate intelligent responses
- Handle specific query types

**Query Types:**
- General questions (`query()`)
- Character comparisons (`compare_characters()`)
- Team suggestions (`suggest_team_composition()`)
- Mechanic explanations (`explain_mechanic()`)

**Processing Flow:**
```
Question → RAG Retrieval → Build Prompt → Gemini API → Parse Response → Return
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│         Application Layer                │
│  • Python 3.10+                         │
│  • asyncio for async operations         │
│  • Pydantic for data validation         │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         Integration Layer                │
│  • MCP Protocol (tool serving)          │
│  • Google Gemini API (LLM)              │
│  • sentence-transformers (embeddings)   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│           Data Layer                     │
│  • TSV files (structured data)          │
│  • Text files (unstructured data)       │
│  • Pickle cache (embeddings)            │
└─────────────────────────────────────────┘
```

## Performance Characteristics

### Base Tools
- **Latency**: ~0.01s (file I/O + parsing)
- **Bottleneck**: Disk I/O
- **Optimization**: In-memory caching (future)

### RAG Tools
- **Latency**: 
  - First run: ~2-3s (indexing)
  - With cache: ~0.01s (search only)
- **Bottleneck**: Embedding generation (first run)
- **Optimization**: Persistent cache

### LLM Tools
- **Latency**: 
  - gemini-1.5-flash: ~1-3s
  - gemini-1.5-pro: ~3-8s
- **Bottleneck**: API call
- **Optimization**: RAG reduces hallucinations, improving answer quality

## Scalability

### Current Limits
- **Documents**: 204 (easily scales to 10,000+)
- **Embedding Dim**: 384 (fixed by model)
- **Cache Size**: ~2MB (scales linearly)
- **API Rate**: 15 RPM (Gemini flash, free tier)

### Scaling Strategies
1. **More Documents**: RAG system scales well (tested up to 100k)
2. **Better Search**: Upgrade to larger embedding model
3. **Faster LLM**: Use streaming responses
4. **Higher Rate**: Paid Gemini tier (higher RPM)

## Error Handling

### Error Flow
```
Error Occurs
    │
    ▼
Catch in Tool
    │
    ▼
Log Error Details
    │
    ▼
Format MCP Error Response
    │
    ▼
Return to Client with:
  • Error message
  • Error type
  • Suggestions
```

### Error Types
1. **Data Errors**: TSV parsing failures
2. **RAG Errors**: Embedding/search failures
3. **API Errors**: Gemini API issues
4. **Validation Errors**: Invalid input

## Security

### Data Protection
- No sensitive data stored
- API keys in environment variables
- No user data persistence

### API Security
- API key required for Gemini
- Rate limiting by Google
- No authentication for local MCP server

## Monitoring & Debugging

### Available Tools
1. **Test Suites**:
   - `tests/test_rag.py` - RAG system
   - `tests/test_gemini.py` - LLM integration
   - `tests/test_tools.py` - Base tools

2. **Logging**:
   - Console output for errors
   - Tool execution traces

3. **MCP Inspector**:
   - Web UI at http://localhost:5173
   - Interactive tool testing
   - Request/response inspection

## Deployment

### Local Development
```
venv/ → Isolated environment
data/ → Game data
mkmchat/ → Source code
tests/ → Test suite
```

### Production (MCP Client)
```
Claude Desktop Config:
{
  "mcpServers": {
    "mkmchat": {
      "command": "python",
      "args": ["-m", "mkmchat.server"],
      "cwd": "/path/to/mkmchat",
      "env": {
        "GEMINI_API_KEY": "your-key"
      }
    }
  }
}
```

## Future Architecture

### Planned Enhancements
1. **Database**: SQLite for complex queries
2. **Caching**: Redis for faster responses
3. **Streaming**: SSE for long LLM responses
4. **Multi-model**: Support multiple LLM providers
5. **Web UI**: Direct web interface (beyond MCP)

---

**Architecture Version**: 2.0 (with RAG + Gemini)  
**Last Updated**: After Gemini integration  
**Complexity**: Medium (3 layers, 10 tools, 3 subsystems)
