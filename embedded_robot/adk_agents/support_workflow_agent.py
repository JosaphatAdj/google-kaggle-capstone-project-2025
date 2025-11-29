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
    # STEP 3: Status Checker Agent
    # ========================================
    status_checker = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_config=retry_config),
        name="status_checker",
        description="Checks robot status and decides if loop should continue",
        instruction=f"""
Check robot status using get_robot_status tool.

Report the current status clearly.
The loop will automatically stop after max iterations or when appropriate.
        """,
        tools=[
            FunctionTool(robot_state.get_robot_status)
        ]
    )
    
    # ========================================
    # Loop: Repeat until resolved or HITL
    # ========================================
    support_workflow = LoopAgent(
        name="support_workflow",
        description="Loops A2A escalation → execution → verification until resolved or HITL",
        sub_agents=[
            escalation_sequence,  # Step 1: Contact support + execute
            status_checker        # Step 2: Check if should continue
        ],
        max_iterations=3
    )
    
    logger.info(f"✅ Support Workflow Agent created (Sequential + Loop)")
    
    return support_workflow
