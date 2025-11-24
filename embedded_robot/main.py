"""
Embedded Robot API - Complete FastAPI server with ADK integration
PORT 8001

This is the ONLY entry point for the embedded robot system.
Everything is built with ADK patterns from the Kaggle course.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import sys
from pathlib import Path

# Add root to path to allow importing communication
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# ADK imports
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
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

# Communication imports
from communication.protocols import MessageFactory, TaskPriority

logger = logging.getLogger(__name__)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class SolutionRequest(BaseModel):
    """Solution received from Support System"""
    action: str = Field(..., description="Action to execute: clean_wheels, cooldown, reboot, shutdown, wait_hitl")
    error_code: str = Field(..., description="Error code being resolved (E01, E07, etc.)")
    ticket_id: str = Field(..., description="Jira ticket ID")
    agent_id: str = Field(..., description="ID of agent that sent solution")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    requires_hitl: bool = Field(False, description="Whether this requires human intervention")


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


class SolutionResult(BaseModel):
    """Result of solution execution"""
    status: str = Field(..., description="success, failed, pending_hitl")
    message: str
    ticket_id: str
    error_resolved: bool = Field(False, description="Whether the error was actually resolved")
    requires_escalation: bool = Field(False, description="Whether to escalate back to support")


class ErrorSimulation(BaseModel):
    """Request to simulate an error"""
    error_code: str = Field(..., description="Error code to simulate: E01, E07, etc.")


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
        
        # Create main orchestrator
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
        
        # Metrics
        self.self_resolution_count = 0
        self.escalation_count = 0
        self.failed_solution_count = 0
        
        logger.info(f"✅ Robot State initialized: {robot_id}")
    
    def _create_main_agent(self) -> LlmAgent:
        """Create main orchestrator agent"""
        return LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=self.retry_config),
            name="robot_orchestrator",
            description="Main robot orchestrator with memory and self-healing",
            instruction="""
            You are the main robot orchestrator.
            
            When handling an error:
            1. Use sensor_agent to get current readings
            2. Use diagnostic_agent to identify root cause
            3. Search memory for known solutions
            4. If memory has solution with confidence > 0.7:
               - Attempt self-resolution using action_agent
               - If successful: update memory with success
               - If failed: escalate with attempted solution details
            5. If no memory or low confidence: escalate immediately
            
            For critical errors (E07, E08, E09): escalate immediately, never attempt self-resolution.
            """,
            tools=[
                FunctionTool(self.search_memory),
                FunctionTool(self.attempt_self_resolution),
                FunctionTool(self.escalate_to_support)
            ],
            sub_agents=[self.sensor_agent, self.diagnostic_agent, self.action_agent]
        )
    
    def search_memory(self, error_code: str) -> Dict[str, Any]:
        """Search memory for solution (simplified for demo)"""
        # In production, use actual memory service
        logger.info(f"🔍 Searching memory for {error_code}")
        return {
            "found": False,
            "error_code": error_code,
            "message": "No solution in memory yet"
        }
    
    def attempt_self_resolution(self, solution: str, error_code: str) -> Dict[str, Any]:
        """Attempt self-resolution"""
        logger.info(f"🔧 Attempting self-resolution: {solution} for {error_code}")
        self.self_resolution_count += 1
        
        # Execute via action agent (synchronous simulation)
        result = self.hardware.execute_action(solution, error_code)
        
        return {
            "success": result["status"] == "success",
            "message": result.get("message", ""),
            "self_resolution_count": self.self_resolution_count
        }
    
    async def escalate_to_support(self, error_code: str, diagnostics: Dict, attempted_solution: Optional[str] = None) -> Dict[str, Any]:
        """Escalate to support via HTTP POST to alert receiver"""
        self.escalation_count += 1
        logger.info(f"📤 Escalating {error_code} to support (Total: {self.escalation_count})")
        
        # Create A2A Escalation Message
        message = MessageFactory.create_escalation(
            sender_id=self.robot_id,
            escalation_id=f"ESC-{self.escalation_count}-{int(datetime.utcnow().timestamp())}",
            escalation_type="technical",
            severity=self._classify_severity(error_code),
            reason=f"Error {error_code} detected",
            ticket_id=f"ROBO-{self.escalation_count:04d}",
            context={
                "robot_id": self.robot_id,
                "error_code": error_code,
                "sensor_data": self.hardware.get_sensor_readings(),
                "diagnostics": diagnostics,
                "attempted_solution": attempted_solution
            }
        )
        
        try:
            # Send HTTP POST to alert receiver
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.support_url}/a2a/message",
                    json=message.to_dict()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Escalation successful. Response: {result}")
                    return {
                        "escalated": True,
                        "ticket_id": result.get("ticket_id", f"ROBO-{self.escalation_count:04d}"),
                        "task_id": result.get("task_id"),
                        "attempted_solution": attempted_solution,
                        "escalation_count": self.escalation_count
                    }
                else:
                    logger.error(f"❌ Escalation failed: {response.status_code} - {response.text}")
                    return {
                        "escalated": False,
                        "error": f"HTTP {response.status_code}",
                        "attempted_solution": attempted_solution
                    }
        
        except Exception as e:
            logger.error(f"❌ Escalation error: {e}")
            return {
                "escalated": False,
                "error": str(e),
                "attempted_solution": attempted_solution
            }
    
    def _classify_severity(self, error_code: str) -> str:
        """Classify error severity"""
        critical_errors = ["E07", "E08", "E09"]
        high_errors = ["E01", "E02"]
        
        if error_code in critical_errors:
            return "critical"
        elif error_code in high_errors:
            return "high"
        else:
            return "medium"


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
    logger.info("🚀 Starting Embedded Robot API...")
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
    title="RoboNest Embedded Robot API (ADK)",
    description="Complete ADK-powered robot with self-healing and memory",
    version="2.0.0",
    lifespan=lifespan
)


# ============================================================
# BACKGROUND DIAGNOSTICS
# ============================================================

async def run_diagnostics():
    """Continuous diagnostics loop using ADK agents"""
    logger.info("🔍 ADK Diagnostics started")
    
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
                
                # Handle via ADK agents
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
    """Handle error using ADK main agent"""
    logger.info(f"🧠 ADK handling: {error.name}")
    
    try:
        # Get sensor data
        sensors = robot_state.hardware.get_sensor_readings()
        
        # Create session
        session_id = f"error_{error.name}_{datetime.utcnow().timestamp()}"
        await robot_state.session_service.create_session(
            app_name=f"robot_{robot_state.robot_id}",
            user_id=robot_state.robot_id,
            session_id=session_id
        )
        
        # Run main agent
        query = f"Error detected: {error.name}. Sensor data: {sensors}. Handle this."
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
        
        logger.info(f"📊 ADK Result: {result_text[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ ADK error handling failed: {e}")
        # Fallback: escalate directly
        robot_state.escalate_to_support(error.name, {})


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "RoboNest Embedded Robot API",
        "version": "2.0.0",
        "framework": "Google ADK",
        "robot_id": robot_state.robot_id,
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
            "self_resolution_rate": f"{robot_state.self_resolution_count / max(1, robot_state.escalation_count + robot_state.self_resolution_count):.1%}"
        }
    )


@app.post("/solution/execute", response_model=SolutionResult, tags=["Solutions"])
async def execute_solution(solution: SolutionRequest, background_tasks: BackgroundTasks):
    """
    Execute solution received from Support System
    
    Flow:
    1. Execute the solution
    2. Check if error is actually resolved
    3. If NOT resolved: escalate back to support automatically
    4. If requires_hitl: enter waiting state
    """
    logger.info(f"📥 Solution received: {solution.action} for {solution.error_code}")
    
    # Handle HITL case
    if solution.requires_hitl or solution.action == "wait_hitl":
        robot_state.waiting_for_hitl = True
        robot_state.current_ticket_id = solution.ticket_id
        
        logger.warning(f"⏳ HITL required for {solution.error_code}. Waiting for human intervention.")
        
        return SolutionResult(
            status="pending_hitl",
            message=f"Waiting for human intervention on ticket {solution.ticket_id}",
            ticket_id=solution.ticket_id,
            error_resolved=False,
            requires_escalation=False
        )
    
    # Execute solution
    try:
        result = robot_state.hardware.execute_action(solution.action, solution.error_code)
        
        if result["status"] == "success":
            # Wait a bit and check if error is actually gone
            await asyncio.sleep(2)
            
            current_error = robot_state.hardware.detect_error()
            
            if current_error and current_error.name == solution.error_code:
                # ERROR STILL PRESENT - Solution didn't work!
                logger.error(f"❌ Solution {solution.action} failed to resolve {solution.error_code}")
                robot_state.failed_solution_count += 1
                
                # Schedule automatic re-escalation
                background_tasks.add_task(
                    re_escalate_failed_solution,
                    solution.error_code,
                    solution.action,
                    solution.ticket_id,
                    result.get("message", "Solution executed but error persists")
                )
                
                return SolutionResult(
                    status="failed",
                    message=f"Solution {solution.action} executed but error {solution.error_code} persists",
                    ticket_id=solution.ticket_id,
                    error_resolved=False,
                    requires_escalation=True
                )
            
            else:
                # SUCCESS - Error resolved!
                logger.info(f"✅ Solution {solution.action} successfully resolved {solution.error_code}")
                robot_state.current_error = None
                robot_state.current_ticket_id = None
                
                return SolutionResult(
                    status="success",
                    message=f"Solution {solution.action} successfully resolved {solution.error_code}",
                    ticket_id=solution.ticket_id,
                    error_resolved=True,
                    requires_escalation=False
                )
        
        else:
            # Execution failed
            logger.error(f"❌ Failed to execute {solution.action}: {result.get('message')}")
            robot_state.failed_solution_count += 1
            
            return SolutionResult(
                status="failed",
                message=f"Failed to execute {solution.action}: {result.get('message')}",
                ticket_id=solution.ticket_id,
                error_resolved=False,
                requires_escalation=True
            )
    
    except Exception as e:
        logger.error(f"❌ Solution execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def re_escalate_failed_solution(error_code: str, failed_solution: str, ticket_id: str, reason: str):
    """
    Re-escalate to support when solution fails
    This runs in background and sends HTTP POST
    """
    logger.warning(f"🔄 Re-escalating {error_code} after failed solution: {failed_solution}")
    
    # Prepare re-escalation payload
    escalation_data = {
        "robot_id": robot_state.robot_id,
        "ticket_id": ticket_id,
        "error_code": error_code,
        "status": "solution_failed",
        "attempted_solution": failed_solution,
        "failure_reason": reason,
        "diagnostics": robot_state.hardware.get_sensor_readings(),
        "timestamp": datetime.utcnow().isoformat(),
        "requires_new_solution": True
    }
    
    try:
        # Send HTTP POST to alert receiver for re-escalation
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try updating existing ticket
            response = await client.post(
                f"{robot_state.support_url}/alerts/solution-failed",
                json=escalation_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Re-escalation successful: {result}")
            else:
                logger.error(f"❌ Re-escalation failed: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Re-escalation error: {e}")
        # Fallback: create new alert
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{robot_state.support_url}/alerts/robot-issue",
                    json=escalation_data
                )
                logger.info(f"📤 Fallback escalation sent: {response.status_code}")
        except Exception as e2:
            logger.error(f"❌ Fallback escalation also failed: {e2}")


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
        raise HTTPException(status_code=400, detail=f"Unknown error code: {error_code}")


@app.post("/fix/{action}", tags=["Simulator"])
async def manual_fix(action: str):
    """Manual fix for testing"""
    result = robot_state.hardware.execute_action(action, "MANUAL")
    return result


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "robot_id": robot_state.robot_id,
        "diagnostics_running": robot_state.diagnostics_running,
        "current_error": robot_state.current_error.name if robot_state.current_error else None
    }


@app.post("/notify/resolution", tags=["Notifications"])
async def notify_resolution(
    ticket_id: str,
    resolved: bool,
    message: Optional[str] = None
):
    """
    Endpoint for support system to notify resolution status
    
    Called by alert_receiver after HITL or other resolution
    """
    logger.info(f"📥 Resolution notification for ticket {ticket_id}: {'✅ Resolved' if resolved else '❌ Not resolved'}")
    
    if resolved:
        # Clear error state
        robot_state.current_error = None
        robot_state.waiting_for_hitl = False
        robot_state.current_ticket_id = None
        
        # Clear hardware error
        robot_state.hardware.clear_error()
        
        logger.info(f"✅ Ticket {ticket_id} resolved. Robot operational.")
    else:
        logger.warning(f"⚠️ Ticket {ticket_id} resolution failed. Error persists.")
    
    return {
        "status": "acknowledged",
        "ticket_id": ticket_id,
        "robot_status": "operational" if resolved else "error",
        "message": message or ("Resolution acknowledged" if resolved else "Awaiting further action")
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
    print("🤖 EMBEDDED ROBOT API - ADK POWERED")
    print("="*60)
    print("\nServer: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)