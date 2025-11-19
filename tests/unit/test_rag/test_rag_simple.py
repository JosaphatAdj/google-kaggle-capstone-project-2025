#!/usr/bin/env python3
"""
Test simple du système RAG - Unit test
"""

import asyncio
import sys
import os
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from rag.rag_engine import RAGEngine

async def test_rag_system():
    """Test basique du système RAG"""
    print("🧪 Test du système RAG RoboNest...")
    
    # Initialisation
    rag = RAGEngine()
    
    # Test de stats
    stats = rag.get_stats()
    print(f"📊 Stats système: {stats}")
    
    # Test de recherche simple
    test_queries = [
        "Code erreur E01",
        "Spécifications XR30", 
        "Procédure maintenance",
        "Politique de congés"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Recherche: '{query}'")
        results = await rag.query(query, n_results=2)
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['document'][:100]}...")
            print(f"     📁 Contexte: {result['metadata'].get('context', 'N/A')}")
    
    print("\n✅ Test RAG terminé avec succès!")

if __name__ == "__main__":
    asyncio.run(test_rag_system())