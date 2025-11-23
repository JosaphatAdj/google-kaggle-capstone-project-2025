import logging
from typing import Dict, List, Any, Optional
from google.adk.tools.function_tool import FunctionTool
from rag.rag_engine import RAGEngine

class RAGTool:
    """MCP Tool for querying RoboBrain - Following ADK patterns"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ RAG Tool initialized")
    
    async def query_knowledge_base(self, 
        question: str, 
        context: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query RoboBrain knowledge base to find relevant information.
        
        Args:
            question: The question or query to search for
            context: Search context (support, products, marketing, hr, technical)
            department: Requesting department (for logging)
            
        Returns:
            Dict containing search results and metadata
        """
        try:    
            # Execute RAG query
            if context is not None:
                results = await self.rag_engine.query(
                    question=question,
                    context=context,
                    n_results=5
                )
            else:
                results = await self.rag_engine.query(
                    question=question,
                    n_results=5
                )
            
            # LOGGING RAW RESULTS FOR DEBUGGING
            print(f"🔍 RAW RAG RESULTS (Before formatting): {results}")
            
            # Format results for agent consumption
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result["document"][:4000] + "..." if len(result["document"]) > 4000 else result["document"],
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
            
            print(f"🔍 RAG Query: '{question}' [Context: {context}] → {len(results)} results")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ RAG Tool Error: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "results": []
            }
    
    def get_tool(self) -> FunctionTool:
        """Returns the tool formatted for ADK - CORRECT SIGNATURE"""
        return FunctionTool(
            func=self.query_knowledge_base,  # ✅ Function reference
            # ADK FunctionTool uses different parameter names
           # description="Query RoboBrain knowledge base for information about error codes, support procedures, technical documentation, HR policies, and marketing guides."
        )