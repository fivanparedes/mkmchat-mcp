# Changelog

All notable changes to the mkmchat project.

## [2.0.0] - 2026-01-30

### Changed - Architecture Simplification 🧹

#### Removed
- **Gemini LLM Integration** - Removed cloud-based AI in favor of local-only
- **Redundant Search Tools** - Consolidated search functionality
  - Removed `search_glossary_term` (use `semantic_search` with `doc_type="glossary"`)
  - Removed `search_gameplay` (use `semantic_search` with `doc_type="gameplay"`)
  - Removed `search_by_strategy` (use `semantic_search`)
  - Removed `explain_mechanic` (use `explain_mechanic_ollama`)

#### Files Removed
- `mkmchat/llm/gemini.py` - Gemini assistant (replaced by Ollama-only)
- `GEMINI_INTEGRATION.md` - Gemini documentation
- `GEMINI_QUICK_REFERENCE.md` - Gemini quick reference
- `GEMINI_VS_OLLAMA.md` - Comparison document
- `COMPLETION_SUMMARY.md` - Outdated summary
- `PROJECT_STATUS.md` - Outdated status
- `DOCUMENTATION_INDEX.md` - Outdated index

#### Updated
- **Tool Count**: 18 → 10 tools (simplified)
- **LLM Module**: Now Ollama-only
- **Documentation**: Updated to reflect current architecture
- `README.md` - Removed Gemini references
- `ARCHITECTURE.md` - Updated architecture diagrams
- `mkmchat/tools/__init__.py` - Clean exports
- `mkmchat/llm/__init__.py` - Ollama-only exports

### Current Tool Set (10 total)

#### Data Tools (3)
- `get_character_info` - Character details with fuzzy matching
- `get_equipment_info` - Equipment details with fuzzy matching
- `suggest_team` - Rule-based team suggestions

#### Search Tools (3)
- `semantic_search` - RAG-powered semantic search (supports all doc types)
- `search_characters_advanced` - Attribute-based character filtering
- `search_equipment_advanced` - Attribute-based equipment filtering

#### LLM Tools - Ollama (4)
- `ask_ollama` - General questions with RAG context
- `compare_characters_ollama` - AI character comparison
- `suggest_team_ollama` - AI team suggestions
- `explain_mechanic_ollama` - AI mechanic explanations

---

## [Unreleased] - 2024

### Added - Ollama Local AI 🖥️

#### New Features
- **Ollama Integration** - Local AI without API costs
- **Model**: llama3.2:3b (configurable)
- **Benefits**: Free, private, offline-capable

#### New MCP Tools
- `ask_ollama` - Local AI questions
- `compare_characters_ollama` - Local character comparison
- `suggest_team_ollama` - Local team suggestions
- `explain_mechanic_ollama` - Local mechanic explanations

---

## [Unreleased] - 2024

### Added - RAG System 🔍

#### New Features
- **Semantic Search** - AI-powered search across all game data
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Caching**: Hash-based validation for fast performance

#### New MCP Tools
- `semantic_search` - Natural language search
- `search_characters_advanced` - Attribute filtering
- `search_equipment_advanced` - Attribute filtering

#### Technical Details
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Cache Location**: `data/.rag_cache/`

---

## [1.0.0] - 2024

### Initial Release

#### Features
- **MCP Server** - Model Context Protocol integration
- **Character Database** - 185+ characters with stats and abilities
- **Equipment Database** - 282 equipment items with effects
- **Team Suggestions** - Rule-based team building

#### MCP Tools
- `get_character_info` - Query character stats, abilities, passives
- `get_equipment_info` - Query equipment details
- `suggest_team` - Basic team composition suggestions

#### Data Format
- **TSV Files** - Optimized tab-separated format
  - `characters.tsv` - Character base data
  - `abilities.tsv` - Character abilities
  - `passives.tsv` - Passive abilities
  - `equipment_*.tsv` - Equipment specifications
  - `gameplay.txt` - Game mechanics
  - `glossary.txt` - Game terminology

---

## Version Summary

| Version | Tools | Major Changes |
|---------|-------|---------------|
| 1.0.0 | 3 | Initial release, MCP server, data layer |
| + RAG | 6 | Semantic search, embeddings |
| + Ollama | 10 | Local LLM integration |
| 2.0.0 | 10 | Simplified architecture, Ollama-only |

## Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Ollama URL | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| Ollama Model | `OLLAMA_MODEL` | `llama3.2:3b` |
