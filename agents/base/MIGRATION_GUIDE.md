# 🔄 Migration Guide - BaseAgent Implementation

## Overview

BaseAgent is now implemented following **Google ADK patterns** from the Kaggle 5-day course, with **OOP extensions** for better code organization.

---

## ✅ What Changed

### Before (Empty BaseAgent)
```python
# agents/base/base_agent.py was empty
class BaseAgent:
    pass
```

### After (ADK-Compatible BaseAgent)
```python
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.function_tool import FunctionTool

class BaseAgent:
    """
    Wraps LlmAgent with:
    - OOP structure for organization
    - Common functionality (metrics, logging)
    - Tool management
    - Authentication integration
    """
    
    def __init__(self, agent_id, agent_type, department, ...):
        # Creates LlmAgent internally
        self.agent = LlmAgent(
            model=Gemini(model="gemini-2.0-flash-exp"),
            name=agent_id,
            instruction=instruction,
            tools=wrapped_tools
        )
```

---

## 🔧 How to Create Agents Now

### Pattern 1: Simple Agent

```python
from agents.base import BaseAgent
from google.adk.tools.function_tool import FunctionTool

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_001",
            agent_type="my_agent",
            department="support",
            instruction="You are a helpful agent..."
        )
        
        # Add tools
        self.add_tool(self.my_function)
    
    def my_function(self, param: str) -> dict:
        """
        Tool function - automatically wrapped in FunctionTool
        
        Args:
            param: Description
        
        Returns:
            Result dictionary
        """
        return {"result": f"Processed: {param}"}
    
    async def process_task(self, task_description: str, context=None):
        """
        Required: Implement task processing logic
        """
        # Your logic here
        return {"status": "success"}
```

### Pattern 2: Agent with External Tools

```python
from agents.base import BaseAgent
from tools.rag.rag_tool import RAGTool

class TechnicalSupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="tech_support_001",
            agent_type="technical_support",
            department="support"
        )
        
        # Initialize external tools
        self.rag_tool = RAGTool()
        
        # Add tool functions
        self.add_tool(self.diagnose_robot)
        self.add_tool(self.create_jira_ticket)
    
    def diagnose_robot(self, issue_description: str) -> dict:
        """
        Diagnose robot issue using RAG
        
        Args:
            issue_description: User's description of the issue
        
        Returns:
            Diagnosis and recommended actions
        """
        # Query RAG for troubleshooting
        rag_result = self.rag_tool.query_knowledge_base(
            question=f"How to diagnose: {issue_description}",
            context="support",
            department="technical"
        )
        
        return {
            "diagnosis": "Analysis from RAG...",
            "recommended_actions": ["Step 1", "Step 2"]
        }
```

### Pattern 3: Director (Manages Multiple Agents)

```python
from agents.base import BaseDirector

class SupportDirector(BaseDirector):
    def __init__(self):
        super().__init__(
            agent_id="support_director_001",
            agent_type="support_director",
            department="support"
        )
        
        # Create and register agents
        self.ticket_router = TicketRouterAgent()
        self.faq_agent = FAQAgent()
        self.tech_support = TechnicalSupportAgent()
        
        self.register_agent(self.ticket_router)
        self.register_agent(self.faq_agent)
        self.register_agent(self.tech_support)
    
    def route_task(self, task: dict) -> str:
        """
        Override: Custom routing logic
        """
        if "error" in task["description"].lower():
            return self.tech_support.agent_id
        else:
            return self.faq_agent.agent_id
```

---

## 🔄 Updating Existing Agents

### COO Agent (Already Updated)

The COO Agent has been updated to inherit from BaseAgent. Key changes:

```python
# OLD (manual implementation)
class COOAgent:
    def __init__(self, ...):
        self.agent_id = agent_id
        self.agent_type = "coordinator"
        # Manual setup...

# NEW (BaseAgent inheritance)
class COOAgent(BaseAgent):
    def __init__(self, auth_manager=None, ...):
        # BaseAgent handles LlmAgent setup
        super().__init__(
            agent_id="coo_agent_001",
            agent_type="coordinator",
            department="coordinator",
            instruction="You are the COO Agent..."
        )
        
        # Add custom functionality
        self.auth_manager = auth_manager
        self.coordinator_tools = CoordinatorTools()
```

### Division Agents (TODO)

Update each division agent to follow the pattern:

