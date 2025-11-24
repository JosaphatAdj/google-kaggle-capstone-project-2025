import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.alert_receiver.alert_receiver_agent import AlertReceiverAgent, RobotAlert, SensorData
from agents.coordinator.coo_agent import COOAgent
from agents.support.technical_support_agent import TechnicalSupportAgent
from communication.message_bus import MessageBus
from security import AuthManager, AuditLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrchestrationTest")

# Mock RAG Tool to avoid loading heavy models
class MockRAGTool:
    def query_knowledge_base(self, question, context, department, max_results=3):
        return "Mocked RAG solution: Use command 'clean_wheels'"
    
    def get_tool(self):
        from google.adk.tools import FunctionTool
        return FunctionTool(func=self.query_knowledge_base)

async def test_orchestration():
    print("\n" + "="*60)
    print("TESTING AGENT ORCHESTRATION (MOCKED RAG)")
    print("="*60)
    
    # 1. Setup Infrastructure
    auth = AuthManager()
    audit = AuditLog(log_dir="logs/test_audit")
    bus = MessageBus(auth, audit)
    await bus.start()
    
    # 2. Initialize Agents
    print("Initializing agents...")
    
    # Patch RAGTool in agents
    with patch('agents.alert_receiver.alert_receiver_agent.RAGTool', side_effect=MockRAGTool), \
         patch('agents.support.technical_support_agent.RAGTool', side_effect=MockRAGTool):
        
        # Alert Receiver
        alert_receiver = AlertReceiverAgent(
            agent_id="alert_receiver_test",
            auth_manager=auth,
            audit_log=audit,
            message_bus=bus
        )
        await alert_receiver.start()
        
        # COO
        coo = COOAgent(
            agent_id="coo_agent_test",
            auth_manager=auth,
            audit_log=audit,
            message_bus=bus
        )
        await coo.start()
        
        # Technical Support
        tech_support = TechnicalSupportAgent(
            agent_id="tech_support_test",
            auth_manager=auth,
            message_bus=bus
        )
        await tech_support.start()
    
    print("All agents started")
    
    # 3. Mock Robot Interaction
    future_result = asyncio.Future()
    
    async def mock_send_solution(robot_id, solution):
        print(f"[MOCK] Sending solution to {robot_id}: {solution}")
        if not future_result.done():
            future_result.set_result(solution)
    
    alert_receiver.send_solution_to_robot = mock_send_solution
    
    # 4. Simulate Alert
    print("\nSimulating Robot Alert...")
    alert = RobotAlert(
        robot_id="XR25-TEST",
        error_code="E01",
        severity="medium",
        description="Wheels blocked",
        sensor_data=SensorData(battery_level=80, temperature=40)
    )
    
    # Process alert
    await alert_receiver.process_alert(alert)
    
    # 5. Wait for Resolution
    print("Waiting for resolution (timeout 20s)...")
    try:
        solution = await asyncio.wait_for(future_result, timeout=20.0)
        print("\nORCHESTRATION SUCCESSFUL!")
        print(f"   Solution received: {solution}")
        
    except asyncio.TimeoutError:
        print("\nORCHESTRATION TIMED OUT")
        print("   Possible causes:")
        print("   - Message bus not routing")
        print("   - Agents not handling messages")
        print("   - LLM too slow")
    
    # Cleanup
    await bus.stop()

if __name__ == "__main__":
    asyncio.run(test_orchestration())
