"""
Unit tests for BaseAgent
Tests core functionality following ADK patterns
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.base.base_agent import BaseAgent, BaseTool
from google.adk.tools.function_tool import FunctionTool


class TestAgent(BaseAgent):
    """Test agent implementation"""
    
    def __init__(self):
        super().__init__(
            agent_id="test_agent_001",
            agent_type="test_agent",
            department="test"
        )
        
        # Add tools
        self.add_tool(self.greet)
        self.add_tool(self.calculate)
    
    def greet(self, name: str) -> dict:
        """Greet a user"""
        return {
            "message": f"Hello {name}!",
            "agent_id": self.agent_id
        }
    
    def calculate(self, operation: str, a: float, b: float) -> dict:
        """Perform calculation"""
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else None
        }
        
        return {
            "operation": operation,
            "result": operations.get(operation)
        }
    
    async def process_task(self, task_description: str, context=None):
        """Process task implementation"""
        return {
            "status": "success",
            "task": task_description,
            "agent_id": self.agent_id
        }


class TestBaseAgent:
    """Test suite for BaseAgent"""
    
    def test_agent_initialization(self):
        """Test agent can be initialized"""
        agent = TestAgent()
        
        assert agent.agent_id == "test_agent_001"
        assert agent.agent_type == "test_agent"
        assert agent.department == "test"
        assert agent.model_name == "gemini-2.0-flash-exp"
    
    def test_agent_has_tools(self):
        """Test agent has tools"""
        agent = TestAgent()
        tools = agent.get_tools()
        
        assert len(tools) == 2
        assert all(isinstance(tool, FunctionTool) for tool in tools)
    
    def test_add_tool(self):
        """Test adding tool to agent"""
        agent = TestAgent()
        initial_count = len(agent.get_tools())
        
        def new_tool(x: int) -> dict:
            return {"result": x * 2}
        
        agent.add_tool(new_tool)
        
        assert len(agent.get_tools()) == initial_count + 1
    
    def test_update_instruction(self):
        """Test updating agent instruction"""
        agent = TestAgent()
        new_instruction = "New instructions for testing"
        
        agent.update_instruction(new_instruction)
        
        assert agent.instruction == new_instruction
    
    @pytest.mark.asyncio
    async def test_process_task(self):
        """Test task processing"""
        agent = TestAgent()
        
        result = await agent.process_task("Test task")
        
        assert result["status"] == "success"
        assert result["agent_id"] == agent.agent_id
    
    def test_metrics(self):
        """Test metrics tracking"""
        agent = TestAgent()
        
        # Update metrics
        agent.update_metrics(success=True, processing_time=1.5)
        agent.update_metrics(success=False, processing_time=0.5)
        
        metrics = agent.get_metrics()
        
        assert metrics["metrics"]["tasks_processed"] == 2
        assert metrics["metrics"]["tasks_succeeded"] == 1
        assert metrics["metrics"]["tasks_failed"] == 1
        assert metrics["metrics"]["total_processing_time"] == 2.0
    
    def test_agent_repr(self):
        """Test string representation"""
        agent = TestAgent()
        repr_str = repr(agent)
        
        assert "TestAgent" in repr_str
        assert "test_agent_001" in repr_str


class TestBaseTool:
    """Test suite for BaseTool"""
    
    def test_base_tool_initialization(self):
        """Test BaseTool can be initialized"""
        
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(name="test_tool")
            
            def get_functions(self):
                return [self.test_function]
            
            def test_function(self, x: int) -> dict:
                return {"result": x * 2}
        
        tool = TestTool()
        
        assert tool.name == "test_tool"
        functions = tool.get_functions()
        assert len(functions) == 1
    
    def test_get_function_tools(self):
        """Test getting FunctionTool wrappers"""
        
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(name="test_tool")
            
            def get_functions(self):
                return [self.func1, self.func2]
            
            def func1(self, x: int) -> dict:
                return {"result": x}
            
            def func2(self, y: str) -> dict:
                return {"message": y}
        
        tool = TestTool()
        function_tools = tool.get_function_tools()
        
        assert len(function_tools) == 2
        assert all(isinstance(ft, FunctionTool) for ft in function_tools)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING BASE AGENT TESTS")
    print("="*60)
    
    # Run tests
    pytest.main([__file__, "-v"])