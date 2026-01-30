# Documentation Index

Complete guide to all documentation in the mkmchat project.

## 📋 Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Project overview & quick start | Everyone |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current project status & summary | Developers |
| [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) | Quick LLM usage guide | Users |
| [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) | Detailed Gemini setup & docs | Developers |
| [RAG_QUICK_REFERENCE.md](RAG_QUICK_REFERENCE.md) | Quick RAG usage guide | Users |
| [RAG_SYSTEM.md](RAG_SYSTEM.md) | Technical RAG documentation | Developers |
| [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) | RAG implementation summary | Developers |

## 🚀 Getting Started

**New User?** Start here:
1. [README.md](README.md) - Project overview
2. [setup_gemini.sh](setup_gemini.sh) - Run setup script
3. [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) - Usage examples

**Want to understand the system?**
1. [PROJECT_STATUS.md](PROJECT_STATUS.md) - See what's built
2. [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - Learn about AI features
3. [RAG_SYSTEM.md](RAG_SYSTEM.md) - Understand semantic search

## 📚 Documentation by Topic

### Setup & Installation
- **[README.md](README.md)** - Installation instructions
- **[setup_gemini.sh](setup_gemini.sh)** - Automated setup script
- **[GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md)** - API key setup

### Using the Tools
- **[GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md)** - LLM tool usage
- **[RAG_QUICK_REFERENCE.md](RAG_QUICK_REFERENCE.md)** - Search tool usage
- **[README.md](README.md)** - MCP server usage

### Technical Documentation
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete status report
- **[GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md)** - Gemini implementation
- **[RAG_SYSTEM.md](RAG_SYSTEM.md)** - RAG architecture
- **[RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md)** - RAG details

### Data & Optimization
- **[data/README.md](data/README.md)** - Data format documentation
- **[TSV_STRUCTURE_UPDATE.md](TSV_STRUCTURE_UPDATE.md)** - TSV format migration
- **[ABILITIES_OPTIMIZATION.md](ABILITIES_OPTIMIZATION.md)** - Abilities format
- **[EQUIPMENT_MIGRATION.md](EQUIPMENT_MIGRATION.md)** - Equipment format

### Development
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Developer guidelines
- **[pyproject.toml](pyproject.toml)** - Project configuration
- **[tests/](tests/)** - Test suite

## 🎯 Documentation by Role

### End Users (MK Mobile Players)
**Goal**: Use the tools to improve gameplay

1. **Setup**
   - [README.md](README.md) - Quick start
   - [setup_gemini.sh](setup_gemini.sh) - Run setup

2. **Usage**
   - [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) - Ask questions, get help
   - [RAG_QUICK_REFERENCE.md](RAG_QUICK_REFERENCE.md) - Search characters/equipment

3. **Examples**
   - "What's the best counter to power drain?"
   - "Compare Scorpion variants"
   - "Build me a fire damage team"

### Developers (Contributing to Project)
**Goal**: Understand and extend the codebase

1. **Overview**
   - [README.md](README.md) - Project structure
   - [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current state
   - [.github/copilot-instructions.md](.github/copilot-instructions.md) - Conventions

2. **Core Systems**
   - [RAG_SYSTEM.md](RAG_SYSTEM.md) - Semantic search internals
   - [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - LLM integration
   - [data/README.md](data/README.md) - Data formats

3. **Implementation Details**
   - [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) - How RAG works
   - [TSV_STRUCTURE_UPDATE.md](TSV_STRUCTURE_UPDATE.md) - Data optimization
   - [tests/](tests/) - Test examples

### System Integrators (Using MCP)
**Goal**: Integrate mkmchat into other systems

1. **MCP Protocol**
   - [README.md](README.md) - Server setup
   - [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - Available tools

2. **Tool Reference**
   - [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) - LLM tools
   - [RAG_QUICK_REFERENCE.md](RAG_QUICK_REFERENCE.md) - Search tools
   - [mkmchat/server.py](mkmchat/server.py) - Tool schemas

3. **Testing**
   - [tests/test_gemini.py](tests/test_gemini.py) - LLM tests
   - [tests/test_rag.py](tests/test_rag.py) - RAG tests
   - [tests/test_tools.py](tests/test_tools.py) - Tool tests

## 📖 Detailed File Descriptions

### Main Documentation

#### README.md (160 lines)
- Project overview and features
- Installation instructions
- Quick start guide
- Project structure
- Basic usage examples
- **When to read**: First file for everyone

#### PROJECT_STATUS.md (New, 350+ lines)
- Complete feature list with status
- Test results and performance metrics
- Configuration options
- Known issues and solutions
- Future enhancements
- **When to read**: To understand current state

### Gemini LLM Documentation

#### GEMINI_QUICK_REFERENCE.md (New, 280+ lines)
- Quick start commands
- All 4 LLM tool examples
- Use cases by category
- Configuration options
- Testing instructions
- Troubleshooting
- **When to read**: To use Gemini tools

#### GEMINI_INTEGRATION.md (New, 350+ lines)
- Comprehensive setup guide
- Architecture explanation
- API reference
- Advanced usage
- Performance optimization
- Detailed troubleshooting
- **When to read**: For deep understanding

### RAG System Documentation

#### RAG_QUICK_REFERENCE.md (140 lines)
- Quick start guide
- All 3 RAG tool examples
- Usage patterns
- Configuration
- Optimization tips
- **When to read**: To use search tools

#### RAG_SYSTEM.md (280 lines)
- Technical architecture
- Embedding details
- Cache system
- Performance characteristics
- Implementation notes
- **When to read**: For technical details

#### RAG_IMPLEMENTATION.md (250 lines)
- Implementation summary
- Tool descriptions
- Testing procedures
- MCP response formats
- Integration guide
- **When to read**: During development

### Data Documentation

#### data/README.md
- TSV file formats
- Character data structure
- Equipment specifications
- Adding new data
- **When to read**: When adding game data

#### TSV_STRUCTURE_UPDATE.md
- Character TSV migration guide
- Format optimization rationale
- Before/after examples
- **When to read**: Understanding data format

#### ABILITIES_OPTIMIZATION.md
- Abilities TSV format
- Horizontal structure
- X-Ray handling
- **When to read**: Adding abilities

#### EQUIPMENT_MIGRATION.md
- Equipment TSV migration
- Simplified structure
- Format examples
- **When to read**: Adding equipment

### Setup & Scripts

#### setup_gemini.sh (New, 80 lines)
- Automated setup script
- Dependency installation
- API key instructions
- Status checking
- **When to run**: Initial setup

## 🔍 Finding Information

### "How do I...?"

| Task | See This |
|------|----------|
| Set up the project | [README.md](README.md) + [setup_gemini.sh](setup_gemini.sh) |
| Use the AI assistant | [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) |
| Search for characters | [RAG_QUICK_REFERENCE.md](RAG_QUICK_REFERENCE.md) |
| Add new characters | [data/README.md](data/README.md) |
| Understand the architecture | [PROJECT_STATUS.md](PROJECT_STATUS.md) |
| Fix API errors | [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) #Troubleshooting |
| Improve search results | [RAG_SYSTEM.md](RAG_SYSTEM.md) #Configuration |
| Run tests | [tests/test_gemini.py](tests/test_gemini.py) |

### "What is...?"

| Concept | See This |
|---------|----------|
| RAG | [RAG_SYSTEM.md](RAG_SYSTEM.md) |
| MCP Protocol | [README.md](README.md) + https://modelcontextprotocol.io |
| Gemini API | [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) |
| Semantic Search | [RAG_SYSTEM.md](RAG_SYSTEM.md) #How It Works |
| TSV Format | [data/README.md](data/README.md) |
| Tools | [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) |

### "Why is...?"

| Question | See This |
|----------|----------|
| Why use TSV over JSON? | [TSV_STRUCTURE_UPDATE.md](TSV_STRUCTURE_UPDATE.md) |
| Why RAG? | [RAG_SYSTEM.md](RAG_SYSTEM.md) #Introduction |
| Why Gemini? | [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) #Overview |
| Why cache embeddings? | [RAG_SYSTEM.md](RAG_SYSTEM.md) #Cache System |
| Why separate abilities? | [ABILITIES_OPTIMIZATION.md](ABILITIES_OPTIMIZATION.md) |

## 📊 Documentation Statistics

| Category | Files | Total Lines |
|----------|-------|-------------|
| Main Docs | 2 | ~500 |
| Gemini Docs | 2 | ~630 |
| RAG Docs | 3 | ~670 |
| Data Docs | 4 | ~400 |
| Scripts | 1 | ~80 |
| **Total** | **12** | **~2280** |

## 🎓 Learning Path

### Beginner Path
1. Read [README.md](README.md) - Understand project
2. Run [setup_gemini.sh](setup_gemini.sh) - Set up environment
3. Try [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) examples - Use tools
4. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) - See what's possible

### Intermediate Path
1. Read [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - Deep dive into AI
2. Read [RAG_SYSTEM.md](RAG_SYSTEM.md) - Understand search
3. Review [data/README.md](data/README.md) - Learn data structure
4. Run tests in [tests/](tests/) - Validate setup

### Advanced Path
1. Study [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) - Implementation details
2. Review [.github/copilot-instructions.md](.github/copilot-instructions.md) - Conventions
3. Check [TSV_STRUCTURE_UPDATE.md](TSV_STRUCTURE_UPDATE.md) - Data optimization
4. Contribute! Add features, improve docs

## 🆘 Quick Help

**Can't find something?**
- Check this index first
- Search in [PROJECT_STATUS.md](PROJECT_STATUS.md)
- Look in [README.md](README.md)

**Having issues?**
- [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) - API problems
- [RAG_SYSTEM.md](RAG_SYSTEM.md) - Search problems
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Known issues

**Want to contribute?**
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Guidelines
- [data/README.md](data/README.md) - Adding data
- [tests/](tests/) - Writing tests

---

**Last Updated**: After Gemini LLM integration  
**Total Documentation**: 12 files, ~2280 lines  
**Coverage**: Setup, Usage, Architecture, Data, Testing
