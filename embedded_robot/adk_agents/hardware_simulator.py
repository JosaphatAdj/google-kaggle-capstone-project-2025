"""
Hardware Simulator - Simulates robot hardware and sensors
This replaces the old SensorSimulator and ErrorCode classes
"""

import random
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Robot error codes"""
    E01 = "Wheels blocked"
    E02 = "Navigation failure"
    E03 = "Battery low - needs charging"
    E04 = "Software glitch"
    E05 = "Performance degraded"
    E06 = "Communication error"
    E07 = "Battery critical - swollen (HITL REQUIRED)"
    E08 = "Firmware corruption (HITL REQUIRED)"
    E09 = "Safety sensor failure (HITL REQUIRED)"


class HardwareSimulator:
    """
    Simulates robot hardware including sensors and actuators
    
    This is what the ADK agents interact with to:
    - Read sensor values
    - Execute actions
    - Simulate faults
    """
    
    def __init__(self):
        """Initialize hardware simulator"""
        # Sensor state
        self.battery_level = 85.0
        self.temperature = 35.0
        self.wheels_blocked = False
        self.navigation_ok = True
        self.position = {"x": 0.0, "y": 0.0}
        
        # Error state
        self.current_error: Optional[ErrorCode] = None
        self.error_persistent = False  # For testing failed solutions
        
        logger.info("✅ Hardware Simulator initialized")
    
    def get_sensor_readings(self) -> Dict[str, Any]:
        """
        Get all sensor readings
        
        Returns:
            Dictionary with all sensor values
        """
        # Add some realistic variation
        battery_noise = random.uniform(-1, 1)
        temp_noise = random.uniform(-0.5, 0.5)
        
        return {
            "battery_level": max(0, min(100, self.battery_level + battery_noise)),
            "temperature": self.temperature + temp_noise,
            "wheels_blocked": self.wheels_blocked,
            "navigation_ok": self.navigation_ok,
            "position": self.position.copy(),
            "timestamp": "now"  # In production, use actual timestamp
        }
    
    def detect_error(self) -> Optional[ErrorCode]:
        """
        Detect if there's a hardware error
        
        Returns:
            ErrorCode if error detected, None if all OK
        """
        # Check for critical temperature (E07)
        if self.temperature > 60:
            return ErrorCode.E07
        
        # Check for blocked wheels (E01)
        if self.wheels_blocked:
            return ErrorCode.E01
        
        # Check for low battery (E03)
        if self.battery_level < 20:
            return ErrorCode.E03
        
        # Check for navigation issues (E02)
        if not self.navigation_ok:
            return ErrorCode.E02
        
        # If error_persistent flag is set, keep returning current error
        # This simulates a situation where the solution didn't work
        if self.error_persistent and self.current_error:
            return self.current_error
        
        return None
    
    def execute_action(self, action: str, error_code: str = None) -> Dict[str, Any]:
        """
        Execute an action on the hardware
        
        Args:
            action: Action to execute (clean_wheels, cooldown, reboot, etc.)
            error_code: The error being addressed
        
        Returns:
            Execution result
        """
        logger.info(f"⚙️ Executing: {action} (for {error_code})")
        
        # Verify safety
        critical_errors = ["E07", "E08", "E09"]
        if error_code in critical_errors and action not in ["shutdown", "wait_hitl"]:
            return {
                "status": "failed",
                "message": f"Action {action} is unsafe for critical error {error_code}. Shutdown required."
            }
        
        # Execute actions
        if action in ["clean_wheels", "fix_wheels"]:
            return self._execute_clean_wheels()
        
        elif action in ["cooldown", "cool_down"]:
            return self._execute_cooldown()
        
        elif action in ["reboot", "restart"]:
            return self._execute_reboot()
        
        elif action == "shutdown":
            return self._execute_shutdown()
        
        elif action == "wait_hitl":
            return {
                "status": "pending",
                "message": "Robot in safe state, waiting for human intervention"
            }
        
        else:
            return {
                "status": "failed",
                "message": f"Unknown action: {action}"
            }
    
    def _execute_clean_wheels(self) -> Dict[str, Any]:
        """Execute wheel cleaning"""
        if not self.wheels_blocked:
            return {
                "status": "success",
                "message": "Wheels were already clean"
            }
        
        # If error_persistent is True, cleaning won't work (for testing)
        if self.error_persistent:
            logger.warning("⚠️ Wheel cleaning failed - obstruction too severe")
            return {
                "status": "success",  # Action executed
                "message": "Cleaning attempted but obstruction remains",
                "warning": "Error persists after action"
            }
        
        # Normal case: cleaning works
        self.wheels_blocked = False
        self.current_error = None
        
        return {
            "status": "success",
            "message": "Wheels cleaned successfully",
            "steps": [
                "Stop all motors",
                "Reverse wheel rotation",
                "Vibrate wheel assembly",
                "Resume operation"
            ]
        }
    
    def _execute_cooldown(self) -> Dict[str, Any]:
        """Execute battery cooldown"""
        if self.temperature <= 50:
            return {
                "status": "success",
                "message": "Temperature already normal"
            }
        
        # Cooldown works (unless persistent)
        if not self.error_persistent:
            self.temperature = 35.0
            self.current_error = None
        
        return {
            "status": "success",
            "message": "Cooldown procedure initiated",
            "estimated_time_seconds": 180
        }
    
    def _execute_reboot(self) -> Dict[str, Any]:
        """Execute system reboot"""
        # Reboot clears most errors
        if not self.error_persistent:
            self.current_error = None
            self.navigation_ok = True
        
        return {
            "status": "success",
            "message": "Robot rebooted successfully",
            "steps": [
                "Save state",
                "Shutdown subsystems",
                "Clear error flags",
                "Restart",
                "POST check"
            ]
        }
    
    def _execute_shutdown(self) -> Dict[str, Any]:
        """Execute robot shutdown"""
        logger.warning("⚠️ Robot shutting down")
        
        # Clear all errors on shutdown
        self.current_error = None
        self.wheels_blocked = False
        self.temperature = 35.0
        
        return {
            "status": "success",
            "message": "Robot shutdown initiated",
            "requires_restart": True
        }
    
    # ============================================================
    # SIMULATION METHODS (for testing)
    # ============================================================
    
    def simulate_wheels_blocked(self, persistent: bool = False):
        """
        Simulate blocked wheels
        
        Args:
            persistent: If True, solution won't work (for testing failed solutions)
        """
        logger.warning("🎬 Simulating E01: Wheels blocked")
        self.wheels_blocked = True
        self.current_error = ErrorCode.E01
        self.error_persistent = persistent
    
    def simulate_battery_critical(self):
        """Simulate critical battery temperature (HITL required)"""
        logger.error("🎬 Simulating E07: Battery critical (HITL)")
        self.temperature = 65.0
        self.current_error = ErrorCode.E07
    
    def simulate_battery_low(self):
        """Simulate low battery"""
        logger.warning("🎬 Simulating E03: Battery low")
        self.battery_level = 15.0
        self.current_error = ErrorCode.E03
    
    def simulate_navigation_failure(self):
        """Simulate navigation failure"""
        logger.warning("🎬 Simulating E02: Navigation failure")
        self.navigation_ok = False
        self.current_error = ErrorCode.E02
    
    def clear_error(self):
        """Manually clear error (for testing)"""
        logger.info("✅ Manually clearing error")
        self.current_error = None
        self.wheels_blocked = False
        self.temperature = 35.0
        self.battery_level = 85.0
        self.navigation_ok = True
        self.error_persistent = False
    
    def set_error_persistent(self, persistent: bool):
        """
        Set whether current error persists after solution
        
        This is useful for testing the re-escalation flow:
        1. Trigger error
        2. Set persistent = True
        3. Receive solution
        4. Solution "works" but error remains
        5. Automatic re-escalation
        """
        self.error_persistent = persistent
        logger.info(f"🔧 Error persistence: {persistent}")


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🧪 HARDWARE SIMULATOR TEST")
    print("="*60 + "\n")
    
    hw = HardwareSimulator()
    
    # Test 1: Normal sensors
    print("Test 1: Normal Sensors")
    sensors = hw.get_sensor_readings()
    print(f"  Sensors: {sensors}")
    print(f"  Error: {hw.detect_error()}")
    print()
    
    # Test 2: Simulate E01
    print("Test 2: Simulate E01 (Wheels Blocked)")
    hw.simulate_wheels_blocked()
    print(f"  Error: {hw.detect_error()}")
    print(f"  Sensors: {hw.get_sensor_readings()}")
    print()
    
    # Test 3: Fix wheels
    print("Test 3: Fix Wheels")
    result = hw.execute_action("clean_wheels", "E01")
    print(f"  Result: {result}")
    print(f"  Error after fix: {hw.detect_error()}")
    print()
    
    # Test 4: Persistent error (solution fails)
    print("Test 4: Persistent Error (Solution Fails)")
    hw.simulate_wheels_blocked(persistent=True)
    print(f"  Error: {hw.detect_error()}")
    result = hw.execute_action("clean_wheels", "E01")
    print(f"  Result: {result}")
    print(f"  Error after fix: {hw.detect_error()}")  # Still there!
    print()
    
    # Test 5: Critical error (HITL)
    print("Test 5: Critical Error (HITL)")
    hw.clear_error()
    hw.simulate_battery_critical()
    print(f"  Error: {hw.detect_error()}")
    result = hw.execute_action("clean_wheels", "E07")  # Should fail
    print(f"  Unsafe action result: {result}")
    result = hw.execute_action("shutdown", "E07")  # Should work
    print(f"  Safe action result: {result}")
    print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)