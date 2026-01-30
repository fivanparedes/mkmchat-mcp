# Changelog

All notable changes to the mkmchat project.

## [Unreleased] - 2024

### Added - Gemini LLM Integration 🤖

#### New Features
- **Gemini AI Assistant** - Conversational AI powered by Google Gemini API
  - Natural language understanding for complex game questions
  - RAG integration for accurate, data-backed responses
  - Support for gemini-1.5-flash and gemini-1.5-pro models
  
#### New MCP Tools
- **`ask_assistant`** - Ask any question about MK Mobile
  - Natural language queries
  - Intelligent responses with game data context
  - Examples: "What's the best counter to power drain?"
  
- **`compare_characters_llm`** - AI-powered character comparison
  - Detailed analysis of strengths/weaknesses
  - Strategic recommendations
  - Synergy insights
  
- **`suggest_team_llm`** - Intelligent team building
  - Strategy-based suggestions
  - Character synergy analysis
  - Equipment recommendations
  
- **`explain_mechanic_llm`** - Comprehensive mechanic explanations
  - Detailed breakdowns of game mechanics
  - Usage tips and strategies
  - Counter-play advice

#### New Files
- `mkmchat/llm/` - New LLM integration module
  - `gemini.py` (355 lines) - GeminiAssistant implementation
  - `__init__.py` - Module exports
  
- `mkmchat/tools/llm_tools.py` (175 lines) - MCP tool wrappers for Gemini
  
- `tests/test_gemini.py` (200+ lines) - Comprehensive Gemini test suite
  
- **Documentation**:
  - `GEMINI_INTEGRATION.md` (350+ lines) - Complete setup guide
  - `GEMINI_QUICK_REFERENCE.md` (280+ lines) - Quick usage guide
  - `PROJECT_STATUS.md` (350+ lines) - Project status summary
  - `DOCUMENTATION_INDEX.md` (500+ lines) - Documentation navigation
  
- `setup_gemini.sh` (80 lines) - Automated setup script

#### Updated Files
- `pyproject.toml` - Added `google-generativeai` dependency
- `README.md` - Added Gemini features section
- `mkmchat/server.py` - Integrated 4 new LLM tools

#### Configuration
- New environment variable: `GEMINI_API_KEY`
- Optional: `GEMINI_MODEL` (default: gemini-1.5-flash)

---

## [Unreleased] - 2024

### Added - RAG System 🔍

#### New Features
- **Semantic Search** - AI-powered search across all game data
  - 204 documents indexed (characters, abilities, equipment, gameplay)
  - sentence-transformers embeddings (all-MiniLM-L6-v2)
  - Intelligent caching system for fast performance
  
#### New MCP Tools
- **`semantic_search`** - Natural language search
  - Query: "Find characters with fire damage"
  - Returns: Relevant characters ranked by similarity
  
- **`search_by_strategy`** - Strategy-focused search
  - Query: "Build a defensive tank team"
  - Returns: Characters and equipment matching strategy
  
- **`explain_mechanic`** - Mechanic explanations
  - Query: "Explain power drain"
  - Returns: Detailed explanation with examples

#### New Files
- `mkmchat/data/rag.py` (430 lines) - RAG system core
  - Document class for data representation
  - RAGSystem class with semantic search
  - Cache management system
  
- `mkmchat/tools/semantic_search.py` (245 lines) - MCP tools
  - Proper MCP response format
  - Error handling
  - Flexible query interface
  
- `tests/test_rag.py` (130 lines) - RAG test suite
  - Indexing tests
  - Search tests
  - Cache validation
  
- **Documentation**:
  - `RAG_SYSTEM.md` (280 lines) - Technical documentation
  - `RAG_IMPLEMENTATION.md` (250 lines) - Implementation guide
  - `RAG_QUICK_REFERENCE.md` (140 lines) - User guide

#### Updated Files
- `pyproject.toml` - Added `sentence-transformers`, `numpy` dependencies
- `README.md` - Added RAG system section
- `mkmchat/server.py` - Integrated 3 new RAG tools

#### Technical Details
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Cache Location**: `data/.rag_cache/`
- **Performance**: 
  - Indexing: ~2-3s for 204 documents
  - Cache load: ~0.1s
  - Search: ~0.01s per query

