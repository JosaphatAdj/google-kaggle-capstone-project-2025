# rag/loaders/json_loader.py
import json
import os
import logging
from typing import Dict, Any

class JSONLoader:
    """Chargeur spécialisé pour documents JSON RoboNest"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Charge un fichier JSON et extrait le contenu structuré"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraction métadonnées basiques
            metadata = {
                'file_path': file_path,
                'language': 'english' if 'english' in file_path else 'french',
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'context': self._extract_context_from_path(file_path),
                'data_type': 'json'
            }
            
            # Convertir les données JSON en texte pour l'indexation
            content = self._json_to_text(data)
            
            return {
                'content': content,
                'metadata': metadata,
                'raw_data': data  # Garder les données brutes pour usage spécifique
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement JSON {file_path}: {e}")
            return {}
    
    def _extract_context_from_path(self, file_path: str) -> str:
        """Extrait le contexte du chemin du fichier (même méthode que MarkdownLoader)"""
        if 'products' in file_path:
            return 'products'
        elif 'support' in file_path:
            return 'support'
        elif 'marketing' in file_path:
            return 'marketing'
        elif 'internal' in file_path:
            if 'hr' in file_path:
                return 'hr'
            elif 'it' in file_path:
                return 'it'
            elif 'security' in file_path:
                return 'security'
            else:
                return 'internal'
        else:
            return 'general'
    
    def _json_to_text(self, data: Any, indent: int = 0) -> str:
        """Convertit les données JSON en texte lisible pour l'indexation"""
        if isinstance(data, dict):
            text_parts = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    nested_text = self._json_to_text(value, indent + 1)
                    text_parts.append(f"{'  ' * indent}{key}:\n{nested_text}")
                else:
                    text_parts.append(f"{'  ' * indent}{key}: {value}")
            return '\n'.join(text_parts)
        
        elif isinstance(data, list):
            text_parts = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    nested_text = self._json_to_text(item, indent + 1)
                    text_parts.append(f"{'  ' * indent}- Item {i + 1}:\n{nested_text}")
                else:
                    text_parts.append(f"{'  ' * indent}- {item}")
            return '\n'.join(text_parts)
        
        else:
            return str(data)
    
    def chunk_document(self, content: str, chunk_size: int = 300) -> list:
        """Découpe le contenu JSON en chunks (compatible avec MarkdownLoader)"""
        # Pour JSON, on découpe par lignes/sections
        lines = content.split('\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line.split())
            
            if current_size + line_size > chunk_size and current_chunk:
                # Sauvegarder le chunk actuel
                chunks.append({
                    'id': f"chunk_{len(chunks)}",
                    'content': '\n'.join(current_chunk),
                    'chunk_number': len(chunks)
                })
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append({
                'id': f"chunk_{len(chunks)}",
                'content': '\n'.join(current_chunk),
                'chunk_number': len(chunks)
            })
        
        return chunks