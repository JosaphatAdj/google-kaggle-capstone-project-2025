import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from google.adk.runners import InMemoryRunner
from google.genai import types
from agents.rag.rag_coordinator_agent import RAGCoordinatorAgent

async def test_rag_multi_agent():
    """Test the RAG multi-agent system"""
    print("🧪 Testing RAG Multi-Agent System...")
    
    # Configure retry
    retry_config = types.HttpRetryOptions(
        attempts=3,
        exp_base=2, 
        initial_delay=1,
        http_status_codes=[429, 500, 503]
    )
    
    # Create RAG coordinator
    rag_coordinator = RAGCoordinatorAgent(retry_config)
    agent = rag_coordinator.get_agent()
    
    # Create runner
    runner = InMemoryRunner(agent=agent)
    
    # Test query
    test_queries = [
        "What is error code E01 and how to fix it?",
        "Explain the battery maintenance procedure for XR30",
        "What are the HR policies for vacation days?"
    ]
    
    for query in test_queries[:1]:  # Test first query
        print(f"\n🔍 Testing: '{query}'")
        
        response = await runner.run_debug(query, verbose=True)
        
        print(f"✅ RAG Multi-Agent test completed")
        break

if __name__ == "__main__":
    asyncio.run(test_rag_multi_agent())