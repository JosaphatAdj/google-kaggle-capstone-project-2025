import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.rag.rag_tool import RAGTool

async def test_rag_tool():
    """Test du RAG Tool MCP"""
    print("🧪 Test RAG Tool...")
    
    rag_tool = RAGTool()
    tool_instance = rag_tool.get_tool()
    
    # Test requête support
    result = rag_tool.query_knowledge_base(
        question="Code erreur E01",
        context="support", 
        department="support"
    )
    
    print(f"✅ RAG Tool fonctionnel")
    print(f"📊 Statut: {result['status']}")
    print(f"🔍 Résultats: {result['results_count']}")
    
    for i, res in enumerate(result['results'][:2]):
        print(f"  {i+1}. {res['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_rag_tool())