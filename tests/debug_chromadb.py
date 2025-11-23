# tests/debug_chromadb.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_db.chroma_db import ChromaDBVectorStore

def debug_chromadb():
    """Debug complet de ChromaDB"""
    vector_store = ChromaDBVectorStore()
    
    print("🔍 DEBUG CHROMADB COMPLET")
    print("=" * 50)
    
    # 1. Stats de la collection
    stats = vector_store.get_collection_stats()
    print(f"📊 Collection Stats: {stats}")
    
    # 2. Voir TOUS les documents (sans filtre)
    print("\n🔎 RECHERCHE SANS FILTRE:")
    all_results = vector_store.search("error code E01", n_results=10)
    print(f"Résultats sans filtre: {len(all_results)}")
    
    for i, result in enumerate(all_results):
        print(f"  {i+1}. Document: {result['document'][:200]}...")
        print(f"     Metadata: {result['metadata']}")
        print(f"     Distance: {result['distance']}")
        print()
    
    # 3. Voir les métadonnées disponibles
    print("\n📋 MÉTADONNées DISPONIBLES:")
    if all_results:
        sample_metadata = all_results[0]['metadata']
        print(f"Clés de métadonnées: {list(sample_metadata.keys())}")
    else:
        print("Aucun document pour voir les métadonnées")
    
    # 4. Test avec différents termes
    print("\n🎯 TEST AVEC DIFFÉRENTS TERMES:")
    test_terms = ["E01", "roues bloquées", "battery", "XR25", "maintenance"]
    for term in test_terms:
        results = vector_store.search(term, n_results=2)
        print(f"'{term}': {len(results)} résultats")

if __name__ == "__main__":
    debug_chromadb()