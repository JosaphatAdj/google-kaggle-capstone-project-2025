from typing import Dict, Any
from google.adk.tools.function_tool import FunctionTool
from .rag_tool import RAGTool

class SpecializedRAGTools:
    """Tools RAG spécialisés par département"""
    
    def __init__(self):
        self.rag_tool = RAGTool()
    
    def query_support_knowledge(self, customer_issue: str) -> Dict[str, Any]:
        """
        Tool spécialisé pour le support client - recherche dans la base support.
        
        Args:
            customer_issue: Description du problème client
            
        Returns:
            Résultats de recherche du contexte support
        """
        return self.rag_tool.query_knowledge_base(
            question=customer_issue,
            context="support",
            department="support"
        )
    
    def query_technical_docs(self, technical_issue: str) -> Dict[str, Any]:
        """
        Tool spécialisé pour le support technique - recherche documentation produits.
        
        Args:
            technical_issue: Problème technique ou question
            
        Returns:
            Résultats de recherche technique
        """
        return self.rag_tool.query_knowledge_base(
            question=technical_issue,
            context="products",
            department="technical"
        )
    
    def query_hr_policies(self, hr_question: str) -> Dict[str, Any]:
        """
        Tool spécialisé pour les RH - recherche politiques et procédures.
        
        Args:
            hr_question: Question sur politiques RH ou procédures
            
        Returns:
            Résultats de recherche RH
        """
        return self.rag_tool.query_knowledge_base(
            question=hr_question,
            context="hr",
            department="hr"
        )
    
    def get_support_tool(self) -> FunctionTool:
        return FunctionTool(
            func=self.query_support_knowledge,
            name="query_support_knowledge",
            description="Recherche dans la base de connaissances support client pour résoudre des problèmes clients."
        )
    
    def get_technical_tool(self) -> FunctionTool:
        return FunctionTool(
            func=self.query_technical_docs,
            name="query_technical_docs", 
            description="Recherche dans la documentation technique produits pour le dépannage avancé."
        )
    
    def get_hr_tool(self) -> FunctionTool:
        return FunctionTool(
            func=self.query_hr_policies,
            name="query_hr_policies",
            description="Recherche dans les politiques RH et procédures internes."
        )