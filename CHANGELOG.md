# Changelog

All notable changes to mkmchat-mcp.

## [2.0.0] - 2026-01-30

### Added
- **HTTP API Server** - REST endpoint for team suggestions
  - `POST /suggest-team` returns structured JSON
  - CORS support for web clients
  - Run with `python -m mkmchat http [port]`

- **Structured Context Building** - Reduces LLM hallucinations
  - Equipment categorized by type (Weapon/Armor/Accessory)
  - Clear section headers in prompts
  - Low temperature (0.1) for consistent output

### Changed
- **Simplified to 10 Tools** (from 18)
- **Ollama-only LLM** - Removed cloud dependencies
- **Version bumped to 2.0.0**

### Removed
- Gemini LLM integration (cloud-based)
- Redundant search tools:
  - `search_glossary_term` → use `semantic_search(doc_type="glossary")`
  - `search_gameplay` → use `semantic_search(doc_type="gameplay")`
  - `search_by_strategy` → use `semantic_search`
  - `explain_mechanic` → use `explain_mechanic_ollama`
- Outdated documentation files

### Current Tool Set

**Data Tools (3)**
- `get_character_info` - Character details with fuzzy matching
- `get_equipment_info` - Equipment details with fuzzy matching
- `suggest_team` - Rule-based team suggestions

**Search Tools (3)**
- `semantic_search` - RAG-powered semantic search
- `search_characters_advanced` - Attribute-based filtering
- `search_equipment_advanced` - Attribute-based filtering

**LLM Tools (4)**
- `ask_ollama` - General questions with RAG context
- `compare_characters_ollama` - AI character comparison
- `suggest_team_ollama` - AI team suggestions
- `explain_mechanic_ollama` - AI mechanic explanations

---

## [1.0.0] - 2024

### Initial Release
- MCP server with character and equipment tools
- RAG system with semantic search
- Ollama local AI integration
- 185 characters, 280+ equipment items
