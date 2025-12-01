"""
Support Workflow Agent 
"""

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types
import logging

logger = logging.getLogger(__name__)


def create_support_workflow_agent(
    robot_state,
    retry_config: types.HttpRetryOptions,
    support_url: str = "http://localhost:8000"
):
    """
    Minimal workflow - formatter in Sequential to avoid LLM hesitation
    """
    
    # Suppress warnings
    import warnings
    warnings.filterwarnings('ignore', message='.*EXPERIMENTAL.*')
    
    # ========================================
    # Message Formatter (FunctionTool)
    # ========================================
    def format_robot_alert() -> str:
        """Auto-format alert with robot_id"""
        current_error = robot_state.current_error
        if not current_error:
            return "No error"
        
        sensors = robot_state.hardware.get_sensor_readings()
        error_name = current_error.name
        
        # Error descriptions
        descriptions = {
            "E01": "Wheels blocked", "E02": "Navigation error",
            "E03": "Low battery", "E04": "Software error",
            "E05": "Performance degraded", "E06": "Communication lost",
            "E07": "Battery critical", "E08": "Firmware corruption",
            "E09": "Safety sensor failure"
        }
        
        message = (
            f"Robot ID: {robot_state.robot_id}\n"
            f"Error Code: {error_name}\n"
            f"Description: {descriptions.get(error_name, error_name)}\n"
            f"Battery: {int(sensors.get('battery_level', 0))}%\n"
            f"Temperature: {sensors.get('temperature', 0.0):.1f}°C"
        )
        
        logger.info(f"📤 Formatted: {robot_state.robot_id} - {error_name}")
        return message
    
    # Formatter agent - just calls tool once
    formatter_agent = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_config=retry_config),
        name="formatter",
        description="Formats alert",
        instruction="Call format_robot_alert. Return ONLY the tool output.Nothing else.",
        tools=[FunctionTool(format_robot_alert)]
    )
    
    # ========================================
    # A2A Communication with Alert Receiver
    # ========================================
    alert_receiver = RemoteA2aAgent(
        name="alert_receiver",
        description="Remote Alert Receiver for RoboNest support",
        agent_card=f"{support_url}{AGENT_CARD_WELL_KNOWN_PATH}"
    )
    
    # ========================================
    # Solution Executor
    # ========================================
    solution_executor = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_config=retry_config),
        name="solution_executor",
        description="Executes solution from support",
        instruction="""
IMMEDIATELY call execute_solution_structured with the solution you received.

CRITICAL: Pass the EXACT input. Do NOT:
- Add explanations
- Modify JSON
- Add quotes
- Remove fields
- Add text before/after

Just call: execute_solution_structured(<exact_input>)
        """,
        tools=[FunctionTool(robot_state.execute_solution_structured)]
    )
    
    # ========================================
    # Sequential: Format → Alert → Execute
    # ========================================
    escalation_sequence = SequentialAgent(
        name="escalation_sequence",
        description="Auto-format → Send → Execute",
        sub_agents=[
            formatter_agent,     # 1. Auto-format with robot_id
            alert_receiver,      # 2. Send via A2A
            solution_executor    # 3. Execute
        ]
    )
    
    # ========================================
    # Status Checker
    # ========================================
    status_checker = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_config=retry_config),
        name="status_checker",
        description="Checks if error resolved or HITL needed",
        instruction="""
Call get_robot_status tool.

STOP loop if:
1. State = OPERATIONAL → Say "STOP: Resolved"
2. waiting_for_hitl = True → Say "STOP: HITL required"

Otherwise: Say "CONTINUE"
        """,
        tools=[FunctionTool(robot_state.get_robot_status)]
    )
    
    # ========================================
    # Loop: Until resolved or HITL
    # ========================================
    support_workflow = LoopAgent(
        name="support_workflow",
        description="Loop escalation until resolved or HITL",
        sub_agents=[
            escalation_sequence,  # Send + Execute
            status_checker        # Check status
        ],
        max_iterations=2  # Max 2 attempts
    )
    
    logger.info(f"✅ Support Workflow Agent created (simplified)")
    
    return support_workflow
