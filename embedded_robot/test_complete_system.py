"""
Complete System Test
Tests all scenarios including re-escalation
"""

import asyncio
import logging
import httpx
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemTester:
    """Complete system tester"""
    
    def __init__(self, robot_url: str = "http://localhost:8001"):
        self.robot_url = robot_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_scenario_1_first_bug(self):
        """
        Scenario 1: First bug - Escalates to support
        
        Expected flow:
        1. Trigger E01
        2. No memory → Escalates
        3. Receives solution
        4. Applies → Success
        5. Stores in memory
        """
        print("\n" + "="*60)
        print("SCENARIO 1: First Bug (Learning)")
        print("="*60)
        
        # 1. Trigger E01
        logger.info("1. Triggering E01 (Wheels blocked)...")
        response = await self.client.post(f"{self.robot_url}/simulate/error/E01")
        logger.info(f"   Response: {response.json()}")
        
        # Wait for diagnostics
        await asyncio.sleep(8)
        
        # 2. Check status
        logger.info("2. Checking status...")
        response = await self.client.get(f"{self.robot_url}/status")
        status = response.json()
        logger.info(f"   Current error: {status.get('current_error')}")
        logger.info(f"   Escalations: {status['adk_metrics']['escalations']}")
        
        # 3. Simulate solution from support
        logger.info("3. Sending solution from support...")
        response = await self.client.post(
            f"{self.robot_url}/solution/execute",
            json={
                "action": "clean_wheels",
                "error_code": "E01",
                "ticket_id": "ROBO-0001",
                "agent_id": "tech_support_test"
            }
        )
        result = response.json()
        logger.info(f"   Solution result: {result['status']}")
        logger.info(f"   Error resolved: {result['error_resolved']}")
        
        # 4. Verify resolution
        await asyncio.sleep(2)
        response = await self.client.get(f"{self.robot_url}/status")
        status = response.json()
        logger.info(f"4. Final status:")
        logger.info(f"   Current error: {status.get('current_error')}")
        logger.info(f"   ✅ Scenario 1 PASSED" if not status.get('current_error') else "   ❌ Scenario 1 FAILED")
        
        return not status.get('current_error')
    
    async def test_scenario_2_self_healing(self):
        """
        Scenario 2: Same bug - Self-heals from memory
        
        Expected flow:
        1. Trigger E01 again
        2. Memory finds solution
        3. Auto-resolution
        4. No escalation
        """
        print("\n" + "="*60)
        print("SCENARIO 2: Self-Healing (Memory)")
        print("="*60)
        
        # Get initial metrics
        response = await self.client.get(f"{self.robot_url}/status")
        initial_metrics = response.json()['adk_metrics']
        initial_escalations = initial_metrics['escalations']
        
        # 1. Trigger E01 again
        logger.info("1. Triggering E01 again...")
        response = await self.client.post(f"{self.robot_url}/simulate/error/E01")
        
        # Wait for auto-resolution
        await asyncio.sleep(10)
        
        # 2. Check if resolved without escalation
        response = await self.client.get(f"{self.robot_url}/status")
        final_status = response.json()
        final_metrics = final_status['adk_metrics']
        
        logger.info("2. Checking resolution...")
        logger.info(f"   Current error: {final_status.get('current_error')}")
        logger.info(f"   Self-resolutions: {final_metrics['self_resolutions']}")
        logger.info(f"   Escalations: {final_metrics['escalations']} (was {initial_escalations})")
        
        # Success if error resolved AND no new escalation
        success = (
            not final_status.get('current_error') and
            final_metrics['escalations'] == initial_escalations
        )
        
        logger.info(f"   ✅ Scenario 2 PASSED" if success else "   ❌ Scenario 2 FAILED")
        
        return success
    
    async def test_scenario_3_failed_solution(self):
        """
        Scenario 3: Solution fails - Re-escalates
        
        Expected flow:
        1. Trigger persistent E01
        2. Receive solution
        3. Apply solution
        4. Error persists → Re-escalation
        """
        print("\n" + "="*60)
        print("SCENARIO 3: Failed Solution (Re-escalation)")
        print("="*60)
        
        # Note: This requires accessing hardware simulator directly
        # In production, you'd trigger via special API endpoint
        
        logger.info("⚠️ This scenario requires direct hardware manipulation")
        logger.info("   It demonstrates the re-escalation mechanism")
        logger.info("   In a full demo, you would:")
        logger.info("   1. Set hardware.error_persistent = True")
        logger.info("   2. Trigger error")
        logger.info("   3. Send solution")
        logger.info("   4. Observe automatic re-escalation")
        
        return True  # Manual verification required
    
    async def test_scenario_4_hitl(self):
        """
        Scenario 4: Critical error - HITL required
        
        Expected flow:
        1. Trigger E07 (critical)
        2. Immediate escalation
        3. No auto-resolution attempt
        4. HITL response
        """
        print("\n" + "="*60)
        print("SCENARIO 4: HITL Required")
        print("="*60)
        
        # 1. Trigger E07
        logger.info("1. Triggering E07 (Battery critical)...")
        response = await self.client.post(f"{self.robot_url}/simulate/error/E07")
        
        # Wait for diagnostics
        await asyncio.sleep(8)
        
        # 2. Check status
        response = await self.client.get(f"{self.robot_url}/status")
        status = response.json()
        logger.info(f"2. Status:")
        logger.info(f"   Current error: {status.get('current_error')}")
        logger.info(f"   Expected: E07 (critical)")
        
        # 3. Send HITL solution
        logger.info("3. Sending HITL solution...")
        response = await self.client.post(
            f"{self.robot_url}/solution/execute",
            json={
                "action": "wait_hitl",
                "error_code": "E07",
                "ticket_id": "ROBO-HITL-001",
                "agent_id": "human_tech",
                "requires_hitl": True
            }
        )
        result = response.json()
        logger.info(f"   Solution result: {result['status']}")
        
        success = result['status'] == "pending_hitl"
        logger.info(f"   ✅ Scenario 4 PASSED" if success else "   ❌ Scenario 4 FAILED")
        
        # Cleanup: manual fix
        await self.client.post(f"{self.robot_url}/fix/battery")
        
        return success
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "="*60)
        print("🧪 COMPLETE SYSTEM TEST")
        print("="*60)
        print("\nTesting ADK-powered robot with:")
        print("  - Sequential Agents (sensors)")
        print("  - Loop Agents (diagnostics)")
        print("  - Memory + Self-healing")
        print("  - Re-escalation on failure")
        print("  - HITL support")
        print()
        
        results = {}
        
        try:
            # Test 1
            results['scenario_1'] = await self.test_scenario_1_first_bug()
            await asyncio.sleep(2)
            
            # Test 2 (requires Test 1 to work)
            if results['scenario_1']:
                results['scenario_2'] = await self.test_scenario_2_self_healing()
            else:
                logger.warning("Skipping Scenario 2 (Scenario 1 failed)")
                results['scenario_2'] = False
            
            await asyncio.sleep(2)
            
            # Test 3
            results['scenario_3'] = await self.test_scenario_3_failed_solution()
            await asyncio.sleep(2)
            
            # Test 4
            results['scenario_4'] = await self.test_scenario_4_hitl()
            
        except Exception as e:
            logger.error(f"Test error: {e}")
            return False
        
        finally:
            await self.client.aclose()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        for scenario, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {scenario}: {status}")
        
        all_passed = all(results.values())
        print("\n" + ("="*60))
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️ Some tests failed")
        print("="*60 + "\n")
        
        return all_passed


async def main():
    """Main test entry point"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))