```python
# agents/support/technical_support_agent.py
from agents.base import BaseAgent
from tools.rag.rag_tool import RAGTool
from tools.jira.jira_tool import JiraTool

class TechnicalSupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="tech_support_001",
            agent_type="technical_support",
            department="support",
            instruction="""You are a technical support specialist.

Your responsibilities:
- Diagnose hardware and software issues
- Provide step-by-step troubleshooting
- Create Jira tickets for complex problems
- Escalate safety issues immediately

Use your tools:
- diagnose_robot: Analyze technical issues
- create_jira_ticket: Create tickets for R&D
- query_rag: Search knowledge base
"""
        )
        
        # Tools
        self.rag_tool = RAGTool()
        self.jira_tool = JiraTool()
        
        # Add functions as tools
        self.add_tool(self.diagnose_robot)
        self.add_tool(self.create_jira_ticket)
    
    def diagnose_robot(self, issue_description: str) -> dict:
        # Implementation
        pass
    
    def create_jira_ticket(self, summary: str, description: str) -> dict:
        # Implementation
        pass
    
    async def process_task(self, task_description: str, context=None):
        # Implementation
        pass
```

---

## 📋 Checklist for New Agents

When creating a new agent, ensure:

- [ ] Inherits from `BaseAgent` or `BaseDirector`
- [ ] Calls `super().__init__()` with proper parameters
- [ ] Defines clear `instruction` in English
- [ ] Tools are added with `self.add_tool()`
- [ ] Tool functions have proper docstrings
- [ ] Tool functions return `dict`
- [ ] Implements `async def process_task()`
- [ ] Uses `self.update_metrics()` for tracking
- [ ] Logs important actions with `logger`

---

## 🧪 Testing Your Agent

```python
# Simple test
import asyncio

async def test_my_agent():
    agent = MyAgent()
    
    # Test tools exist
    assert len(agent.get_tools()) > 0
    
    # Test task processing
    result = await agent.process_task("Test task")
    assert result["status"] == "success"
    
    # Check metrics
    metrics = agent.get_metrics()
    print(metrics)

asyncio.run(test_my_agent())
```

---

## 🔗 Integration with Existing Infrastructure

### Security & Authentication

```python
from security import AuthManager

class MyAgent(BaseAgent):
    def __init__(self, auth_manager: AuthManager):
        super().__init__(...)
        self.auth_manager = auth_manager
        
        # Register and get token
        self.token = auth_manager.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            department=self.department
        )
```

### Message Bus Communication

```python
from communication import MessageBus, Message

class MyAgent(BaseAgent):
    def __init__(self, message_bus: MessageBus):
        super().__init__(...)
        self.message_bus = message_bus
    
    async def start(self):
        # Subscribe to topics
        self.message_bus.subscribe(
            topic="tasks.myagent",
            agent_id=self.agent_id,
            token=self.token,
            handler=self.handle_message
        )
    
    async def handle_message(self, message: Message):
        # Process incoming message
        result = await self.process_task(
            message.payload["description"]
        )
```

### RAG Tools

```python
from tools.rag.rag_tool import RAGTool

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.rag_tool = RAGTool()
    
    def my_rag_function(self, query: str) -> dict:
        result = self.rag_tool.query_knowledge_base(
            question=query,
            context="support",
            department=self.department
        )
        return result
```

---

## 🚀 Next Steps

1. **Run Tests**: Verify BaseAgent works
   ```bash
   python agents/base/base_agent.py
   pytest tests/unit/test_agents/test_base_agent.py
   ```

2. **Update Integration Tests**: Fix tests that depend on BaseAgent
   ```bash
   pytest tests/integration/test_coo_integration.py
   ```

3. **Implement Division Agents**: Create support, marketing, HR agents
   - Use BaseAgent pattern
   - Follow English conventions
   - Add proper tools

4. **Test End-to-End**: Run demo
   ```bash
   python scripts/start_coo_demo.py
   ```

---

## 📚 References

- **Google ADK Course**: Day 2b - Agent Tools Best Practices
- **BaseAgent Code**: `agents/base/base_agent.py`
- **BaseDirector Code**: `agents/base/base_director.py`
- **Example Tests**: `tests/unit/test_agents/test_base_agent.py`
- **COO Agent**: `agents/coordinator/coo_agent.py` (reference implementation)

---

## ❓ FAQ

**Q: Can I use French in internal comments?**
A: Yes, but public APIs, docstrings, and messages must be English.

**Q: Do I need to wrap my functions in FunctionTool?**
A: No, `add_tool()` does it automatically.

**Q: Can agents talk to each other directly?**
A: No, use MessageBus for A2A communication.

**Q: Where do I put agent-specific config?**
A: In `config/agents_config.yaml` or agent's `__init__`.

---

**✅ BaseAgent is now ready for production use following ADK best practices!**