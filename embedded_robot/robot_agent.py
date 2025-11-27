"""
Embedded Robot Agent - Simulates robot with self-diagnostics
Runs on the robot hardware (simulated here)
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from enum import Enum
import random
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# MCP HTTP Client helpers
from embedded_robot.mcp_http_client import send_alert_http, poll_solution_http

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Robot error codes"""
    E01 = "Wheels blocked"
    E02 = "Navigation failure"
    E03 = "Charging issues"
    E04 = "Software glitch"
    E05 = "Performance degraded"
    E06 = "Communication error"
    E07 = "Battery swollen - CRITICAL"
    E08 = "Firmware corruption"
    E09 = "Safety sensor failure"


class RobotState(Enum):
    """Robot operational states"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    CHARGING = "charging"
    SHUTDOWN = "shutdown"
    MAINTENANCE = "maintenance"


class SensorSimulator:
    """Simulates robot sensors"""
    
    def __init__(self):
        self.battery_level = 85
        self.temperature = 35
        self.position = {"x": 0, "y": 0}
        self.wheels_blocked = False
        self.navigation_ok = True
        
    def get_readings(self) -> Dict[str, Any]:
        """Get current sensor readings"""
        # Add some random variation
        return {
            "battery_level": max(0, min(100, self.battery_level + random.randint(-2, 2))),
            "temperature": self.temperature + random.uniform(-2, 2),
            "location": self.position.copy()
        }
    
    def simulate_battery_issue(self):
        """Simulate battery overheating"""
        self.temperature = 65
        logger.warning("⚠️ Battery temperature critical!")
    
    def simulate_wheels_blocked(self):
        """Simulate blocked wheels"""
        self.wheels_blocked = True
        logger.warning("⚠️ Wheels blocked!")
    
    def fix_wheels(self):
        """Fix wheels"""
        self.wheels_blocked = False
        logger.info("✅ Wheels fixed")
    
    def cool_down(self):
        """Cool down battery"""
        self.temperature = 35
        logger.info("✅ Temperature normalized")


class EmbeddedRobotAgent:
    """
    Embedded Robot Agent - Runs on robot hardware
    
    Responsibilities:
    1. Monitor sensors continuously
    2. Detect issues via self-diagnostics
    3. Send alerts to Alert Receiver
    4. Receive and execute solutions
    5. Report back success/failure
    """
    
    def __init__(
        self,
        robot_id: str = "XR25-001",
        alert_receiver_url: str = "http://localhost:8000"
    ):
        """
        Initialize robot agent
        
        Args:
            robot_id: Unique robot identifier
            alert_receiver_url: URL of Alert Receiver API
        """
        self.robot_id = robot_id
        self.alert_receiver_url = alert_receiver_url
        
        # Robot state
        self.state = RobotState.IDLE
        self.current_error: Optional[ErrorCode] = None
        self.pending_solution: Optional[Dict] = None
        
        # Sensors
        self.sensors = SensorSimulator()
        
        # Diagnostics
        self.diagnostics_running = True
        self.diagnostic_interval = 5  # seconds
        
        # Alert tracking
        self.last_alert_sent = None
        self.alert_acknowledged = False
        
        logger.info(f"✅ Robot Agent initialized: {self.robot_id}")
    
    async def run_diagnostics(self):
        """
        Continuous diagnostic monitoring
        Runs in background loop
        """
        logger.info("🔍 Diagnostics started")
        
        while self.diagnostics_running:
            try:
                # Get sensor readings
                sensors = self.sensors.get_readings()
                
                # Check for issues
                error = self._detect_issues(sensors)
                
                if error and error != self.current_error:
                    # New error detected
                    self.current_error = error
                    self.state = RobotState.ERROR
                    
                    logger.error(f"❌ Error detected: {error.name} - {error.value}")
                    
                    # Send alert
                    await self._send_alert(error, sensors)
                
                elif not error and self.current_error:
                    # Error resolved
                    logger.info(f"✅ Error {self.current_error.name} resolved")
                    self.current_error = None
                    self.state = RobotState.IDLE
                
                # Wait before next diagnostic
                await asyncio.sleep(self.diagnostic_interval)
                
            except Exception as e:
                logger.error(f"❌ Diagnostic error: {e}")
                await asyncio.sleep(self.diagnostic_interval)
    
    def _detect_issues(self, sensors: Dict[str, Any]) -> Optional[ErrorCode]:
        """
        Detect issues from sensor data
        
        Args:
            sensors: Sensor readings
        
        Returns:
            Error code if issue detected, None otherwise
        """
        # Critical: Battery overheating
        if sensors["temperature"] > 60:
            return ErrorCode.E07
        
        # Wheels blocked
        if self.sensors.wheels_blocked:
            return ErrorCode.E01
        
        # Low battery
        if sensors["battery_level"] < 20:
            return ErrorCode.E03
        
        # Navigation issues
        if not self.sensors.navigation_ok:
            return ErrorCode.E02
        
        return None
    
    async def _send_alert(self, error: ErrorCode, sensors: Dict[str, Any]):
        """
        Send alert to Alert Receiver
        
        Args:
            error: Error code
            sensors: Sensor data
        """
        try:
            # Determine severity
            severity = self._classify_severity(error)
            
            # Build alert payload
            alert_data = {
                "robot_id": self.robot_id,
                "error_code": error.name,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "description": error.value,
                "sensor_data": sensors
            }
            
            logger.info(f"📤 Sending alert: {error.name} ({severity})")
            
            # Send to Alert Receiver MCP endpoint
            content = await send_alert_http(
                robot_id=self.robot_id,
                error_code=error.name,
                severity=severity,
                description=error.value,
                sensors=sensors
            )

            logger.info(f"✅ Alert sent successfully: {content}")
            self.last_alert_sent = alert_data
            self.alert_acknowledged = True

        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")
    
    def _classify_severity(self, error: ErrorCode) -> str:
        """Classify error severity"""
        critical = [ErrorCode.E07, ErrorCode.E08, ErrorCode.E09]
        high = [ErrorCode.E01, ErrorCode.E02]
        
        if error in critical:
            return "critical"
        elif error in high:
            return "high"
        else:
            return "medium"
    
    async def execute_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute solution received from system
        
        Args:
            solution: Solution data
            {
                "action": "shutdown" | "fix_wheels" | "cool_down" | "reboot",
                "details": {...},
                "ticket_id": "ROBO-123"
            }
        
        Returns:
            Execution result
        """
        action = solution.get("action")
        ticket_id = solution.get("ticket_id")
            
        logger.info(f"🔧 Executing solution: {action} (Ticket: {ticket_id})")
        
        try:
            if action == "shutdown":
                await self._shutdown()
                return {"status": "success", "message": "Robot shutting down"}
            
            elif action == "clean_wheels":
                self.sensors.fix_wheels()
                await asyncio.sleep(2)  # Simulate fix time
                return {"status": "success", "message": "Wheels cleaned"}
            
            elif action == "cool_down":
                self.sensors.cool_down()
                await asyncio.sleep(3)
                return {"status": "success", "message": "Battery cooled down"}
            
            elif action == "reboot":
                await self._reboot()
                return {"status": "success", "message": "Robot rebooted"}
            
            elif action == "wait_hitl":
                # Human intervention required
                self.state = RobotState.MAINTENANCE
                return {"status": "pending", "message": "Awaiting human intervention"}
            
            else:
                return {"status": "failed", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"❌ Solution execution failed: {e}")
            return {"status": "failed", "message": str(e)}
    
    async def _shutdown(self):
        """Shutdown robot"""
        logger.warning("⚠️ Initiating shutdown...")
        self.state = RobotState.SHUTDOWN
        self.diagnostics_running = False
        await asyncio.sleep(1)
        logger.info("🛑 Robot shutdown complete")
    
    async def _reboot(self):
        """Reboot robot"""
        logger.info("🔄 Rebooting...")
        await asyncio.sleep(2)
        self.state = RobotState.IDLE
        self.current_error = None
        logger.info("✅ Robot rebooted")
    
    async def report_resolution(self, ticket_id: str, success: bool):
        """
        Report solution result back to system
        
        Args:
            ticket_id: Jira ticket ID
            success: Whether solution worked
        """
        try:
            result_data = {
                "robot_id": self.robot_id,
                "ticket_id": ticket_id,
                "resolved": success,
                "timestamp": datetime.utcnow().isoformat(),
                "final_state": self.state.value
            }
            
            # In real system, would POST to /ticket-resolution endpoint
            logger.info(f"📊 Resolution report: Ticket {ticket_id} - {'✅ Resolved' if success else '❌ Failed'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to report resolution: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current robot status"""
        return {
            "robot_id": self.robot_id,
            "state": self.state.value,
            "current_error": self.current_error.name if self.current_error else None,
            "sensors": self.sensors.get_readings(),
            "diagnostics_running": self.diagnostics_running,
            "last_alert": self.last_alert_sent
        }


# ============================================================
# INTERACTIVE SIMULATOR
# ============================================================

class InteractiveSimulator:
    """Interactive console to trigger robot issues"""
    
    def __init__(self, robot: EmbeddedRobotAgent):
        self.robot = robot
        
    def show_menu(self):
        """Show interactive menu"""
        print("\n" + "="*60)
        print("🤖 ROBOT SIMULATOR - INTERACTIVE CONSOLE")
        print("="*60)
        print("\nCommands:")
        print("  1 - Simulate E01 (Wheels blocked)")
        print("  2 - Simulate E07 (Battery critical - HITL)")
        print("  3 - Fix wheels")
        print("  4 - Cool down battery")
        print("  5 - Show status")
        print("  6 - Trigger random error")
        print("  shutdown - Shutdown robot")
        print("  exit - Exit simulator")
        print("\nCurrent State:", self.robot.state.value)
        print("="*60)
    
    async def run(self):
        """Run interactive console"""
        print("\n🚀 Starting Robot Simulator...")
        print("   Robot ID:", self.robot.robot_id)
        print("   Alert Receiver:", self.robot.alert_receiver_url)
        
        # Start diagnostics in background
        diagnostics_task = asyncio.create_task(self.robot.run_diagnostics())

        # Start solution polling in background
        async def poll_for_solutions():
            """Poll for solutions every 5 seconds"""
            while True:
                try:
                    from embedded_robot.mcp_http_client import poll_solution_http
                    solution = await poll_solution_http(self.robot.robot_id)
                    
                    if solution:
                        print(f"\n💡 Solution received: {solution.get('action')}")
                        await self.robot.execute_solution(solution)
                except Exception as e:
                    # Silently continue on errors
                    print(f"❌ Solution polling failed: {e}")
                    pass
                
                await asyncio.sleep(5)  # Poll every 5 seconds
        
        polling_task = asyncio.create_task(poll_for_solutions())

        
        
        try:
            while True:
                self.show_menu()
                
                # Use async input to avoid blocking event loop
                loop = asyncio.get_event_loop()
                cmd = await loop.run_in_executor(None, lambda: input("\nEnter command: ").strip().lower())
                
                if cmd == "1":
                    print("\n⚠️ Simulating E01: Wheels blocked...")
                    self.robot.sensors.simulate_wheels_blocked()
                    # Manually trigger error detection and alert
                    self.robot.current_error = ErrorCode.E01
                    self.robot.state = RobotState.ERROR
                    sensors = self.robot.sensors.get_readings()
                    await self.robot._send_alert(ErrorCode.E01, sensors)
    
                elif cmd == "2":
                    print("\n🚨 Simulating E07: Battery critical (HITL required)...")
                    self.robot.sensors.simulate_battery_issue()
                    # Manually trigger error detection and alert
                    self.robot.current_error = ErrorCode.E07
                    self.robot.state = RobotState.ERROR
                    sensors = self.robot.sensors.get_readings()
                    await self.robot._send_alert(ErrorCode.E07, sensors)
                    
                elif cmd == "3":
                    print("\n🔧 Fixing wheels...")
                    result = await self.robot.execute_solution({
                        "action": "fix_wheels",
                        "ticket_id": "MANUAL"
                    })
                    print(f"   Result: {result['message']}")
                    
                elif cmd == "4":
                    print("\n❄️ Cooling down battery...")
                    result = await self.robot.execute_solution({
                        "action": "cool_down",
                        "ticket_id": "MANUAL"
                    })
                    print(f"   Result: {result['message']}")
                    
                elif cmd == "5":
                    status = self.robot.get_status()
                    print("\n📊 Robot Status:")
                    print(f"   State: {status['state']}")
                    print(f"   Error: {status['current_error']}")
                    print(f"   Battery: {status['sensors']['battery_level']}%")
                    print(f"   Temperature: {status['sensors']['temperature']:.1f}°C")
                    
                elif cmd == "6":
                    errors = [ErrorCode.E01, ErrorCode.E02, ErrorCode.E04]
                    error = random.choice(errors)
                    print(f"\n🎲 Triggering random error: {error.name}")
                    if error == ErrorCode.E01:
                        self.robot.sensors.simulate_wheels_blocked()
                    
                elif cmd == "shutdown":
                    print("\n🛑 Shutting down robot...")
                    await self.robot._shutdown()
                    break
                    
                elif cmd == "exit":
                    print("\n👋 Exiting simulator...")
                    self.robot.diagnostics_running = False
                    break
                
                await asyncio.sleep(0.5)
                
        finally:
            self.robot.diagnostics_running = False
            diagnostics_task.cancel()
            polling_task.cancel()
            try:
                await diagnostics_task
            except asyncio.CancelledError:
                pass
            try:
                await polling_task
            except asyncio.CancelledError:
                pass

# ============================================================
# MAIN
# ============================================================

async def main():
    """Main entry point"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if Alert Receiver URL provided
    alert_receiver_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        alert_receiver_url = sys.argv[1]
    
    # Create robot
    robot = EmbeddedRobotAgent(
        robot_id="XR25-001",
        alert_receiver_url=alert_receiver_url
    )
    
    # Run interactive simulator
    simulator = InteractiveSimulator(robot)
    await simulator.run()


if __name__ == "__main__":
    asyncio.run(main())
    
