import os
import logging
from typing import List, Dict, Any
import re

class MarkdownLoader:
    """Chargeur spécialisé pour documents Markdown RoboNest"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Charge un fichier Markdown et extrait le contenu structuré"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraction métadonnées basiques
            metadata = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'context': self._extract_context_from_path(file_path)
            }
            
            return {
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement {file_path}: {e}")
            return {}
    
    def _extract_context_from_path(self, file_path: str) -> str:
        """Extrait le contexte du chemin du fichier"""
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
    
    def chunk_document(self, content: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Découpe un document en chunks pour l'indexation"""
        # Séparation par sections Markdown
        sections = re.split(r'\n#+\s+', content)
        
        chunks = []
        chunk_id = 0
        
        for section in sections:
            if not section.strip():
                continue
                
            # Détection du titre
            lines = section.split('\n')
            title = lines[0].strip() if lines else "Sans titre"
            text_content = '\n'.join(lines[1:]) if len(lines) > 1 else section
            
            # Découpage en chunks plus petits si nécessaire
            words = text_content.split()
            for i in range(0, len(words), chunk_size):
                chunk_text = ' '.join(words[i:i + chunk_size])
                
                chunks.append({
                    'id': f"chunk_{chunk_id}",
                    'content': f"{title}\n{chunk_text}",
                    'title': title,
                    'chunk_number': chunk_id
                })
                chunk_id += 1
        
        return chunks