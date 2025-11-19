import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingsGenerator:
    """Générateur d'embeddings pour documents RoboNest"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger(__name__)
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle d'embedding"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"✅ Modèle d'embedding '{self.model_name}' chargé")
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement modèle: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Génère l'embedding pour un texte"""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"❌ Erreur génération embedding: {e}")
            return []
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère les embeddings pour une liste de textes"""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            self.logger.error(f"❌ Erreur génération batch embeddings: {e}")
            return []