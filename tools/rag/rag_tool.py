import logging
from typing import Dict, List, Any
from google.adk.tools.function_tool import FunctionTool
from rag.rag_engine import RAGEngine

class RAGTool:
    """Tool MCP pour interroger RoboBrain - Base de connaissances RoboNest"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ RAG Tool initialisé")
    
    def query_knowledge_base(self, 
        question: str, 
        context: str = None,
        department: str = None
    ) -> Dict[str, Any]:
        """
        Interroge la base de connaissances RoboBrain pour trouver des informations pertinentes.
        
        Args:
            question: La question ou requête à rechercher
            context: Contexte de recherche (support, products, marketing, hr, technical)
            department: Département demandeur (pour logging)
            
        Returns:
            Dict contenant les résultats de recherche et métadonnées
        """
        try:
            # Import asynchrone pour l'appel RAG
            import asyncio
            
            # Exécution de la requête RAG
            results = asyncio.run(self.rag_engine.query(
                question=question,
                context=context,
                n_results=5
            ))
            
            # Formatage des résultats pour l'agent
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result["document"][:500] + "..." if len(result["document"]) > 500 else result["document"],
                    "metadata": result["metadata"],
                    "relevance_score": 1 - (result["distance"] if result["distance"] else 0.5)
                })
            
            response = {
                "status": "success",
                "question": question,
                "department": department,
                "context_used": context,
                "results_count": len(results),
                "results": formatted_results
            }
            
            self.logger.info(f"🔍 RAG Query: '{question}' → {len(results)} résultats")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Erreur RAG Tool: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }
    
    def get_tool(self) -> FunctionTool:
        """Retourne le tool formaté pour ADK"""
        return FunctionTool(
            func=self.query_knowledge_base,
            name="query_robo_brain",
            description="""Interroge la base de connaissances RoboBrain pour trouver des informations sur:
            - Codes erreur et dépannage produits
            - Procédures support client  
            - Documentation technique robots
            - Politiques RH et internes
            - Guides marketing et contenu
            Utilisez ce tool quand vous avez besoin d'informations précises depuis la base de connaissances.""",
        )