#### Bug Fixes
- Fixed MCP response format validation errors
- Proper JSON formatting for tool responses
- Correct content structure: `{content: [{type: "text", text: "..."}]}`

---

## [1.0.0] - 2024

### Initial Release

#### Features
- **MCP Server** - Model Context Protocol integration
- **Character Database** - 204 characters with stats and abilities
- **Equipment Database** - Common equipment with effects
- **Team Suggestions** - Rule-based team building

#### MCP Tools
- **`get_character_info`** - Query character stats, abilities, passives
- **`get_equipment_info`** - Query equipment details
- **`suggest_team`** - Basic team composition suggestions

#### Data Format
- **TSV Files** - Optimized tab-separated format
  - `characters.tsv` - Character base data
  - `abilities.tsv` - Character abilities (horizontal format)
  - `passives.tsv` - Passive abilities with tags
  - `equipment_basic.tsv` - Equipment specifications
  - `gameplay.txt` - Basic game mechanics
  - `glossary.txt` - Game terminology

#### Documentation
- `README.md` - Project overview
- `data/README.md` - Data format documentation
- `.github/copilot-instructions.md` - Developer guidelines
- `TSV_STRUCTURE_UPDATE.md` - Data migration guide
- `ABILITIES_OPTIMIZATION.md` - Abilities format docs
- `EQUIPMENT_MIGRATION.md` - Equipment format docs

#### Infrastructure
- **Python Package** - Installable with pip
- **Test Suite** - pytest-based testing
- **Pydantic Models** - Type-safe data models
- **Data Loader** - TSV parsing with JSON fallback

---

## Version History Summary

| Version | Date | Major Features | Tools Added | Files Added |
|---------|------|----------------|-------------|-------------|
| 1.0.0 | 2024 | Initial release, MCP server, TSV data | 3 | ~15 |
| Unreleased | 2024 | RAG system, semantic search | +3 (6 total) | +8 |
| Unreleased | 2024 | Gemini LLM, AI assistant | +4 (10 total) | +9 |

## Statistics

### Codebase Growth
- **Initial**: ~1,500 lines (core system)
- **After RAG**: ~2,300 lines (+800)
- **After Gemini**: ~3,100 lines (+800)

### Documentation Growth
- **Initial**: ~600 lines
- **After RAG**: ~1,270 lines (+670)
- **After Gemini**: ~2,280 lines (+1,010)

### Features
- **MCP Tools**: 3 → 6 → 10
- **Data Sources**: 6 files, 204 documents
- **Dependencies**: 5 → 7 → 8

## Upcoming Features

### Planned Enhancements
- [ ] Conversation history/memory for LLM
- [ ] Streaming responses for long queries
- [ ] Multi-turn conversations
- [ ] Hybrid search (semantic + keyword)
- [ ] Query expansion with game-specific synonyms
- [ ] Cross-encoder re-ranking for better search
- [ ] Upgrade to all-mpnet-base-v2 embedding model

### Data Expansions
- [ ] Legendary/Epic equipment
- [ ] Tower mode data
- [ ] Challenge mode data
- [ ] Character skins/variants
- [ ] Talent tree data

### Quality Improvements
- [ ] Lower default min_similarity to 0.2
- [ ] Increase default top_k to 10
- [ ] Add more comprehensive tests
- [ ] Performance profiling
- [ ] API rate limit handling

## Migration Guides

### Upgrading to RAG System
```bash
# Install new dependencies
pip install -e .

# RAG will auto-index on first use
# Or manually index:
python -c "from mkmchat.data.rag import RAGSystem; rag = RAGSystem(); rag.index_data()"
```

### Upgrading to Gemini LLM
```bash
# Run setup script
./setup_gemini.sh

# Set API key
export GEMINI_API_KEY='your-key-here'

# Test integration
python tests/test_gemini.py
```

## Breaking Changes

### None Yet
All features are backward compatible:
- Old tools still work (get_character_info, etc.)
- New tools are additive
- Data format unchanged (TSV)
- No API changes

## Contributors

- Initial development and RAG system
- Gemini LLM integration
- Comprehensive documentation

## Acknowledgments

- **sentence-transformers** - Semantic search embeddings
- **Google Gemini** - LLM API
- **Model Context Protocol** - Tool integration standard
- **MK Mobile Community** - Game data and insights

---

**Note**: This project is under active development. Features marked as "Unreleased" are complete and available in the main branch, pending version tagging.
