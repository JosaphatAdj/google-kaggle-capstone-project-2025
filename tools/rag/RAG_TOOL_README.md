**📄 FICHIER : `tools/rag/RAG_TOOL_README.md`** (Version complète)

```markdown
# 🧠 RAG Tool - RoboBrain Integration

**Tool MCP pour l'interrogation de la base de connaissances RoboNest**

## 🎯 Overview

Le **RAG Tool** permet à tous les agents du système d'interroger la base de connaissances centralisée (RoboBrain) via le standard MCP. Il fournit un accès unifié à toute la documentation produits, support, RH et marketing.

## 📋 Table des Matières
- [Setup et Installation](#-setup-et-installation)
- [Ingestion des Documents](#-ingestion-des-documents) 
- [Tools Disponibles](#-tools-disponibles)
- [Intégration Agents](#-intégration-avec-les-agents)
- [Maintenance](#-maintenance)

## ⚙️ Setup et Installation

### Prérequis
```bash
# Dépendances principales
pip install chromadb sentence-transformers

# Pour le développement
pip install pytest asyncio
```

### Structure des Données
```
rag/
├── knowledge_base/           # Documents sources
│   ├── products/            # Documentation produits
│   ├── support/             # Support client
│   ├── marketing/           # Marketing & contenu
│   ├── internal/            # RH & procédures internes
│   └── technical/           # Documentation technique
├── vector_db/
│   └── chroma_db/           # Base vectorielle (auto-généré)
└── loaders/                 # Chargeurs de documents
```

### Initialisation
```bash
# 1. Nettoyer la base existante
python scripts/clean_chromadb.py

# 2. Indexer tous les documents
python scripts/index_knowledge_base.py

# 3. Vérifier l'indexation
python tests/unit/test_rag/test_rag_simple.py
```

## 📥 Ingestion des Documents

### Structure des Documents

Les documents doivent être organisés par contexte :

```
knowledge_base/
├── products/
│   ├── manuals/
│   │   ├── xr_series_manual_french.md
│   │   ├── xr_series_manual_english.md
│   │   └── lawnbot_manual_french.md
│   ├── specs/
│   │   ├── xr_specs_french.json
│   │   └── xr_specs_english.json
│   └── error_codes/
│       ├── error_codes_french.json
│       └── error_codes_english.json
```

### Formats Supportés

| Format | Chargeur | Métadonnées Auto |
|--------|----------|------------------|
| Markdown (.md) | `MarkdownLoader` | Contexte, langue |
| JSON (.json) | `JSONLoader` | Structure, type |
| Text (.txt) | `MarkdownLoader` | Basique |

### Script d'Indexation

```python
# scripts/index_knowledge_base.py
from rag.rag_engine import RAGEngine

async def index_entire_knowledge_base():
    rag_engine = RAGEngine()
    
    # Indexation automatique de tous les documents
    # Détection auto du contexte par le chemin
    # Détection auto de la langue par le nom de fichier
```

### Ajout de Nouveaux Documents

1. **Placer le fichier** dans le dossier contexte approprié
2. **Nommer avec la langue** : `_french.md` ou `_english.md`
3. **Lancer l'indexation** :
```bash
python scripts/index_knowledge_base.py
```

### Mise à Jour des Documents

```python
# Pour mettre à jour un document spécifique
from rag.rag_engine import RAGEngine

rag_engine = RAGEngine()
await rag_engine.index_document("rag/knowledge_base/products/manuals/xr_series_manual_french.md")
```

## 🔧 Tools Disponibles

### 1. **Tool Principal** - `query_robo_brain`
```python
query_knowledge_base(
    question: str,
    context: str = None,
    department: str = None
) -> Dict
```

**Utilisation :**
```python
from tools.rag.rag_tool import RAGTool

rag_tool = RAGTool()
result = rag_tool.query_knowledge_base(
    question="Code erreur E01",
    context="support",
    department="technical_support"
)
```

### 2. **Tools Spécialisés** (Recommandés)
```python
from tools.rag.specialized_tools import SpecializedRAGTools

specialized = SpecializedRAGTools()

# Pour le support client
support_result = specialized.query_support_knowledge("robot ne démarre pas")

# Pour le support technique  
tech_result = specialized.query_technical_docs("problème navigation lidar")

