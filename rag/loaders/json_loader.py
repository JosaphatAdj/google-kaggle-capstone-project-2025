import json
import logging
import os
from typing import List, Dict, Any

class JSONLoader:
    """Chargeur spécialisé pour fichiers JSON structurés"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Charge un fichier JSON et le transforme en texte sémantique"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'context': self._extract_context_from_path(file_path),
                'data_type': 'structured'
            }
            
            # Conversion JSON → texte sémantique
            semantic_content = self._json_to_semantic_text(data, file_path)
            
            return {
                'content': semantic_content,
                'metadata': metadata,
                'raw_data': data
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement JSON {file_path}: {e}")
            return {}
    
    def _json_to_semantic_text(self, data: Any, file_path: str) -> str:
        """Convertit les données JSON en texte sémantique pour l'embedding"""
        
        if 'error_codes' in file_path:
            return self._format_error_codes(data)
        elif 'specs' in file_path:
            return self._format_specs(data)
        elif 'scripts' in file_path:
            return self._format_conversation_scripts(data)
        else:
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_error_codes(self, data: Dict) -> str:
        """Formate les codes erreur en texte sémantique"""
        text = "Codes d'erreur RoboNest:\n\n"
        
        if 'error_codes' in data:
            for code, info in data['error_codes'].items():
                text += f"Code {code}: {info.get('description', '')}\n"
                text += f"Causes: {', '.join(info.get('causes', []))}\n"
                text += f"Résolution: {info.get('resolution', '')}\n"
                text += f"Urgence: {info.get('urgency', '')}\n"
                text += f"Modèles: {', '.join(info.get('models', []))}\n\n"
        
        return text
    
    def _format_specs(self, data: Dict) -> str:
        """Formate les spécifications techniques"""
        text = "Spécifications techniques RoboNest:\n\n"
        
        for product, specs in data.items():
            text += f"Produit: {product}\n"
            for key, value in specs.items():
                text += f"{key}: {value}\n"
            text += "\n"
        
        return text