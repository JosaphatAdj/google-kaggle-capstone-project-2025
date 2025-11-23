import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.rag.rag_tool import RAGTool

async def test_rag_with_forced_context():
    """Test RAG avec contexte forcé pour debug"""
    print("🧪 Testing RAG with forced contexts...")
    
    rag_tool = RAGTool()
    
    # Test avec différents contextes
    contexts = ["support", "products", "technical"]
    query = "error code E01"
    
    for context in contexts:
        print(f"\n🔍 Testing context: '{context}'")
        
        results = await rag_tool.query_knowledge_base(
            question=query,
            context=context,
            department="test"
        )
        
        print(f"   Status: {results['status']}")
        print(f"   Results: {results['results_count']}")
        
        if results['results']:
            for i, result in enumerate(results['results'][:2]):
                print(f"   {i+1}. {result['content'][:100]}...")
                print(f"      Metadata: {result['metadata']}")

if __name__ == "__main__":
    asyncio.run(test_rag_with_forced_context())