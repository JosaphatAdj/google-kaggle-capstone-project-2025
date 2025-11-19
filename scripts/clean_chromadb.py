# scripts/clean_chromadb.py
import shutil
import os

def clean_chroma_db():
    """Supprime complètement la base ChromaDB"""
    chroma_path = "./chroma_db"
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        print("✅ ChromaDB nettoyé")
    else:
        print("ℹ️  Aucune base à nettoyer")

if __name__ == "__main__":
    clean_chroma_db()