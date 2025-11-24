"""
Technical Support Agent - Handles robot alerts and resolutions
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from agents.base.base_agent import BaseAgent
from google.adk.tools import FunctionTool
from communication.message_bus import MessageBus, Message
from communication.protocols import MessageFactory, TaskStatus
from security import AuthManager

# Tools
from tools.rag.rag_tool import RAGTool
from tools.jira.jira_tool import create_jira_ticket, update_jira_ticket
from tools.gmail.gmail_tool import send_escalation_email

logger = logging.getLogger(__name__)

class TechnicalSupportAgent(BaseAgent):
    """
    Technical Support Agent specialized in resolving robot issues.
    
    Capabilities:
    - Analyze alerts using RAG (Technical Manuals)
    - Create Jira tickets for tracking
    - Send email notifications
    - Publish solutions back to the system
    """
    
    def __init__(
        self, 
        agent_id: str = "tech_support_001",
        auth_manager: Optional[AuthManager] = None,
        message_bus: Optional[MessageBus] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="technical_support",
            department="support",
            instruction="""
            You are a Technical Support Agent for RoboNest.
            Your goal is to resolve robot alerts efficiently.
            
            When you receive an alert:
            1. Analyze the error code and diagnostics.
            2. Search the Technical Knowledge Base (RAG) for solutions.
            3. If a solution is found:
               - Create a tracking ticket (Jira).
               - Formulate a solution command (e.g., "clean_wheels", "reboot").
            4. If NO solution is found or issue is CRITICAL:
               - Create a high-priority Jira ticket.
               - Escalate to Human in the Loop (HITL) via Email.
               - Solution command should be "wait_hitl".
            
            Always prioritize safety and data integrity.
            """
        )
        
        # Infrastructure
        self.auth_manager = auth_manager or AuthManager()
        self.message_bus = message_bus
        
        # Register with auth
        self.token = self.auth_manager.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            department=self.department
        )
        
        # Initialize RAG tool
        self.rag_tool = RAGTool()
        
        # Add tools
        self.add_tool(self.analyze_issue)
        
        # Add external tools
        self._add_external_tools()
        
    def _add_external_tools(self):
        """Add RAG, Jira, and Gmail tools"""
        # RAG
        self._wrapped_tools.append(self.rag_tool.get_tool())
            
        # Jira (using standalone functions)
        self.add_tool(create_jira_ticket)
        self.add_tool(update_jira_ticket)
            
        # Gmail (using standalone function)
        self.add_tool(send_escalation_email)
            
        # Re-initialize agent with new tools
        self.update_instruction(self.instruction)

    async def start(self):
        """Start the agent and subscribe to topics"""
        if not self.message_bus:
            logger.error("❌ Message bus not configured for Technical Support Agent")
            return
            
        # Subscribe to assigned tasks
        self.message_bus.subscribe(
            topic="task.assigned.technical_support",
            agent_id=self.agent_id,
            token=self.token,
            handler=self._handle_message
        )
        
        logger.info(f"✅ Technical Support Agent started: {self.agent_id}")

    async def _handle_message(self, message: Message):
        """Handle incoming messages"""
        try:
            payload = message.payload
            task_id = payload.get("task_id")
            
            logger.info(f"📥 Received task: {task_id}")
            
            # Process the task
            result = await self.process_task(
                task_description=payload.get("description", ""),
                context=payload.get("context")
            )
            
            # Publish completion
            if self.message_bus:
                completion_msg = Message(
                    sender_id=self.agent_id,
                    topic="task.completed",
                    payload={
                        "task_id": task_id,
                        "status": "completed",
                        "result": result,
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    correlation_id=task_id
                )
                
                await self.message_bus.publish(completion_msg, self.token)
                logger.info(f"✅ Task {task_id} completed and published")
                
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            # Publish failure
            if self.message_bus and message.payload.get("task_id"):
                failure_msg = Message(
                    sender_id=self.agent_id,
                    topic="task.failed",
                    payload={
                        "task_id": message.payload.get("task_id"),
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    correlation_id=message.payload.get("task_id")
                )
                await self.message_bus.publish(failure_msg, self.token)

    async def process_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a technical support task/alert
        """
        logger.info(f"🔧 Processing technical task: {task_description}")
        
        # Run the agent
        # The LLM will use tools to create tickets, query RAG, etc.
        # It should return a summary or specific solution structure.
        agent_response = await self.agent.run(task_description)
        
        # Extract structured solution from agent response or context
        # For now, we assume the agent's text response contains the solution explanation
        # In a real system, we might want the agent to return a structured object via a tool
        
        # Construct a standardized solution object
        solution = {
            "action": "unknown", # Default
            "error_code": context.get("error_code") if context else "UNKNOWN",
            "ticket_id": "PENDING", # Should be extracted from tool outputs if possible
            "agent_id": self.agent_id,
            "details": {
                "explanation": agent_response,
                "timestamp": datetime.utcnow().isoformat()
            },
            "requires_hitl": False
        }
        
        # Simple parsing of response to find action (this could be improved with a specific tool)
        lower_response = agent_response.lower()
        if "clean_wheels" in lower_response:
            solution["action"] = "clean_wheels"
        elif "reboot" in lower_response:
            solution["action"] = "reboot"
        elif "wait_hitl" in lower_response or "escalat" in lower_response:
            solution["action"] = "wait_hitl"
            solution["requires_hitl"] = True
            
        return solution

    def analyze_issue(self, error_code: str, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the issue using internal logic (pre-RAG check)
        """
        logger.info(f"🔍 Analyzing issue {error_code}")
        
        # Simple heuristic check
        severity = "medium"
        if error_code in ["E07", "E08", "E09"]:
            severity = "critical"
        
        return {
            "error_code": error_code,
            "severity": severity,
            "recommendation": "Search RAG for specific solution"
        }
