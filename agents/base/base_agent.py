"""
Base Agent - Foundation for all RoboNest agents
"""

from typing import List, Optional, Dict, Any, Callable
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import logging

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all RoboNest agents
    
    Combines:
    - Google ADK patterns (LlmAgent, FunctionTool, Gemini)
    - OOP structure for code organization
    - Common functionality (auth, logging, metrics)
    
    Usage:
        class TechnicalSupportAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="tech_support_001",
                    agent_type="technical_support",
                    department="support"
                )
                
            def get_tools(self) -> List[FunctionTool]:
                return [
                    FunctionTool(func=self.diagnose_robot),
                    FunctionTool(func=self.create_jira_ticket)
                ]
                
            def diagnose_robot(self, issue_description: str) -> dict:
                # Implementation here
                pass
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        model_name: str = "gemini-2.0-flash-exp",
        instruction: Optional[str] = None,
        tools: Optional[List] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique agent identifier (e.g., "tech_support_001")
            agent_type: Type of agent (e.g., "technical_support")
            department: Department (support, marketing, hr, coordinator)
            model_name: Gemini model to use
            instruction: Agent instructions (prompt)
            tools: List of tools (FunctionTool or raw functions)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.department = department
        self.model_name = model_name
        
        # Retry configuration (from course pattern)
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )
        
        # Create Gemini model
        self.model = Gemini(
            model=model_name,
            retry_options=self.retry_config
        )
        
        # Default instruction if not provided
        self.instruction = instruction or self._get_default_instruction()
        
        # Tools - wrap in FunctionTool if needed
        self._raw_tools = tools or []
        self._wrapped_tools = self._wrap_tools(self._raw_tools)
        
        # Create LlmAgent (ADK pattern)
        self.agent = LlmAgent(
            model=self.model,
            name=self.agent_id,
            instruction=self.instruction,
            tools=self._wrapped_tools
        )
        
        # Metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0
        }
        
        logger.info(f"✅ {self.agent_type} initialized: {self.agent_id}")
    
    def _get_default_instruction(self) -> str:
        """
        Get default instruction based on agent type
        Override in subclass for custom instructions
        """
        return f"""You are a {self.agent_type} agent in the RoboNest multi-agent system.
Your role is to handle tasks efficiently and professionally.
Always use the provided tools when needed.
Escalate to human when uncertain or dealing with critical issues."""
    
    def _wrap_tools(self, tools: List) -> List[FunctionTool]:
        """
        Wrap raw functions in FunctionTool if needed
        
        Args:
            tools: List of tools (can be FunctionTool or raw functions)
        
        Returns:
            List of FunctionTool objects
        """
        wrapped = []
        
        for tool in tools:
            if isinstance(tool, FunctionTool):
                # Already wrapped
                wrapped.append(tool)
            elif callable(tool):
                # Raw function - wrap it
                wrapped.append(FunctionTool(func=tool))
            else:
                logger.warning(f"⚠️ Unknown tool type: {type(tool)}")
        
        return wrapped
    
    def add_tool(self, tool: Callable):
        """
        Add a tool to the agent
        
        Args:
            tool: Function to add as tool
        """
        wrapped = FunctionTool(func=tool)
        self._wrapped_tools.append(wrapped)
        
        # Recreate agent with new tools
        self.agent = LlmAgent(
            model=self.model,
            name=self.agent_id,
            instruction=self.instruction,
            tools=self._wrapped_tools
        )
        
        logger.info(f"✅ Tool added: {tool.__name__}")
    
    def get_tools(self) -> List[FunctionTool]:
        """
        Get agent's tools
        Override in subclass to define custom tools
        
        Returns:
            List of FunctionTool objects
        """
        return self._wrapped_tools
    
    def update_instruction(self, new_instruction: str):
        """
        Update agent instructions
        
        Args:
            new_instruction: New instruction string
        """
        self.instruction = new_instruction
        
        # Recreate agent
        self.agent = LlmAgent(
            model=self.model,
            name=self.agent_id,
            instruction=self.instruction,
            tools=self._wrapped_tools
        )
        
        logger.info(f"✅ Instruction updated for {self.agent_id}")
    
    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a task (to be implemented by subclass)
        
        Args:
            task_description: Description of the task
            context: Additional context
        
        Returns:
            Result dictionary
        """
        raise NotImplementedError("Subclass must implement process_task()")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent metrics
        
        Returns:
            Metrics dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "department": self.department,
            "metrics": self.metrics
        }
    
    def update_metrics(
        self,
        success: bool,
        processing_time: float
    ):
        """
        Update agent metrics
        
        Args:
            success: Whether task succeeded
            processing_time: Time taken to process (seconds)
        """
        self.metrics["tasks_processed"] += 1
        
        if success:
            self.metrics["tasks_succeeded"] += 1
        else:
            self.metrics["tasks_failed"] += 1
        
        self.metrics["total_processing_time"] += processing_time
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"<{self.__class__.__name__} "
            f"id={self.agent_id} "
            f"type={self.agent_type} "
            f"dept={self.department}>"
        )


class BaseTool:
    """
    Base class for tool implementations
    Follows ADK FunctionTool pattern
    
    Usage:
        class JiraTool(BaseTool):
            def __init__(self):
                super().__init__(name="jira_tool")
                
            def create_ticket(
                self,
                summary: str,
                description: str,
                tool_context: ToolContext
            ) -> dict:
                # Implementation
                return {"ticket_id": "ROBO-123"}
                
            def get_functions(self) -> List[Callable]:
                return [self.create_ticket]
    """
    
    def __init__(self, name: str):
        """
        Initialize base tool
        
        Args:
            name: Tool name
        """
        self.name = name
        logger.info(f"✅ Tool initialized: {name}")
    
    def get_functions(self) -> List[Callable]:
        """
        Get list of tool functions
        Override in subclass
        
        Returns:
            List of callable functions
        """
        raise NotImplementedError("Subclass must implement get_functions()")
    
    def get_function_tools(self) -> List[FunctionTool]:
        """
        Get functions wrapped as FunctionTools
        
        Returns:
            List of FunctionTool objects
        """
        functions = self.get_functions()
        return [FunctionTool(func=func) for func in functions]


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    # Example: Create a simple agent
    class ExampleAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                agent_id="example_001",
                agent_type="example",
                department="test",
                instruction="You are a helpful test agent."
            )
            
            # Add custom tools
            self.add_tool(self.greet)
            self.add_tool(self.calculate)
        
        def greet(self, name: str) -> dict:
            """
            Greet a user
            
            Args:
                name: User's name
            
            Returns:
                Greeting message
            """
            return {
                "message": f"Hello {name}! I'm {self.agent_id}.",
                "agent_type": self.agent_type
            }
        
        def calculate(self, operation: str, a: float, b: float) -> dict:
            """
            Perform a calculation
            
            Args:
                operation: Operation to perform (add, subtract, multiply, divide)
                a: First number
                b: Second number
            
            Returns:
                Calculation result
            """
            operations = {
                "add": a + b,
                "subtract": a - b,
                "multiply": a * b,
                "divide": a / b if b != 0 else None
            }
            
            result = operations.get(operation)
            
            return {
                "operation": operation,
                "a": a,
                "b": b,
                "result": result
            }
        
        async def process_task(
            self,
            task_description: str,
            context: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Process task implementation"""
            import time
            start_time = time.time()
            
            try:
                # Simulate processing
                logger.info(f"Processing task: {task_description}")
                result = {
                    "status": "success",
                    "task": task_description,
                    "agent_id": self.agent_id
                }
                
                processing_time = time.time() - start_time
                self.update_metrics(success=True, processing_time=processing_time)
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Task failed: {e}")
                processing_time = time.time() - start_time
                self.update_metrics(success=False, processing_time=processing_time)
                
                return {
                    "status": "failed",
                    "error": str(e)
                }
    
    # Test the agent
    print("\n" + "="*60)
    print("TESTING BASE AGENT")
    print("="*60)
    
    agent = ExampleAgent()
    
    print(f"\n✅ Agent created: {agent}")
    print(f"   Tools: {len(agent.get_tools())}")
    print(f"   Model: {agent.model_name}")
    
    # Test process_task
    async def test():
        result = await agent.process_task("Test task")
        print(f"\n✅ Task result: {result}")
        
        # Check metrics
        metrics = agent.get_metrics()
        print(f"\n📊 Metrics:")
        print(f"   Tasks processed: {metrics['metrics']['tasks_processed']}")
        print(f"   Tasks succeeded: {metrics['metrics']['tasks_succeeded']}")
    
    asyncio.run(test())
    
    print("\n" + "="*60)
    print("✅ BASE AGENT TEST COMPLETE")
    print("="*60)