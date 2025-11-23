from google.adk.agents import SequentialAgent, Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool, FunctionTool
from google.genai import types
from .rag_specialized_agents import RAGSearchAgent, RAGContextAgent, RAGResponseAgent
from .rag_context_router import RAGContextRouter

class RAGCoordinatorAgent:
    """Main RAG Coordinator avec routing de contexte intelligent"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
        self.context_router = RAGContextRouter(retry_config).get_agent()
        self.search_agent = RAGSearchAgent(retry_config).get_agent()
        self.context_agent = RAGContextAgent(retry_config).get_agent() 
        self.response_agent = RAGResponseAgent(retry_config).get_agent()
        
        # Workflow: Router → Search → Context → Response
        self.sequential_agent = SequentialAgent(
            name="RAGWorkflow",
            sub_agents=[
                self.context_router,
                self.search_agent,
                self.context_agent, 
                self.response_agent
            ]
        )
    
    def get_agent(self):
        return self.sequential_agent