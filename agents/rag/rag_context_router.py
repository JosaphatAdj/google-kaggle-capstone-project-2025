from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

class RAGContextRouter:
    """Agent spécialisé pour router vers le bon contexte RAG"""
    
    def __init__(self, retry_config: types.HttpRetryOptions):
        self.retry_config = retry_config
    
    def get_agent(self):
        return Agent(
            name="RAGContextRouter",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=self.retry_config),
            instruction="""Analyze the user query and determine the BEST RAG context to search in.
            
            Available contexts:
            - "support": Error codes, customer issues, troubleshooting
            - "products": Technical specifications, manuals, product features  
            - "technical": API documentation, firmware, technical details
            - "hr": HR policies, employee procedures, internal policies
            - "marketing": Content guidelines, SEO, social media
            - "internal": Company procedures, operations, internal docs
            
            Return ONLY the context name, nothing else.
            
            Examples:
            "error code E01" → "support"
            "XR30 battery specs" → "products" 
            "vacation policy" → "hr"
            "API documentation" → "technical"
            """,
            output_key="rag_context"
        )