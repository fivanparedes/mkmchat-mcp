# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Clients                              │
│                (Claude Desktop, VS Code, Custom Apps)            │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server (server.py)                      │
│                                                                  │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │  Data Tools (3)   │  │ Search Tools (3)  │  │ LLM Tools(4)│  │
│  │                   │  │                   │  │  (Ollama)   │  │
│  │ • character_info  │  │ • semantic_search │  │ • ask       │  │
│  │ • equipment_info  │  │ • search_chars_   │  │ • compare   │  │
│  │ • suggest_team    │  │   advanced        │  │ • suggest   │  │
│  │                   │  │ • search_equip_   │  │ • explain   │  │
│  │                   │  │   advanced        │  │             │  │
│  └─────────┬─────────┘  └─────────┬─────────┘  └──────┬──────┘  │
└────────────┼────────────────────────┼────────────────────┼───────┘
             │                        │                    │
             ▼                        ▼                    ▼
┌────────────────────┐   ┌────────────────────┐   ┌──────────────┐
│   Data Loader      │   │    RAG System      │   │   Ollama     │
│   (loader.py)      │   │    (rag.py)        │   │  Assistant   │
│                    │   │                    │   │              │
│ • Load TSV files   │   │ • Embeddings       │   │ • LLM queries│
│ • Fuzzy matching   │   │ • Semantic search  │   │ • RAG context│
│ • Parse data       │   │ • Cache system     │   │ • Local AI   │
└─────────┬──────────┘   └──────────┬─────────┘   └──────────────┘
          │                         │
          ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│                                                                  │
│  characters.tsv │ abilities.tsv │ passives.tsv │ equipment*.tsv │
│  glossary.txt   │ gameplay.txt  │ .rag_cache/  (embeddings)     │
└─────────────────────────────────────────────────────────────────┘
```

## HTTP API Server

```
┌─────────────────────────────────────────────────────────────────┐
│                       HTTP Clients                               │
│               (Web Apps, Mobile Apps, CLI tools)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /suggest-team
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HTTP Server (http_server.py)                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  /suggest-team endpoint                    │  │
│  │                                                            │  │
│  │  1. Parse JSON request (strategy, owned_characters)       │  │
│  │  2. Build structured context from RAG                     │  │
│  │  3. Send prompt to Ollama with low temperature (0.1)      │  │
│  │  4. Parse and return JSON response                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌────────────┐    ┌────────────┐    ┌──────────────┐
   │ RAG System │    │   Ollama   │    │ JSON Response│
   │            │    │ (LLM API)  │    │              │
   │ Characters │    │            │    │ char1/2/3   │
   │ Equipment  │    │ llama3.2:3b│    │ equipment[] │
   │ by type    │    │            │    │ strategy    │
   └────────────┘    └────────────┘    └──────────────┘
```

## Data Flow

### MCP Query Flow
```
User Query → MCP Client → MCP Server → Tool Handler
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
         Data Loader                  RAG System                   Ollama LLM
         (direct lookup)              (semantic search)            (AI response)
              │                            │                            │
              └────────────────────────────┼────────────────────────────┘
                                           ▼
                                    Response to Client
```

### HTTP API Flow
```
HTTP POST /suggest-team
    │
    ▼
Parse Request Body
    │
    ▼
Build Structured Context ──────┐
    │                          │
    │         ┌────────────────┘
    │         ▼
    │    RAG Search:
    │    • Characters (top 8)
    │    • Weapons (top 6)
    │    • Armor (top 6)
    │    • Accessories (top 8)
    │         │
    ▼         ▼
Create Prompt with Context
    │
    ▼
Send to Ollama (temp=0.1)
    │
    ▼
Parse JSON Response
    │
    ▼
Return Structured Team JSON
```

## Component Details

### MCP Server (`server.py`)
- Registers 10 MCP tools
- Handles tool calls from MCP clients
- Routes to appropriate handlers

### HTTP Server (`http_server.py`)
- Single endpoint: POST `/suggest-team`
- CORS enabled for web clients
- Structured context building to reduce hallucinations
- Low temperature (0.1) for consistent output

### Data Loader (`loader.py`)
- Loads TSV files on startup
- Fuzzy name matching with `difflib`
- Caches parsed data

### RAG System (`rag.py`)
- `all-MiniLM-L6-v2` embeddings
- Cosine similarity search
- Cache with hash validation
- Document types: character, equipment, gameplay, glossary

### Ollama Assistant (`ollama.py`)
- HTTP client for Ollama API
- System prompt with MK Mobile context
- RAG integration for context-aware responses
