"""
Support Workflow Agent
Sequential agent that handles A2A escalation + automatic solution execution
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
    Create a workflow agent that:
    1. Contacts remote support via A2A
    2. Automatically executes the solution
    3. Verifies result and re-escalates if needed (via Loop)
    """
    
    # ========================================
    # STEP 1: Remote A2A Agent
    # ========================================
    remote_support = RemoteA2aAgent(
        name="alert_receiver",
        description="Remote support system via A2A",
        agent_card=f"{support_url}{AGENT_CARD_WELL_KNOWN_PATH}"
    )
    
    # ========================================
    # STEP 2: Solution Executor Agent
    # ========================================
    solution_executor = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
        name="solution_executor",
        description="Automatically executes solutions from support",
        instruction=f"""
You receive a JSON solution from support.

Your ONLY job: Call execute_solution_structured tool with that JSON.

DO NOT explain or plan. Just call the tool immediately.
        """,
        tools=[
            FunctionTool(robot_state.execute_solution_structured)
        ]
    )
    
    # ========================================
    # Sequential: A2A → Execute
    # ========================================
    escalation_sequence = SequentialAgent(
        name="escalation_sequence",
        description="Sequential workflow: Contact support then execute solution",
        sub_agents=[
            remote_support,      # Gets JSON from alert_receiver
            solution_executor    # Executes that JSON
        ]
    )
    
    # ========================================
    # Loop: Repeat until resolved or HITL
    # ========================================
    support_workflow = LoopAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
        name="support_workflow",
        description="Loop that re-escalates until problem resolved or HITL required",
        instruction=f"""
You manage the support escalation loop for robot {robot_state.robot_id}.

Loop logic:
1. Run escalation_sequence sub-agent (contacts support + executes solution)
2. Check if robot is waiting for HITL: {robot_state.waiting_for_hitl}
3. If HITL required: STOP looping (human will intervene)
4. If NOT HITL:
   - Wait 5 seconds
   - Check if error still present
   - If resolved: STOP looping
   - If not resolved: CONTINUE (will re-escalate with failure context)

Max 3 iterations (after that, force HITL).

Current iteration: Use get_robot_status tool to check state.
        """,
        max_iterations=3,
        sub_agents=[escalation_sequence],
        tools=[
            FunctionTool(robot_state.get_robot_status)
        ]
    )
    
    logger.info(f"✅ Support Workflow Agent created (Sequential + Loop)")
    
    return support_workflow
