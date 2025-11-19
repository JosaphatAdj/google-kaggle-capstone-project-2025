import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any
import logging

class ChromaDBVectorStore:
    """Gestionnaire de base vectorielle ChromaDB pour RoboNest"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialise le client ChromaDB avec configuration"""
        try:
            # Création du dossier si inexistant
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Configuration ChromaDB
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Création/accès à la collection principale
            self.collection = self.client.get_or_create_collection(
                name="robonest_knowledge",
                metadata={"description": "Base de connaissances RoboNest - Multi-agents"}
            )
            
            self.logger.info("✅ ChromaDB initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation ChromaDB: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """Ajoute des documents à la collection"""
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"✅ {len(documents)} documents ajoutés à ChromaDB")
        except Exception as e:
            self.logger.error(f"❌ Erreur ajout documents: {e}")
            raise
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """Recherche sémantique dans la base"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"❌ Erreur recherche: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la collection"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "robonest_knowledge",
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            self.logger.error(f"❌ Erreur stats: {e}")
            return {}