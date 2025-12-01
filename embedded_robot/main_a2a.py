"""
Embedded Robot - A2A Version
Complete robot with Google ADK A2A protocol for communication with support system
PORT 8001
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress Google ADK warnings
import warnings
warnings.filterwarnings('ignore', message='.*EXPERIMENTAL.*')
warnings.filterwarnings('ignore', module='google_adk.*')
warnings.filterwarnings('ignore', module='google_genai.*')
warnings.filterwarnings('ignore', module='a2a.*')

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import FunctionTool
from google.genai import types

# Import our ADK agents
from adk_agents.sensor_agents import create_sensor_sequential_agent
from adk_agents.diagnostic_agent import create_diagnostic_loop_agent
from adk_agents.action_agent import create_action_agent
from adk_agents.hardware_simulator import HardwareSimulator, ErrorCode

logger = logging.getLogger(__name__)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class StatusResponse(BaseModel):
    """Robot status response"""
    robot_id: str
    state: str
    current_error: Optional[str]
    battery_level: int
    temperature: float
    wheels_blocked: bool
    diagnostics_running: bool
    adk_metrics: Dict[str, Any]


# ============================================================
# GLOBAL STATE
# ============================================================

class RobotState:
    """Global robot state managed by ADK agents"""
    
    def __init__(self, robot_id: str = "XR25-001", support_url: str = "http://localhost:8000"):
        self.robot_id = robot_id
        self.support_url = support_url
        
        # Hardware simulator
        self.hardware = HardwareSimulator()
        
        # ADK services
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        
        # Retry config
        self.retry_config = types.HttpRetryOptions(
            attempts=5, exp_base=7, initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )
        
        # Create ADK agents
        self.sensor_agent = create_sensor_sequential_agent(self.retry_config, self.hardware)
        self.diagnostic_agent = create_diagnostic_loop_agent(self.retry_config)
        self.action_agent = create_action_agent(self.retry_config, self.hardware)
        
        # Support Workflow (Sequential + Loop for auto-execution + re-escalation)
        from adk_agents.support_workflow_agent import create_support_workflow_agent
        self.support_workflow_agent = create_support_workflow_agent(
            robot_state=self,
            retry_config=self.retry_config,
            support_url=self.support_url
        )
        
        # Create main orchestrator with remote support
        self.main_agent = self._create_main_agent()
        
        # Create runner
        self.runner = Runner(
            agent=self.main_agent,
            app_name=f"robot_{robot_id}",
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        
        # State tracking
        self.current_error: Optional[ErrorCode] = None
        self.current_ticket_id: Optional[str] = None
        self.diagnostics_running = True
        self.waiting_for_hitl = False
        
        # Solution tracking
        self.error_attempt_count: Dict[str, int] = {}  # error_code -> attempt count
        self.last_failed_solution: Dict[str, str] = {}  # error_code -> failed action
        
        # Metrics
        self.self_resolution_count = 0
        self.escalation_count = 0
        self.failed_solution_count = 0
        
        logger.info(f"✅ Robot State initialized with A2A: {robot_id}")
        logger.info(f"   Support system: {support_url}")
    
    def _create_main_agent(self) -> LlmAgent:
        """Create main orchestrator agent with A2A support"""
        return LlmAgent(
            model=Gemini(model="gemini-2.0-flash-lite", retry_options=self.retry_config),
            name="robot_orchestrator",
            description="Main robot orchestrator with memory, self-healing, and A2A support communication",
            instruction=f"""
You are robot {self.robot_id} orchestrator.

ROUTING (SIMPLE):

1. ERROR E01 → use action_agent sub-agent and execute action "clean_wheels", very important
2. ALL OTHER ERRORS (E02-E09) → use support_workflow sub-agent,very important

That's it. No formatting needed for support_workflow (it handles it automatically).

