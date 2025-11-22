"""
Sensor Agents - Sequential reading of robot sensors
Uses SequentialAgent to read sensors in order
"""

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from typing import Dict, Any


def create_sensor_sequential_agent(retry_config: types.HttpRetryOptions, hardware) -> SequentialAgent:
    """
    Create a SequentialAgent that reads all sensors in order
    
    This demonstrates the Sequential pattern from Day 1:
    Reads all sensors from hardware simulator
    
    Args:
        retry_config: Retry configuration for Gemini
        hardware: HardwareSimulator instance
    
    Returns:
        SequentialAgent for sensor reading
    """
    
    # Create sensor reading tool that uses hardware simulator
    def read_all_sensors() -> Dict[str, Any]:
        """Read all hardware sensors at once"""
        return hardware.get_sensor_readings()
    
    # Sensor reading agent
    sensor_agent = Agent(
        name="sensor_reader",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""
        Read all robot sensors using read_all_sensors tool.
        Report the complete sensor status clearly.
        
        Pay special attention to:
        - Battery level < 20% (critical)
        - Temperature > 60°C (critical)
        - Wheels blocked (critical)
        
        Format your response as a clear sensor report with all readings.
        """,
        tools=[read_all_sensors],
        output_key="sensor_readings"
    )
    
    # Wrap in Sequential Agent for pattern demonstration
    sensor_sequential = SequentialAgent(
        name="sensor_reading_pipeline",
        description="Reads robot sensors",
        sub_agents=[sensor_agent]
    )
    
    return sensor_sequential