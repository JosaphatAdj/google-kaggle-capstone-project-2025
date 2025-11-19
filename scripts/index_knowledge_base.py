#!/usr/bin/env python3
"""
Script d'indexation de la base de connaissances RoboNest
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from rag.rag_engine import RAGEngine

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def index_entire_knowledge_base():
    """Indexe toute la base de connaissances RoboNest"""
    logger = logging.getLogger("indexer")
    rag_engine = RAGEngine()
    
    # Dossier racine de la connaissance
    knowledge_base_path = Path("rag/knowledge_base")
    
    if not knowledge_base_path.exists():
        logger.error("❌ Dossier knowledge_base non trouvé")
        return
    
    # Compteurs
    total_files = 0
    indexed_files = 0
    
    # Patterns de fichiers à indexer
    supported_extensions = {'.md', '.json', '.txt'}
    
    logger.info("🚀 Début de l'indexation de la base de connaissances...")
    
    # Parcours récursif de tous les fichiers
    for file_path in knowledge_base_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in supported_extensions:
            total_files += 1
            logger.info(f"📄 Indexation: {file_path}")
            
            try:
                await rag_engine.index_document(str(file_path))
                indexed_files += 1
            except Exception as e:
                logger.error(f"❌ Erreur avec {file_path}: {e}")
    
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