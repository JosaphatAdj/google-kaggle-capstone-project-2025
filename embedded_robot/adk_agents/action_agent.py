"""
Action Agent - Executes solutions on the robot
Handles commands like shutdown, clean_wheels, cooldown, etc.
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_action_agent(retry_config: types.HttpRetryOptions, hardware) -> Agent:
    """
    Create an Agent that executes solutions on the robot
    
    This agent can:
    - Execute wheel cleaning
    - Initiate cooldown
    - Perform reboot
    - Shutdown robot
    
    Args:
        retry_config: Retry configuration for Gemini
        hardware: HardwareSimulator instance
    
    Returns:
        Action execution agent
    """
    
    # Create action execution tool using hardware simulator
    def execute_action(action: str, error_code: str = "UNKNOWN") -> Dict[str, Any]:
        """
        Execute action on hardware
        
        Args:
            action: Action to execute (clean_wheels, cooldown, reboot, shutdown, wait_hitl)
            error_code: Error code being addressed
        
        Returns:
            Execution result
        """
        logger.info(f"⚙️ Action Agent executing: {action} for {error_code}")
        return hardware.execute_action(action, error_code)
    
    action_agent = Agent(
        name="action_executor",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""
        You are the action execution agent for a robot.
        
        Your job is to safely execute solutions on the robot hardware.
        
        Use execute_action tool to perform actions:
        - clean_wheels (or fix_wheels): Clean blocked wheels
        - cooldown (or cool_down): Cool down overheated battery
        - reboot (or restart): Reboot the robot
        - shutdown: Safely shutdown the robot
        - wait_hitl: Enter safe state waiting for human intervention
        
        SAFETY RULES:
        1. For critical errors (E07, E08, E09), only shutdown or wait_hitl are allowed
        2. The execute_action tool will automatically verify safety
        3. Never execute unsafe actions
        4. Report execution results clearly with all details
        
        Process:
        1. Call execute_action with the action and error_code
        2. Read the result carefully
        3. Report the outcome to the user with:
           - Whether the action succeeded or failed
           - Any important warnings or messages
           - Next steps if applicable
        
        Be clear, concise, and informative in your responses.
        """,
        tools=[execute_action],
        output_key="action_result"
    )
    
    return action_agent