**README.md**

# 🧠 RoboBrain - RAG System for RoboNest

## 📋 Description

RoboBrain is the central **Retrieval-Augmented Generation (RAG)** system for RoboNest, powering all AI agents with a unified and structured knowledge base.

## 🏗️ Architecture

### Data Structure
```
rag/
├── knowledge_base/          # Knowledge base
│   ├── products/           # Product documentation (XR, LawnBot)
│   ├── support/            # Customer support & procedures
│   ├── marketing/          # Marketing content & guidelines
│   ├── internal/           # Internal resources (HR, IT)
│   └── technical/          # Technical documentation
├── vector_db/              # ChromaDB vector store
├── loaders/                # Document loaders
├── embeddings.py           # Embeddings generator
└── rag_engine.py           # Main RAG engine
```

### Core Components

#### 🔧 **RAG Engine**
- **`rag_engine.py`** - Main RAG query orchestrator
- Handles semantic search and context filtering
- Unified interface for all agents

#### 🗄️ **Vector Store**
- **`vector_db/chroma_db.py`** - ChromaDB manager
- Embedding persistence with metadata
- Optimized semantic search

#### 📚 **Knowledge Base**
- **Bilingual format**: French 🇫🇷 and English 🇺🇸
- **Modular structure** by department
- **Optimized documents** for semantic search

## 🚀 Usage

### Initialization
```python
from rag.rag_engine import RAGEngine

# Automatic initialization
rag_engine = RAGEngine()
```

### Basic Query
```python
# Search across entire knowledge base
results = await rag_engine.query("error code E01")

# Search with specific context
results = await rag_engine.query(
    "battery maintenance", 
    context="support",
    n_results=5
)
```

### Agent Integration
```python
from tools.rag.rag_tool import RAGTool

# MCP tool for ADK agents
rag_tool = RAGTool().get_tool()

# Usage in an agent
response = rag_tool.query_knowledge_base(
    question="How to fix E01?",
    context="support",
    department="technical_support"
)
```

## 🛠️ Development

### Adding Documents

1. **Place document** in appropriate folder:
   ```bash
   rag/knowledge_base/{context}/subfolder/new_document.md
   ```

2. **Supported formats**:
   - Markdown (`.md`)
   - JSON (`.json`) 

3. **Automatic indexing**:
   ```bash
   python scripts/index_knowledge_base.py
   ```

### Automatic Metadata

Documents are automatically tagged with:
- **`context`**: Department (support, products, marketing, hr, technical)
- **`language`**: Language (fr, en) based on filename
- **`file_path`**: Relative file path

## 🔧 Maintenance

### Database Cleanup
```bash
python scripts/clean_chromadb.py
```

### Full Reindexing
```bash
python scripts/clean_chromadb.py
python scripts/index_knowledge_base.py
```

### Status Check
```bash
python tests/unit/test_rag/test_rag_simple.py
```

## 📊 Monitoring

### Key Metrics
- **Indexed documents**: `rag_engine.get_stats()`
- **Search performance**: Response time & relevance
- **Context coverage**: Distribution by department

### Logging
- **INFO level**: Main operations
- **DEBUG level**: Search & embedding details
- **Log files**: `logs/rag/`

## 🎯 Search Contexts

| Context | Content | Examples |
|---------|---------|----------|
| **support** | Error codes, troubleshooting, FAQ | `E01`, `battery issue`, `navigation problem` |
| **products** | Specifications, manuals | `XR30 specs`, `LawnBot features` |
| **technical** | APIs, firmware, architecture | `API documentation`, `firmware update` |
| **marketing** | Content, SEO, campaigns | `blog post`, `social media`, `email campaign` |
| **hr** | HR policies, procedures | `vacation policy`, `onboarding` |
| **internal** | Operations, security | `security protocols`, `internal procedures` |

## 🔍 Troubleshooting

### Common Issues

**No search results**
```bash
# Check indexing
python tests/debug_chromadb.py

# Reindex if needed
python scripts/clean_chromadb.py
python scripts/index_knowledge_base.py
```

**ChromaDB errors**
```bash
# Check persistence path
python tests/debug_chromadb_persistence.py
```

### Testing
```bash
# RAG unit test
python tests/unit/test_rag/test_rag_simple.py

# Agent integration test
python tests/unit/test_agents/test_rag_multi_agent.py

# Performance test
python tests/unit/test_rag/test_rag_performance.py
```

## 📈 Performance

- **Response time**: < 500ms for most queries
- **Accuracy**: > 85% relevance on common queries
- **Scalability**: Support for up to 10,000 documents

## 🤝 Contribution

### Guidelines
1. **Bilingual documents**: Maintain FR/EN versions
2. **Modular structure**: Respect context-based architecture
3. **Metadata**: Let automatic indexing handle tagging
4. **Testing**: Verify impact on existing searches

---

**RoboBrain** - The knowledge brain of RoboNest 🤖✨