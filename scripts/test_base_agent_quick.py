#!/usr/bin/env python3
"""
Quick test script for BaseAgent
Verifies everything works before running full integration tests
"""

import sys
from pathlib import Path
import asyncio
import logging

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test 1: All imports work"""
    print("\n" + "="*60)
    print("TEST 1: Importing modules")
    print("="*60)
    
    try:
        from agents.base import BaseAgent, BaseDirector, BaseTool
        print("✅ BaseAgent imported")
        
        from security import AuthManager, TokenManager, AuditLog
        print("✅ Security modules imported")
        
        from communication import MessageBus, Message, MessageFactory
        print("✅ Communication modules imported")
        
        from tools.coordinator import CoordinatorTools
        print("✅ Coordinator tools imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_agent():
    """Test 2: BaseAgent creation"""
    print("\n" + "="*60)
    print("TEST 2: Creating BaseAgent")
    print("="*60)
    
    try:
        from agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="test_001",
                    agent_type="test",
                    department="test"
                )
                
                self.add_tool(self.test_function)
            
            def test_function(self, x: int) -> dict:
                return {"result": x * 2}
            
            async def process_task(self, task_description: str, context=None):
                return {"status": "success", "task": task_description}
        
        agent = TestAgent()
        print(f"✅ Agent created: {agent}")
        print(f"   ID: {agent.agent_id}")
        print(f"   Type: {agent.agent_type}")
        print(f"   Tools: {len(agent.get_tools())}")
        
        print("\n✅ BaseAgent test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ BaseAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_operations():
    """Test 3: Async operations"""
    print("\n" + "="*60)
    print("TEST 3: Async operations")
    print("="*60)
    
    try:
        from agents.base import BaseAgent
        
        class AsyncAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="async_001",
                    agent_type="async",
                    department="test"
                )
            
            async def process_task(self, task_description: str, context=None):
                await asyncio.sleep(0.1)  # Simulate work
                return {
                    "status": "success",
                    "task": task_description,
                    "agent_id": self.agent_id
                }
        
        agent = AsyncAgent()
        result = await agent.process_task("Test async task")
        
        print(f"✅ Task processed: {result['status']}")
        print(f"   Agent: {result['agent_id']}")
        
        # Test metrics
        agent.update_metrics(success=True, processing_time=0.1)
        metrics = agent.get_metrics()
        
        print(f"✅ Metrics tracked: {metrics['metrics']['tasks_processed']} tasks")
        
        print("\n✅ Async operations test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Async operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_integration():
    """Test 4: Security integration"""
    print("\n" + "="*60)
    print("TEST 4: Security integration")
    print("="*60)
    
    try:
        from security import AuthManager, TokenManager, AuditLog, ActionType
        
        # Token manager
        tm = TokenManager()
        token = tm.generate_agent_token(
            agent_id="test_agent",
            agent_type="test",
            department="test",
            permissions=["read:test"]
        )
        print("✅ Token generated")
        
        # Validate token
        payload = tm.validate_token(token)
        print(f"✅ Token validated: {payload['agent_id']}")
        
        # Auth manager
        auth = AuthManager(tm)
        agent_token = auth.register_agent(
            agent_id="test_agent_001",
            agent_type="test",
            department="test"
        )
        print("✅ Agent registered")
        
        # Audit log
        audit = AuditLog(log_dir="logs/test")
        audit.log_action(
            action_type=ActionType.AGENT_REGISTERED,
            agent_id="test_agent_001",
            details={"test": True}
        )
        print("✅ Action logged")
        
        print("\n✅ Security integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Security integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinator_tools():
    """Test 5: Coordinator tools"""
    print("\n" + "="*60)
    print("TEST 5: Coordinator tools")
    print("="*60)
    
    try:
        from tools.coordinator import CoordinatorTools
        
        tools = CoordinatorTools()
        
        # Test agent assignment
        assignment = tools.determine_agent_assignment(
            task_description="Robot won't start",
            task_type="technical_issue",
            urgency="high"
        )
        
        print(f"✅ Agent assignment: {assignment['assigned_agent']}")
        print(f"   Reason: {assignment['reason']}")
        print(f"   Confidence: {assignment['confidence']}")
        
        # Test escalation check
        escalation = tools.check_escalation_policy(
            issue_type="battery_swollen",
            sentiment="angry",
            severity="critical"
        )
        
        print(f"✅ Escalation check: escalate={escalation['escalate']}")
        if escalation['escalate']:
            print(f"   Type: {escalation['escalation_type']}")
            print(f"   Reason: {escalation['reason']}")
        
        print("\n✅ Coordinator tools test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Coordinator tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" " * 25 + "🧪 QUICK TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: BaseAgent
    results.append(("BaseAgent", test_base_agent()))
    
    # Test 3: Async operations
    results.append(("Async Operations", await test_async_operations()))
    
    # Test 4: Security
    results.append(("Security Integration", test_security_integration()))
    
    # Test 5: Coordinator tools
    results.append(("Coordinator Tools", test_coordinator_tools()))
    
    # Summary
    print("\n" + "="*80)
    print(" " * 30 + "📊 RESULTS")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("\n" + "="*80)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! System is ready.")
        print("\nNext steps:")
        print("  1. Run full integration tests:")
        print("     pytest tests/integration/test_coo_integration.py")
        print("\n  2. Run demo:")
        print("     python scripts/start_coo_demo.py")
    else:
        print("\n⚠️ Some tests failed. Please fix before proceeding.")
    
    print("="*80 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)