import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types
from tools.rag.rag_tool import RAGTool
import logging

class RAGSearchAgent:
    """Specialized agent for RAG search operations"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
        self.rag_tool = RAGTool()
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("GOOGLE_API_KEY")
    
    def get_agent(self):
        """Returns the search agent"""
        return Agent(
            name="RAGSearchAgent",
            model=Gemini(model="gemini-2.5-flash-lite", api_key=self.api_key, retry_options=self.retry_config),
            instruction="""You are a RAG search specialist. Your ONLY job is to:
            1. Analyze the user query to determine the most relevant search context
            2. Use the query_knowledge_base tool to search the knowledge base
            3. Return the raw search results with metadata
            
            Available contexts: 
            - products (technical specs, error codes E01-E99, manuals)
            - support (customer service policies, refund rules)
            - technical (mapped to products)
            - hr (leave policies)
            - internal (IT workflows)
            
            Focus on finding the most relevant information. For error codes, ALWAYS use 'products'.""",
            tools=[self.rag_tool.get_tool()],
            output_key="search_results"
        )

class RAGContextAgent:
    """Specialized agent for context analysis and filtering"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
        self.api_key = os.getenv("GOOGLE_API_KEY")
    
    def get_agent(self):
        """Returns the context agent"""
        return Agent(
            name="RAGContextAgent", 
            model=Gemini(model="gemini-2.5-flash-lite", api_key=self.api_key, retry_options=self.retry_config),
            instruction="""You are a RAG context analyst. Your ONLY job is to:
            1. Analyze the search results in {search_results}
            2. Filter and rank the most relevant information
            3. Extract key facts, procedures, and solutions
            4. Structure the information for easy consumption
            5. Return a clean, organized context summary
            
            Do NOT answer the original question - just prepare the best context.""",
            output_key="filtered_context"
        )

class RAGResponseAgent:
    """Specialized agent for generating final responses"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
        self.api_key = os.getenv("GOOGLE_API_KEY")
    
    def get_agent(self):
        """Returns the response agent"""
        return Agent(
            name="RAGResponseAgent",
            model=Gemini(model="gemini-2.5-flash-lite", api_key=self.api_key, retry_options=self.retry_config),
            instruction="""You are a RAG response specialist. Your ONLY job is to:
            1. Use the filtered context in {filtered_context}
            2. Answer the user's original question clearly and accurately
            3. Cite specific information from the context
            4. Provide step-by-step solutions when applicable
            5. Return a helpful, professional response
            
            Always base your answer strictly on the provided context.""",
            output_key="final_response"
        )