Just delegate to the right sub-agent based on error code.
            """,
            tools=[
                FunctionTool(self.get_robot_status)
            ],
            sub_agents=[
                self.sensor_agent,
                self.diagnostic_agent,
                self.action_agent,
                self.support_workflow_agent  #  remote_support_agent
            ]
        )
    
    def search_memory(self, error_code: str) -> str:
        """Search memory for solution"""
        logger.info(f"🔍 Searching memory for {error_code}")
        # Simplified for demo
        return f"No solution in memory for {error_code}. Escalate to support."
    
    def attempt_self_resolution(self, solution: str, error_code: str) -> str:
        """Attempt self-resolution"""
        logger.info(f"🔧 Attempting self-resolution: {solution} for {error_code}")
        self.self_resolution_count += 1
        
        result = self.hardware.execute_action(solution, error_code)
        
        success = result["status"] == "success"
        return f"Self-resolution {'' if success else 'failed'}. Result: {result.get('message')}"
    
    def execute_solution_structured(self, solution_data: str) -> str:
        """Execute structured solution received from A2A"""
        import json
        import re
        
        # DEBUG: Log raw input
        logger.info(f"📥 RAW solution received (type={type(solution_data).__name__}):")
        logger.info(f"📥 First 500 chars: {str(solution_data)[:500]}")
        
        try:
            # Parse solution (might be string or already dict)
            if isinstance(solution_data, str):
                # Remove markdown code blocks if present
                if '```json' in solution_data or '```' in solution_data:
                    # Extract content between ```json and ``` or ``` and ```
                    pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
                    match = re.search(pattern, solution_data, re.DOTALL)
                    if match:
                        solution_data = match.group(1).strip()
                        logger.info(f"📝 Extracted JSON from markdown code block")
                
                # Try to extract JSON from response
                if '{' in solution_data and '}' in solution_data:
                    start = solution_data.index('{')
                    end = solution_data.rindex('}') + 1
                    solution = json.loads(solution_data[start:end])
                else:
                    logger.warning(f"⚠️ Could not parse solution, using fallback")
                    return f"Could not parse solution: {solution_data}"
            else:
                solution = solution_data
            
            actions = solution.get('actions', [])
            requires_hitl = solution.get('requires_hitl', False)
            is_temporary = solution.get('is_temporary_solution', False)
            error_code = solution.get('error_code', 'UNKNOWN')
            ticket_id = solution.get('ticket_id', 'UNKNOWN')
            
            logger.info(f"📦 Structured solution: {len(actions)} actions, HITL={requires_hitl}, Temp={is_temporary}")
            
            # Store ticket
            self.current_ticket_id = ticket_id
            
            # Execute all actions in order
            results = []
            for i, action in enumerate(actions, 1):
                logger.info(f"⚙️ Executing action {i}/{len(actions)}: {action}")
                result = self.hardware.execute_action(action, error_code)
                results.append(result)
            
            # If HITL required, enter waiting mode
            if requires_hitl:
                self.waiting_for_hitl = True
                logger.warning(f"⏳ HITL required for {error_code}. Robot waiting for human intervention.")
                if is_temporary:
                    logger.info(f"🔧 Executed {len(actions)} temporary solutions to prevent further damage")
                # Schedule verification but don't re-escalate
                asyncio.create_task(self._verify_solution_hitl(error_code, actions, ticket_id))
            else:
                # Normal solution, verify and potentially re-escalate
                asyncio.create_task(self._verify_solution_with_reescalation(error_code, actions, ticket_id))
            
            return f"✅ Executed {len(actions)} actions. HITL={'WAITING' if requires_hitl else 'NOT REQUIRED'}"
            
        except Exception as e:
            logger.error(f"❌ Error parsing/executing solution: {e}")
            return f"Failed to execute solution: {e}"
    
    def execute_solution(self, action: str, error_code: str, ticket_id: str = "UNKNOWN") -> str:
        """Execute single solution (legacy, for compatibility)"""
        logger.info(f"⚙️ Executing single solution: {action} for {error_code}")
        
        # Store ticket
        self.current_ticket_id = ticket_id
        
        result = self.hardware.execute_action(action, error_code)
        
        # Check if error resolved
        asyncio.create_task(self._verify_solution_with_reescalation(error_code, [action], ticket_id))
        
        return f"Solution '{action}' executed. Status: {result['status']}"
    
    async def _verify_solution_hitl(self, error_code: str, actions: list, ticket_id: str):
        """Verify HITL solution - doesn't re-escalate, just monitors"""
        await asyncio.sleep(5)  # Wait longer for temporary solutions
        
        current_error = self.hardware.detect_error()
        
        if current_error and current_error.name == error_code:
            logger.warning(f"⏳ Error {error_code} still present - waiting for HITL intervention")
            # Don't re-escalate - robot knows it's waiting for human
        else:
            logger.info(f"✅ Temporary solutions resolved {error_code} OR HITL completed")
            self.current_error = None
            self.waiting_for_hitl = False
            # Reset attempt count on success
            if error_code in self.error_attempt_count:
                del self.error_attempt_count[error_code]
    
    async def _verify_solution_with_reescalation(self, error_code: str, actions: list, ticket_id: str):
        """Verify solution and re-escalate if failed (with attempt tracking)"""
        await asyncio.sleep(5)  # Wait for actions to take effect
        
        current_error = self.hardware.detect_error()
        
        if current_error and current_error.name == error_code:
            # Solution failed!
            logger.error(f"❌ Solution {actions} failed to resolve {error_code}")
            self.failed_solution_count += 1
            
            # Track attempt count
            if error_code not in self.error_attempt_count:
                self.error_attempt_count[error_code] = 0
            self.error_attempt_count[error_code] += 1
            
            # Store failed solution
            self.last_failed_solution[error_code] = ", ".join(actions)
            
            attempt_num = self.error_attempt_count[error_code]
            logger.warning(f"📊 Error {error_code} - Attempt #{attempt_num} failed")
            
            if attempt_num >= 2:
                # 2nd failure → HITL obligatoire
                logger.error(f"🚨 2nd failure for {error_code} - HITL NOW REQUIRED")
                await self._reescalate_with_hitl(error_code, actions)
            else:
                # 1st failure → Re-escalate with mention of failure
                logger.warning(f"🔄 1st failure for {error_code} - Re-escalating")
                await self._reescalate_normal(error_code, actions)
        else:
            logger.info(f"✅ Solution {actions} successfully resolved {error_code}")
            self.current_error = None
            # Reset attempt count on success
            if error_code in self.error_attempt_count:
                del self.error_attempt_count[error_code]
    
    async def _reescalate_normal(self, error_code: str, failed_actions: list):
        """Re-escalate after 1st failure"""
        logger.info(f"🔄 Re-escalating {error_code} with failure context")
        
        sensors = self.hardware.get_sensor_readings()
        session_id = f"reescalate_{error_code}_{datetime.now(timezone.utc).timestamp()}"
        
        await self.session_service.create_session(
            app_name=f"robot_{self.robot_id}",
            user_id=self.robot_id,
            session_id=session_id
        )
        
        query = f"""ESCALATION ALERT: Error {error_code} persists after solution attempt.

Previous solution attempted: {', '.join(failed_actions)}
Result: FAILED - Error still present

Current sensor data: Battery {sensors['battery_level']}%, Temperature {sensors['temperature']}°C

This is attempt #1 failure. Please provide alternative solution."""
        
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        
        # Run via main agent (will use remote A2A)
        async for event in self.runner.run_async(
            user_id=self.robot_id,
            session_id=session_id,
            new_message=query_content
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        # Parse and execute new solution
                        self.execute_solution_structured(part.text)
    
    async def _reescalate_with_hitl(self, error_code: str, failed_actions: list):
        """Re-escalate with HITL required (2nd failure)"""
        logger.error(f"🚨 Re-escalating {error_code} - HITL MANDATORY")
        
        self.waiting_for_hitl = True
        
        sensors = self.hardware.get_sensor_readings()
        session_id = f"hitl_{error_code}_{datetime.now(timezone.utc).timestamp()}"
        
        await self.session_service.create_session(
            app_name=f"robot_{self.robot_id}",
            user_id=self.robot_id,
            session_id=session_id
        )
        
        query = f"""CRITICAL ESCALATION: Error {error_code} REQUIRES HUMAN INTERVENTION.

Multiple solution attempts have FAILED:
- Attempt #2 failed: {', '.join(failed_actions)}

Current sensor data: Battery {sensors['battery_level']}%, Temperature {sensors['temperature']}°C

⚠️ HITL REQUIRED - Robot entering safe mode and awaiting human intervention."""
        
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        
        # Run via main agent
        async for event in self.runner.run_async(
            user_id=self.robot_id,
            session_id=session_id,
            new_message=query_content
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        # Execute temporary solutions while waiting for HITL
                        self.execute_solution_structured(part.text)
    
    def get_robot_status(self) -> str:
        """Get current robot status"""
        sensors = self.hardware.get_sensor_readings()
        return f"""Robot {self.robot_id} Status:
- State: {'ERROR' if self.current_error else 'OPERATIONAL'}
- Battery: {sensors['battery_level']}%
- Temperature: {sensors['temperature']}°C
- Wheels: {'BLOCKED' if sensors.get('wheels_blocked') else 'OK'}
- Waiting HITL: {self.waiting_for_hitl}
"""


# Global robot state
robot_state: Optional[RobotState] = None


# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global robot_state
    
    # Startup
    logger.info("🚀 Starting Embedded Robot API (A2A)...")
    robot_state = RobotState(robot_id="XR25-001", support_url="http://localhost:8000")
    
    # Start diagnostics in background
    diagnostics_task = asyncio.create_task(run_diagnostics())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Embedded Robot API...")
    robot_state.diagnostics_running = False
    diagnostics_task.cancel()
    try:
        await diagnostics_task
    except asyncio.CancelledError:
        pass


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="RoboNest Embedded Robot API (A2A)",
    description="ADK-powered robot with A2A protocol for support communication",
    version="3.0.0-A2A",
    lifespan=lifespan
)


# ============================================================
# BACKGROUND DIAGNOSTICS
# ============================================================

async def run_diagnostics():
    """Continuous diagnostics loop using ADK agents"""
    logger.info("🔍 ADK Diagnostics started with A2A support")
    
    while robot_state.diagnostics_running:
        try:
            # Check for errors
            error = robot_state.hardware.detect_error()
            
            if error and error != robot_state.current_error:
                # New error detected
                logger.error(f"❌ Error detected: {error.name} - {error.value}")
                robot_state.current_error = error
                
                # Skip if waiting for HITL
                if robot_state.waiting_for_hitl:
                    logger.info("⏳ Waiting for HITL, skipping auto-handling")
                    await asyncio.sleep(5)
                    continue
                
                # Handle via ADK agents (with A2A escalation)
                await handle_error_with_adk(error)
            
            elif not error and robot_state.current_error:
                # Error resolved
                logger.info(f"✅ Error {robot_state.current_error.name} resolved")
                robot_state.current_error = None
                robot_state.waiting_for_hitl = False
            
            await asyncio.sleep(5)  # Diagnostic interval
            
        except Exception as e:
            logger.error(f"❌ Diagnostic error: {e}")
            await asyncio.sleep(5)


async def handle_error_with_adk(error: ErrorCode):
    """Handle error using ADK main agent with A2A escalation"""
    logger.info(f"🧠 ADK handling with A2A: {error.name}")
    
    try:
        # Get sensor data
        sensors = robot_state.hardware.get_sensor_readings()
        
        # Create session
        session_id = f"error_{error.name}_{datetime.now(timezone.utc).timestamp()}"
        await robot_state.session_service.create_session(
            app_name=f"robot_{robot_state.robot_id}",
            user_id=robot_state.robot_id,
            session_id=session_id
        )
        
        # Run main agent (will use remote_support_agent automatically via A2A)
        query = f"""Error detected: {error.name} ({error.value})
Sensor data: Battery {sensors['battery_level']}%, Temperature {sensors['temperature']}°C
Please handle this error. Escalate to support if needed."""
        
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        
        result_text = ""
        async for event in robot_state.runner.run_async(
            user_id=robot_state.robot_id,
            session_id=session_id,
            new_message=query_content
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result_text += part.text
        
        logger.info(f"📊 ADK A2A Result: {result_text[:200]}...")
        
    except Exception as e:
        logger.error(f"❌ ADK A2A error handling failed: {e}")


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "RoboNest Embedded Robot API",
        "version": "3.0.0-A2A",
        "framework": "Google ADK",
        "protocol": "A2A",
        "robot_id": robot_state.robot_id,
        "support_connection": robot_state.support_url,
        "status": "operational"
    }


@app.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status():
    """Get complete robot status"""
    sensors = robot_state.hardware.get_sensor_readings()
    
    return StatusResponse(
        robot_id=robot_state.robot_id,
        state="error" if robot_state.current_error else "operational",
        current_error=robot_state.current_error.name if robot_state.current_error else None,
        battery_level=int(sensors["battery_level"]),
        temperature=round(sensors["temperature"], 1),
        wheels_blocked=sensors.get("wheels_blocked", False),
        diagnostics_running=robot_state.diagnostics_running,
        adk_metrics={
            "self_resolutions": robot_state.self_resolution_count,
            "escalations": robot_state.escalation_count,
            "failed_solutions": robot_state.failed_solution_count,
            "protocol": "A2A",
            "self_resolution_rate": f"{robot_state.self_resolution_count / max(1, robot_state.escalation_count + robot_state.self_resolution_count):.1%}"
        }
    )


@app.post("/simulate/error/{error_code}", tags=["Simulator"])
async def simulate_error(error_code: str):
    """
    Simulate an error for testing
    
    Available codes:
    - E01: Wheels blocked
    - E07: Battery critical (HITL)
    - E03: Battery low
    """
    logger.info(f"🎬 Simulating error: {error_code}")
    
    if error_code == "E01":
        robot_state.hardware.simulate_wheels_blocked()
        return {"status": "success", "message": f"Simulated {error_code}: Wheels blocked"}
    
    elif error_code == "E07":
        robot_state.hardware.simulate_battery_critical()
        return {"status": "success", "message": f"Simulated {error_code}: Battery critical (HITL required)"}
    
    elif error_code == "E03":
        robot_state.hardware.simulate_battery_low()
        return {"status": "success", "message": f"Simulated {error_code}: Battery low"}
    
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown error code: {error_code}")


@app.post("/fix/{action}", tags=["Simulator"])
async def manual_fix(action: str):
    """Manual fix for testing (HITL simulation)"""
    logger.info(f"🔧 Manual HITL fix: {action}")
    result = robot_state.hardware.execute_action(action, "MANUAL")
    
    # Clear HITL waiting state
    if robot_state.waiting_for_hitl:
        robot_state.waiting_for_hitl = False
        logger.info("✅ HITL intervention completed, robot resuming normal operation")
    
    return result


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "robot_id": robot_state.robot_id,
        "protocol": "A2A",
        "diagnostics_running": robot_state.diagnostics_running,
        "current_error": robot_state.current_error.name if robot_state.current_error else None,
        "support_connected": True  # Assume connected if agent created
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🤖 EMBEDDED ROBOT API - A2A PROTOCOL")
    print("="*60)
    print("\nRobot: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    print("Support System: http://localhost:8000")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
