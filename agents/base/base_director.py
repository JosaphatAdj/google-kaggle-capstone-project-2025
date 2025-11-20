"""
Base Director - Foundation for division directors
Manages multiple agents within a division (Support, Marketing, HR)
"""

from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)


class BaseDirector(BaseAgent):
    """
    Base class for division directors
    
    A Director is a special agent that:
    - Manages multiple agents in their division
    - Routes tasks to appropriate agents
    - Monitors division performance
    - Reports to COO Agent
    
    Usage:
        class SupportDirector(BaseDirector):
            def __init__(self):
                super().__init__(
                    agent_id="support_director_001",
                    agent_type="support_director",
                    department="support"
                )
                
                # Register managed agents
                self.register_agent(self.ticket_router)
                self.register_agent(self.faq_agent)
                self.register_agent(self.technical_support)
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        model_name: str = "gemini-2.0-flash-exp",
        instruction: Optional[str] = None
    ):
        """
        Initialize director
        
        Args:
            agent_id: Director's unique ID
            agent_type: Type (e.g., "support_director")
            department: Division name
            model_name: Gemini model
            instruction: Director instructions
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            department=department,
            model_name=model_name,
            instruction=instruction or self._get_director_instruction()
        )
        
        # Managed agents registry
        self.managed_agents: Dict[str, BaseAgent] = {}
        
        # Division metrics
        self.division_metrics = {
            "total_agents": 0,
            "active_agents": 0,
            "total_tasks": 0,
            "division_load": 0.0
        }
        
        logger.info(f"✅ Director initialized: {self.agent_id} (Division: {self.department})")
    
    def _get_director_instruction(self) -> str:
        """Get default director instruction"""
        return f"""You are the {self.department} division director.

Your responsibilities:
- Route incoming tasks to appropriate agents in your division
- Monitor agent performance and load
- Escalate complex issues to COO Agent
- Generate division performance reports
- Ensure efficient task distribution

Always prioritize:
1. Task urgency
2. Agent specialization
3. Agent current load
4. Quality of service
"""
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent under this director
        
        Args:
            agent: Agent to register
        """
        self.managed_agents[agent.agent_id] = agent
        self.division_metrics["total_agents"] += 1
        self.division_metrics["active_agents"] += 1
        
        logger.info(
            f"✅ Agent registered under {self.agent_id}: "
            f"{agent.agent_id} ({agent.agent_type})"
        )
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent
        
        Args:
            agent_id: ID of agent to unregister
        """
        if agent_id in self.managed_agents:
            del self.managed_agents[agent_id]
            self.division_metrics["active_agents"] -= 1
            logger.info(f"✅ Agent unregistered: {agent_id}")
        else:
            logger.warning(f"⚠️ Agent not found: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get a managed agent by ID
        
        Args:
            agent_id: Agent's ID
        
        Returns:
            Agent instance or None
        """
        return self.managed_agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all managed agents
        
        Returns:
            List of agent info dictionaries
        """
        return [
            {
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "metrics": agent.get_metrics()
            }
            for agent in self.managed_agents.values()
        ]
    
    def route_task(
        self,
        task: Dict[str, Any]
    ) -> Optional[str]:
        """
        Route a task to appropriate agent
        Override in subclass for custom routing logic
        
        Args:
            task: Task dictionary
        
        Returns:
            Agent ID to route to, or None if no suitable agent
        """
        # Default: round-robin
        if not self.managed_agents:
            logger.warning("⚠️ No agents available for routing")
            return None
        
        # Find least loaded agent
        best_agent = None
        min_load = float('inf')
        
        for agent_id, agent in self.managed_agents.items():
            metrics = agent.get_metrics()
            total_tasks = metrics["metrics"]["tasks_processed"]
            
            if total_tasks < min_load:
                min_load = total_tasks
                best_agent = agent_id
        
        return best_agent
    
    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process task by routing to appropriate agent
        
        Args:
            task_description: Task description
            context: Additional context
        
        Returns:
            Result dictionary
        """
        import time
        start_time = time.time()
        
        try:
            # Create task dict
            task = {
                "description": task_description,
                "context": context or {}
            }
            
            # Route to agent
            agent_id = self.route_task(task)
            
            if not agent_id:
                return {
                    "status": "failed",
                    "error": "No available agent"
                }
            
            agent = self.get_agent(agent_id)
            
            logger.info(
                f"📋 Routing task to {agent_id}: {task_description[:50]}..."
            )
            
            # Process with agent
            result = await agent.process_task(task_description, context)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.update_metrics(
                success=result.get("status") == "success",
                processing_time=processing_time
            )
            self.division_metrics["total_tasks"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Director task processing failed: {e}")
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_division_metrics(self) -> Dict[str, Any]:
        """
        Get complete division metrics
        
        Returns:
            Division metrics including all agents
        """
        # Calculate division load
        if self.division_metrics["active_agents"] > 0:
            total_load = sum(
                agent.metrics["tasks_processed"]
                for agent in self.managed_agents.values()
            )
            self.division_metrics["division_load"] = (
                total_load / self.division_metrics["active_agents"]
            )
        
        return {
            "director_id": self.agent_id,
            "department": self.department,
            "division_metrics": self.division_metrics,
            "agents": self.list_agents()
        }
    
    def generate_report(self) -> str:
        """
        Generate division performance report
        
        Returns:
            Report string
        """
        metrics = self.get_division_metrics()
        
        report = f"""
{'='*60}
DIVISION PERFORMANCE REPORT
{'='*60}

Director: {metrics['director_id']}
Department: {metrics['department']}

Division Metrics:
- Total Agents: {metrics['division_metrics']['total_agents']}
- Active Agents: {metrics['division_metrics']['active_agents']}
- Total Tasks: {metrics['division_metrics']['total_tasks']}
- Average Load: {metrics['division_metrics']['division_load']:.2f}

Agent Details:
"""
        
        for agent_info in metrics['agents']:
            agent_metrics = agent_info['metrics']['metrics']
            report += f"""
  - {agent_info['agent_id']} ({agent_info['agent_type']})
    Tasks: {agent_metrics['tasks_processed']} 
    Success: {agent_metrics['tasks_succeeded']}
    Failed: {agent_metrics['tasks_failed']}
"""
        
        report += f"\n{'='*60}\n"
        
        return report


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    # Example director with agents
    class ExampleDirector(BaseDirector):
        def __init__(self):
            super().__init__(
                agent_id="example_director_001",
                agent_type="example_director",
                department="test"
            )
    
    # Example agents
    class Agent1(BaseAgent):
        def __init__(self):
            super().__init__(
                agent_id="agent_001",
                agent_type="worker",
                department="test"
            )
        
        async def process_task(self, task_description: str, context=None):
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "result": f"Processed: {task_description}"
            }
    
    class Agent2(BaseAgent):
        def __init__(self):
            super().__init__(
                agent_id="agent_002",
                agent_type="worker",
                department="test"
            )
        
        async def process_task(self, task_description: str, context=None):
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "result": f"Processed: {task_description}"
            }
    
    async def test():
        print("\n" + "="*60)
        print("TESTING BASE DIRECTOR")
        print("="*60)
        
        # Create director and agents
        director = ExampleDirector()
        agent1 = Agent1()
        agent2 = Agent2()
        
        # Register agents
        director.register_agent(agent1)
        director.register_agent(agent2)
        
        print(f"\n✅ Director created: {director}")
        print(f"   Managed agents: {len(director.managed_agents)}")
        
        # Process tasks
        for i in range(3):
            result = await director.process_task(f"Task {i+1}")
            print(f"\n✅ Task {i+1} result: {result['status']}")
        
        # Generate report
        print(director.generate_report())
        
        print("="*60)
        print("✅ DIRECTOR TEST COMPLETE")
        print("="*60)
    
    asyncio.run(test())