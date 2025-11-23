from google.adk.agents import SequentialAgent, Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.genai import types
from .rag_specialized_agents import RAGSearchAgent, RAGContextAgent, RAGResponseAgent

class RAGCoordinatorAgent:
    """Main RAG Coordinator following ADK patterns - Orchestrates RAG workflow"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
        self.search_agent = RAGSearchAgent(retry_config).get_agent()
        self.context_agent = RAGContextAgent(retry_config).get_agent() 
        self.response_agent = RAGResponseAgent(retry_config).get_agent()
        
        # Create sequential workflow: Search → Context → Response
        self.sequential_agent = SequentialAgent(
            name="RAGWorkflow",
            sub_agents=[
                self.search_agent,
                self.context_agent, 
                self.response_agent
            ]
        )
    
    def get_agent(self):
        """Returns the sequential agent for integration"""
        return self.sequential_agent