# Pour les RH
hr_result = specialized.query_hr_policies("politique congés")
```

## 🎪 Contextes de Recherche

| Contexte | Contenu | Utilisation Typique |
|----------|---------|---------------------|
| `support` | FAQ, scripts, procédures support | Support client, résolution problèmes |
| `products` | Documentation technique, codes erreur | Support technique, dépannage |
| `marketing` | Guidelines, contenu, SEO | Création contenu, campagnes |
| `hr` | Politiques RH, procédures internes | Support employés, RH |
| `technical` | APIs, firmware, spécifications | Développement, intégrations |
| `internal` | Procédures opérationnelles | Coordination, management |

## 🚀 Intégration avec les Agents

### COO Agent (Orchestrateur)
```python
from tools.rag.rag_tool import RAGTool

class COOAgent:
    def __init__(self):
        self.rag_tool = RAGTool().get_tool()
    
    async def route_ticket(self, ticket_description: str):
        # Consultation RAG pour décision de routage
        rag_result = await self.rag_tool.func(
            question=ticket_description,
            context="support"
        )
        return self._decide_routing(rag_result)
```

### FAQ Agent
```python
from tools.rag.specialized_tools import SpecializedRAGTools

class FAQAgent:
    def __init__(self):
        self.rag = SpecializedRAGTools().get_support_tool()
    
    def answer_question(self, user_question: str):
        result = self.rag.func(user_question)
        return self._format_answer(result)
```

## 📊 Format de Réponse

```python
{
    "status": "success",  # ou "error"
    "question": "Code erreur E01",
    "department": "technical_support",
    "context_used": "support",
    "results_count": 3,
    "results": [
        {
            "content": "Code E01: Roues bloquées. Causes: cheveux, obstacle...",
            "metadata": {
                "file_path": "products/error_codes/error_codes_fr.json",
                "context": "products",
                "language": "fr"
            },
            "relevance_score": 0.92
        }
    ]
}
```

## 🔧 Maintenance

### Nettoyage de la Base
```bash
# Supprimer complètement ChromaDB
python scripts/clean_chromadb.py

# Réindexer depuis zéro
python scripts/index_knowledge_base.py
```

### Monitoring
```python
# Vérifier les stats
from rag.rag_engine import RAGEngine

rag = RAGEngine()
stats = rag.get_stats()
print(f"Documents indexés: {stats['vector_store']['total_documents']}")
```

### Résolution de Problèmes

**Problème** : Résultats non pertinents
```bash
# 1. Vérifier l'indexation
python tests/unit/test_rag/test_rag_simple.py

# 2. Réindexer si nécessaire
python scripts/clean_chromadb.py
python scripts/index_knowledge_base.py
```

**Problème** : Erreurs ChromaDB
```bash
# Supprimer et recréer la base
rm -rf rag/vector_db/chroma_db
python scripts/index_knowledge_base.py
```

## 🧪 Tests et Validation

### Tests Unitaires
```bash
# Test du moteur RAG
python tests/unit/test_rag/test_rag_simple.py

# Test du RAG Tool
python tests/unit/test_tools/test_rag_tool.py

# Test d'intégration
python tests/integration/test_rag_agent_integration.py
```

### Validation des Résultats
```python
# Vérifier la pertinence des résultats
from rag.rag_engine import RAGEngine

rag = RAGEngine()
results = await rag.query("Code erreur E01", context="products")

for result in results:
    print(f"Score: {result.get('distance')}")
    print(f"Contenu: {result['document'][:200]}...")
```

## 🎯 Best Practices

### ✅ À Faire
- Utiliser les **tools spécialisés** par département
- Spécifier le **contexte** approprié
- **Limiter** les résultats à 3-5 pour la pertinence
- **Logger** toutes les requêtes pour le debugging
- **Maintenir** la structure des dossiers de documents

### ❌ À Éviter
- Interroger sans contexte spécifique
- Utiliser le tool principal directement (préférer les spécialisés)
- Ignorer les métadonnées de résultats
- Modifier manuellement la base ChromaDB

## 🔮 Évolutions Futures

- [ ] Serveur MCP RAG dédié
- [ ] Cache des embeddings
- [ ] Métriques de performance
- [ ] Support multi-langues avancé
- [ ] API REST pour intégrations externes
- [ ] Interface d'administration des documents

## 📞 Support

Pour les questions sur l'intégration RAG :
- Consulter `rag/rag_engine.py` pour le moteur de base
- Voir les tests dans `tests/unit/test_rag/`
- Documentation ADK : https://google.github.io/adk-docs/

**Fichiers Importants :**
- `rag/rag_engine.py` - Moteur principal
- `tools/rag/rag_tool.py` - Tool MCP
- `scripts/index_knowledge_base.py` - Indexation
- `scripts/clean_chromadb.py` - Nettoyage

---

**Mainteneurs :** Équipe Technique RoboNest  
**Dernière mise à jour :** ${DATE}
```

