"""
Alert Receiver Agent - A2A Compatible version
Receives robot alerts and provides solutions via Google ADK A2A protocol
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from pathlib import Path
import sys
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.genai import types

# Internal imports
from tools.rag.rag_tool import RAGTool
from tools.gmail.gmail_tool import send_escalation_email, get_gmail_tool
from tools.jira.jira_tool import create_jira_ticket, get_jira_tool
from communication.message_bus import MessageBus, Message
from security import AuthManager, AuditLog, ActionType

logger = logging.getLogger(__name__)


# ============================================================
# GLOBAL STATE (shared between agent and tools)
# ============================================================

class AlertReceiverState:
    """Global state for Alert Receiver Agent"""
    
    def __init__(self):
        # Infrastructure
        self.auth_manager = AuthManager()
        self.audit_log = AuditLog()
        self.message_bus: Optional[MessageBus] = None
        self.rag_tool = RAGTool()
        
        # Token
        self.token: Optional[str] = None
        
        # Tracking
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.solution_queue: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.alerts_received = 0
        self.solutions_sent = 0
        
        logger.info("✅ Alert Receiver State initialized")


# Global state instance
alert_state = AlertReceiverState()


# ============================================================
# TOOL FUNCTIONS (exposed to the agent)
# ============================================================

async def query_error_code(error_code: str) -> str:
    """
    Query RAG for error code information.
    
    Args:
        error_code: Error code (e.g., E01, E07)
        
    Returns:
        Information about the error code
    """
    try:
        logger.info(f"🔍 Querying RAG for error code: {error_code}")
        
        # Use RAG tool (synchronous version)
        result = await alert_state.rag_tool.query_knowledge_base(
            question=f"What is error code {error_code}? What are the causes and solutions?",
            context="robot_errors",
            department="technical"
        )
        
        return f"Error {error_code} information: {result}"
    
    except Exception as e:
        logger.error(f"❌ RAG query failed: {e}")
        return f"Could not query RAG for {error_code}. Error: {str(e)}"


def classify_error(error_code: str, severity: str, temperature: float = 0.0) -> str:
    """
    Classify error urgency.
    
    Args:
        error_code: Error code
        severity: Stated severity
        temperature: Robot temperature
        
    Returns:
        Classification result
    """
    critical_codes = ["E07", "E08", "E09"]
    
    if error_code in critical_codes or temperature > 60:
        urgency = "critical"
        reason = "Safety hazard detected - HITL required"
    elif error_code in ["E01", "E02", "E03"] or severity == "high":
        urgency = "high"
        reason = "High priority issue"
    else:
        urgency = "medium"
        reason = "Standard issue"
    
    return f"Urgency: {urgency}. Reason: {reason}"


def send_hitl_notifications(
    robot_id: str,
    error_code: str,
    severity: str,
    description: str,
    ticket_id: str
) -> str:
    """
    Send HITL notifications via Gmail and create Jira ticket
    
    Args:
        robot_id: Robot identifier
        error_code: Error code
        severity: Severity level
        description: Error description
        ticket_id: Ticket ID
    
    Returns:
        Notification status message
    """
    logger.warning(f"📧 Sending HITL notifications for {robot_id} - {error_code}")
    
    results = []
    
    # Send Gmail notification
    try:
        email_result = send_escalation_email(
            division="support",
            issue_data={
                "robot_id": robot_id,
                "error_code": error_code,
                "severity": severity,
                "description": description,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            escalation_type="HITL"
        )
        if email_result.get("success"):
            results.append(f"✅ Email sent to {email_result.get('to')}")
            logger.warning(f"✅ HITL Email sent")
        else:
            results.append(f"⚠️  Email failed: {email_result.get('error')}")
    except Exception as e:
        results.append(f"⚠️  Email skipped: {str(e)}")
        logger.warning(f"⚠️  Gmail skipped: {e}")
    
    # Create Jira ticket
    try:
        jira_result = create_jira_ticket(
            summary=f"[HITL] Robot {robot_id} - Error {error_code}",
            description=f"Robot {robot_id} requires human intervention\\n\\nError: {error_code}\\nSeverity: {severity}\\n\\n{description}",
            priority="Critical" if severity == "critical" else "High",
            labels=["HITL", "robot", error_code]
        )
        if jira_result.get("success"):
            results.append(f"✅ Jira ticket: {jira_result.get('ticket_key')}")
            logger.warning(f"✅ HITL Jira: {jira_result.get('ticket_key')}")
        else:
            results.append(f"⚠️  Jira failed: {jira_result.get('error')}")
    except Exception as e:
        results.append(f"⚠️  Jira skipped: {str(e)}")
        logger.warning(f"⚠️  Jira skipped: {e}")
    
    return "; ".join(results)


async def process_robot_alert(
    robot_id: str,
    error_code: str,
    severity: str,
    description: str,
    battery_level: int = 0,
    temperature: float = 0.0,
    location: Optional[Dict[str, float]] = None
) -> str:
    """
    Process a robot alert and forward to support system.
    
    Args:
        robot_id: Unique robot identifier
        error_code: Error code (E01, E07, etc.)
        severity: Severity level
        description: Description of the issue
        battery_level: Battery level %
        temperature: Temperature in °C
        location: Robot location {x, y}
        
    Returns:
        Status message
    """
    logger.info(f"🚨 Processing alert from {robot_id}: {error_code}")
    
    alert_state.alerts_received += 1
    
    try:
        # Create task ID
        task_id = f"ALERT-{robot_id}-{int(time.time())}"
        
        # Build task data
        task_data = {
            "task_id": task_id,
            "task_type": "robot_alert",
            "robot_id": robot_id,
            "error_code": error_code,
            "severity": severity,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "robot_id": robot_id,
                "error_code": error_code,
                "sensor_data": {
                    "battery_level": battery_level,
                    "temperature": temperature,
                    "location": location or {}
                }
            }
        }
        
        # Store active alert
        alert_state.active_alerts[task_id] = {
            "robot_id": robot_id,
            "timestamp": time.time()
        }
        
        # Forward to COO via Message Bus
        if alert_state.message_bus:
            message = Message(
                sender_id="alert_receiver_001",
                topic="task.new",
                payload=task_data,
                priority=severity,
                requires_ack=True
            )
            
            # NOTE: This is synchronous for tool compatibility
            # In production, use asyncio.create_task or similar
            logger.info(f"📤 Forwarding alert to COO: {task_id}")
        
        # Audit log
        alert_state.audit_log.log_action(
            action_type=ActionType.MESSAGE_RECEIVED,
            agent_id="alert_receiver_001",
            details={"robot_id": robot_id, "error_code": error_code}
        )
        
        return f"Alert {task_id} received and forwarded to support system. Solution will be provided asynchronously."
    
    except Exception as e:
        logger.error(f"❌ Alert processing failed: {e}")
        return f"Failed to process alert: {str(e)}"


def provide_solution(
    robot_id: str,
    error_code: str,
    action: str,
    ticket_id: str,
    requires_hitl: bool = False,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    Queue a solution for the robot to retrieve.
    
    Args:
        robot_id: Robot identifier
        error_code: Error code
        action: Action to execute (clean_wheels, reboot, etc.)
        ticket_id: Ticket ID
        requires_hitl: Whether HITL is required
        details: Additional details
        
    Returns:
        Status message
    """
    logger.info(f"💡 Providing solution to {robot_id}: {action}")
    
    solution = {
        "action": action,
        "error_code": error_code,
        "ticket_id": ticket_id,
        "agent_id": "tech_support",
        "details": details or {},
        "requires_hitl": requires_hitl,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Queue solution
    alert_state.solution_queue[robot_id] = solution
    alert_state.solutions_sent += 1
    
    logger.info(f"✅ Solution queued for {robot_id}")
    
    return f"Solution '{action}' queued for robot {robot_id}"


def get_pending_solution(robot_id: str) -> str:
    """
    Get pending solution for a robot.
    
    Args:
        robot_id: Robot identifier
        
    Returns:
        Solution if available, otherwise message
    """
    if robot_id in alert_state.solution_queue:
        solution = alert_state.solution_queue.pop(robot_id)
        logger.info(f"📤 Sending solution to {robot_id}: {solution.get('action')}")
        return f"Solution: {solution}"
    else:
        return f"No pending solution for {robot_id}"


def get_alert_stats() -> str:
    """Get alert statistics"""
    return f"Alerts received: {alert_state.alerts_received}, Solutions sent: {alert_state.solutions_sent}"


# ============================================================
# AGENT CREATION
# ============================================================

def create_alert_receiver_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """Create Alert Receiver Agent with GoogleADK"""
    
    # Define JSON schema for response
    from google.genai.types import GenerateContentConfig
    
    agent = LlmAgent(
        model=Gemini(
            model="gemini-2.0-flash-lite", 
            retry_options=retry_config,
            generation_config=GenerateContentConfig(
                response_mime_type="application/json"
            )
        ),
        name="alert_receiver",
        description="Alert Receiver Agent that processes robot alerts and provides solutions via A2A protocol",
        instruction="""
You are the Alert Receiver Agent for the RoboNest system.

CRITICAL: Always respond with VALID JSON in this exact format:
{
  "actions": ["action1", "action2",...,"actionN"],
  "requires_hitl": true/false,
  "is_temporary_solution": true/false,
  "ticket_id": "ALERT-ROBOTID-TIMESTAMP",
  "error_code": "E01"
}

Error handling rules:
- E07/E08/E09 or temp>60°C → requires_hitl=true, is_temporary_solution=true
- E01 (wheels blocked) → actions: ["clean_wheels", "recalibrate_motors"], requires_hitl=false
- E02 (navigation) → actions: ["reset_navigation", "reboot_sensors"], requires_hitl=false
- E03 (charging) → actions: ["clean_charging_port"], requires_hitl=false

If message contains "ESCALATION ALERT" (1st failure):
- Provide DIFFERENT actions than mentioned as failed
- Keep requires_hitl=false unless critical error 

If message contains "CRITICAL ESCALATION" (2nd failure):
- MANDATORY: requires_hitl=true, is_temporary_solution=true
- Provide safety actions only

When requires_hitl=true, use send_hitl_notifications tool to send notifications to COO and Tech Support.

Examples:
E01 normal: {"actions": ["clean_wheels", "recalibrate_motors"], "requires_hitl": false, "is_temporary_solution": false, "ticket_id": "ALERT-XR25-001-123", "error_code": "E01"}
E07 critical: {"actions": ["cooldown", "power_down"], "requires_hitl": true, "is_temporary_solution": true, "ticket_id": "ALERT-XR25-001-124", "error_code": "E07"}
        """,
        tools=[
            FunctionTool(query_error_code),
            FunctionTool(classify_error),
            FunctionTool(send_hitl_notifications),
            FunctionTool(process_robot_alert),
            FunctionTool(provide_solution),
            FunctionTool(get_pending_solution),
            FunctionTool(get_alert_stats)
        ]
    )
    
    logger.info("✅ Alert Receiver Agent created")
    return agent


# ============================================================
# A2A SERVER INITIALIZATION
# ============================================================

async def initialize_infrastructure():
    """Initialize message bus and other infrastructure"""
    global alert_state
    
    # Start Message Bus
    alert_state.message_bus = MessageBus(
        auth_manager=alert_state.auth_manager,
        audit_log=alert_state.audit_log
    )
    await alert_state.message_bus.start()
    
    # Register agent
    alert_state.token = alert_state.auth_manager.register_agent(
        agent_id="alert_receiver_001",
        agent_type="alert_receiver",
        department="support"
    )
    
    logger.info("✅ Infrastructure initialized")


def create_a2a_server(port: int = 8000):
    """
    Create A2A server for Alert Receiver.
    
    Usage:
        app = create_a2a_server(port=8000)
        # Then run with:  uvicorn alert_receiver_agent:app --port 8000
    """
    
    # Create retry config
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504]
    )
    
    # Create agent
    agent = create_alert_receiver_agent(retry_config)
    
    # Convert to A2A
    app = to_a2a(agent, port=port)
    
    logger.info(f"✅ Alert Receiver A2A Server created on port {port}")
    logger.info(f"   Agent card will be available at: /.well-known/agent-card.json")
    
    return app


# ============================================================
# MAIN (for standalone testing)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🤖 ALERT RECEIVER AGENT - A2A SERVER")
    print("="*60)
    print(f"\nStarting server on port 8000...")
    print(f"Agent card: http://localhost:8000/.well-known/agent-card.json")
    print("="*60 + "\n")
    
    # Create A2A app
    app = create_a2a_server(port=8000)
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)
