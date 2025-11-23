import logging
from typing import List, Dict, Any
from .vector_db.chroma_db import ChromaDBVectorStore
from .embeddings import EmbeddingsGenerator
from .loaders.markdown_loader import MarkdownLoader
from .loaders.json_loader import JSONLoader
import os

class RAGEngine:
    """Moteur RAG principal pour RoboNest"""
    
    def __init__(self):
        self.vector_store = ChromaDBVectorStore()
        self.embeddings = EmbeddingsGenerator()
        self.markdown_loader = MarkdownLoader()
        self.json_loader = JSONLoader()
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ Moteur RAG initialisé")
    
    async def index_document(self, file_path: str):
        """Indexe un document dans ChromaDB"""
        try:
            # Sélection du loader selon l'extension
            if file_path.endswith('.md'):
                loader = self.markdown_loader
            elif file_path.endswith('.json'):
                loader = self.json_loader
            else:
                self.logger.warning(f"Format non supporté: {file_path}")
                return
            
            # Chargement du document
            document_data = loader.load_file(file_path)
            if not document_data:
                return
            
            # Découpage en chunks (pour Markdown)
            if file_path.endswith('.md'):
                chunks = loader.chunk_document(document_data['content'])
                documents_to_index = []
                metadatas_to_index = []
                ids_to_index = []
                
                for chunk in chunks:
                    documents_to_index.append(chunk['content'])
                    metadata = document_data['metadata'].copy()
                    metadata.update({
                        'chunk_id': chunk['id'],
                        'title': chunk['title'],
                        'chunk_number': chunk['chunk_number']
                    })
                    metadatas_to_index.append(metadata)
                    ids_to_index.append(f"{file_path}_{chunk['id']}")
                
            else:  # JSON et autres formats
                documents_to_index = [document_data['content']]
                metadatas_to_index = [document_data['metadata']]
                ids_to_index = [file_path]
            
            # Ajout à ChromaDB
            if documents_to_index:
                self.vector_store.add_documents(
                    documents=documents_to_index,
                    metadatas=metadatas_to_index,
                    ids=ids_to_index
                )
                self.logger.info(f"✅ Document indexé: {file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur indexation {file_path}: {e}")
    
    
    async def query(self, question: str, context: str = None, n_results: int = 5) -> List[Dict]:
        """Interroge la base de connaissances - VERSION FLEXIBLE"""
        try:
            # Si contexte spécifié, essayer avec filtre, sinon sans filtre
            if context:
                # Essayer d'abord avec le filtre
                results = self.vector_store.search(
                    query=question,
                    n_results=n_results,
                    filter_metadata={"context": context}
                )
                # Si aucun résultat avec filtre, essayer sans filtre
                if len(results) == 0:
                    self.logger.info(f"🔍 Aucun résultat avec filtre '{context}', recherche sans filtre")
                    
                    results = self.vector_store.search(
                        query=question,
                        n_results=n_results,    
                    )
            else:
                # Recherche sans filtre
                results = self.vector_store.search(
                    query=question,
                    n_results=n_results,
                )
        
            self.logger.info(f"🔍 Recherche: '{question}' → {len(results)} résultats")
            return results
        
        except Exception as e:  
            self.logger.error(f"❌ Erreur recherche: {e}")
            return []

   
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système RAG"""
        vector_stats = self.vector_store.get_collection_stats()
        
        return {
            "vector_store": vector_stats,
            "embedding_model": self.embeddings.model_name,
            "status": "active"
        }