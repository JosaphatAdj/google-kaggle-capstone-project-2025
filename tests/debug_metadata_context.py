# tests/debug_metadata_context.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_db.chroma_db import ChromaDBVectorStore

def debug_metadata_context():
    """Debug des métadonnées de contexte"""
    vector_store = ChromaDBVectorStore()
    
    print("🔍 DEBUG MÉTADONNÉES DE CONTEXTE")
    print("=" * 50)
    
    # Recherche sans filtre pour voir les contextes
    results = vector_store.search("E01", n_results=10, filter_metadata=None)
    print(f"📊 Résultats sans filtre: {len(results)}")
    
    # Analyser les contextes des documents trouvés
    context_count = {}
    
    for i, result in enumerate(results):
        metadata = result['metadata']
        context = metadata.get('context', 'NO_CONTEXT')
        file_path = metadata.get('file_path', 'NO_PATH')
        
        print(f"\n{i+1}. Contexte: '{context}'")
        print(f"   Fichier: {file_path}")
        print(f"   Document: {result['document'][:150]}...")
        
        # Compter les contextes
        context_count[context] = context_count.get(context, 0) + 1
    
    print(f"\n📋 RÉPARTITION DES CONTEXTES:")
    for context, count in context_count.items():
        print(f"   '{context}': {count} documents")
    
    # Tester les filtres avec les contextes réels
    print(f"\n🎯 TEST FILTRES AVEC CONTEXTES RÉELS:")
    for context in context_count.keys():
        filtered_results = vector_store.search("E01", n_results=5, filter_metadata={"context": context})
        print(f"   Filtre '{context}': {len(filtered_results)} résultats")

if __name__ == "__main__":
    debug_metadata_context()