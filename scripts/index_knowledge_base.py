# scripts/index_knowledge_base.py (CORRIGÉ)
#!/usr/bin/env python3
"""
Script d'indexation de la base de connaissances RoboNest - VERSION CORRIGÉE
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Ajout du chemin racine pour les imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from rag.rag_engine import RAGEngine

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def index_entire_knowledge_base():
    """Indexe toute la base de connaissances RoboNest - VERSION CORRIGÉE"""
    logger = logging.getLogger("indexer")
    
    # Chemin ABSOLU vers la knowledge base
    knowledge_base_path = project_root / "rag" / "knowledge_base"
    
    print(f"🔍 Recherche dans: {knowledge_base_path.absolute()}")
    
    if not knowledge_base_path.exists():
        logger.error(f"❌ Dossier knowledge_base non trouvé: {knowledge_base_path}")
        return
    
    rag_engine = RAGEngine()
    
    # Compteurs
    total_files = 0
    indexed_files = 0
    
    # Patterns de fichiers à indexer
    supported_extensions = {'.md', '.json', '.txt'}
    
    logger.info("🚀 Début de l'indexation de la base de connaissances...")
    
    # Parcours récursif de tous les fichiers
    for file_path in knowledge_base_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            total_files += 1
            relative_path = file_path.relative_to(project_root)
            logger.info(f"📄 Indexation: {relative_path}")
            
            try:
                await rag_engine.index_document(str(file_path))
                indexed_files += 1
                logger.info(f"✅ Indexé: {relative_path}")
            except Exception as e:
                logger.error(f"❌ Erreur avec {relative_path}: {e}")
    
    # Affichage des statistiques finales
    stats = rag_engine.get_stats()
    logger.info("=" * 50)
    logger.info("📊 RAPPORT D'INDEXATION TERMINÉ")
    logger.info(f"📁 Fichiers trouvés: {total_files}")
    logger.info(f"✅ Fichiers indexés: {indexed_files}")
    logger.info(f"❌ Échecs: {total_files - indexed_files}")
    logger.info(f"🗄️ Documents dans ChromaDB: {stats['vector_store'].get('total_documents', 0)}")
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(index_entire_knowledge_base())