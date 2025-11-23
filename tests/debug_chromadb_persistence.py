# tests/debug_chromadb_persistence.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def debug_chromadb_persistence():
    """Debug complet de la persistence ChromaDB"""
    print("🔍 DEBUG PERSISTENCE CHROMADB")
    print("=" * 50)
    
    # Chemins absolus
    project_root = Path(__file__).parent.parent
    chroma_path = project_root / "chroma_db"
    default_chroma_path = Path("./chroma_db")
    
    print(f"📁 Project Root: {project_root}")
    print(f"📁 ChromaDB Path (absolu): {chroma_path}")
    print(f"📁 ChromaDB Path (relatif): {default_chroma_path}")
    print(f"📁 Existe (absolu): {chroma_path.exists()}")
    print(f"📁 Existe (relatif): {default_chroma_path.exists()}")
    
    # Vérifier le contenu
    if chroma_path.exists():
        print(f"\n📂 CONTENU {chroma_path}:")
        for item in chroma_path.iterdir():
            print(f"  - {item.name} (dir: {item.is_dir()})")
            if item.is_dir():
                for subitem in item.iterdir():
                    print(f"    * {subitem.name}")
    
    if default_chroma_path.exists():
        print(f"\n📂 CONTENU {default_chroma_path}:")
        for item in default_chroma_path.iterdir():
            print(f"  - {item.name} (dir: {item.is_dir()})")
    
    # Vérifier les variables d'environnement
    print(f"\n🌍 VARIABLES D'ENVIRONNEMENT:")
    print(f"  CWD: {Path.cwd()}")
    
    # Test création manuelle
    print(f"\n🔧 TEST CRÉATION MANUELLE:")
    test_client_path = project_root / "test_chroma"
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(test_client_path))
        collection = client.get_or_create_collection("test")
        collection.add(
            documents=["test document"],
            metadatas=[{"test": "metadata"}],
            ids=["test_id"]
        )
        print(f"✅ Test ChromaDB créé: {test_client_path}")
        print(f"✅ Documents dans test: {collection.count()}")
    except Exception as e:
        print(f"❌ Erreur test ChromaDB: {e}")

if __name__ == "__main__":
    debug_chromadb_persistence()