"""
Diagnostic Agent - Uses LoopAgent to iteratively diagnose issues
Loops until root cause is identified or max iterations reached
"""

from google.adk.agents import Agent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types
from typing import Dict, Any


def analyze_symptoms(sensor_data: str) -> Dict[str, Any]:
    """
    Analyze sensor data to identify symptoms
    
    Args:
        sensor_data: String containing sensor readings
    
    Returns:
        Identified symptoms
    """
    symptoms = []
    
    # Convert to lowercase for easier matching
    data_lower = str(sensor_data).lower()
    
    # Check battery
    if "battery" in data_lower:
        if "critical" in data_lower or any(str(x) in data_lower for x in range(0, 20)):
            symptoms.append("battery_critical")
        elif "low" in data_lower:
            symptoms.append("battery_low")
    
    # Check temperature
    if "temperature" in data_lower:
        if "critical" in data_lower or "60" in data_lower or "65" in data_lower or "70" in data_lower:
            symptoms.append("temperature_critical")
        elif "warning" in data_lower or "50" in data_lower or "55" in data_lower:
            symptoms.append("temperature_high")
    
    # Check wheels
    if "wheel" in data_lower:
        if "blocked" in data_lower or "true" in data_lower:
            symptoms.append("wheels_blocked")
    
    # Check navigation
    if "navigation" in data_lower:
        if "false" in data_lower or "fail" in data_lower:
            symptoms.append("navigation_failure")
    
    return {
        "symptoms_found": len(symptoms),
        "symptoms": symptoms,
        "analysis_complete": len(symptoms) > 0
    }


def correlate_error_code(symptoms: list) -> Dict[str, Any]:
    """
    Correlate symptoms to error codes
    
    Args:
        symptoms: List of identified symptoms
    
    Returns:
        Error code and diagnosis
    """
    # Error code mapping
    error_map = {
        "wheels_blocked": {
            "code": "E01",
            "description": "Wheels blocked - obstacle or mechanical issue",
            "severity": "high"
        },
        "temperature_critical": {
            "code": "E07",
            "description": "Battery temperature critical - possible swelling",
            "severity": "critical"
        },
        "battery_critical": {
            "code": "E03",
            "description": "Battery level critical - needs charging",
            "severity": "medium"
        },
        "battery_low": {
            "code": "E03",
            "description": "Battery level low - needs charging soon",
            "severity": "medium"
        },
        "navigation_failure": {
            "code": "E02",
            "description": "Navigation system failure",
            "severity": "high"
        }
    }
    
    # Find matching error (prioritize critical ones)
    for symptom in symptoms:
        if symptom in error_map:
            error_info = error_map[symptom]
            return {
                "error_code": error_info["code"],
                "description": error_info["description"],
                "severity": error_info["severity"],
                "root_cause_found": True,
                "symptoms": symptoms
            }
    
    # No specific error found
    return {
        "error_code": "E04",
        "description": "General malfunction detected",
        "severity": "medium",
        "root_cause_found": True,
        "symptoms": symptoms
    }


def exit_diagnostic_loop():
    """
    Exit the diagnostic loop when root cause is found
    
    This is called by the DiagnosticRefinerAgent to signal completion
    """
    return {
        "status": "diagnosis_complete",
        "message": "Root cause identified, exiting diagnostic loop"
    }


def create_diagnostic_loop_agent(retry_config: types.HttpRetryOptions) -> LoopAgent:
    """
    Create a LoopAgent for iterative diagnostics
    
    This demonstrates the Loop pattern from Day 1:
    - Analyzer identifies symptoms
    - Refiner correlates to error codes
    - Loops until root cause found or max iterations
    
    Args:
        retry_config: Retry configuration for Gemini
    
    Returns:
        LoopAgent for diagnostics
    """
    
    # Symptom Analyzer Agent
    analyzer_agent = Agent(
        name="symptom_analyzer",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""
        You are a symptom analysis expert for robot diagnostics.
        
        Use the analyze_symptoms tool to examine the sensor data provided.
        Identify all symptoms present in the readings.
        
        Report findings clearly and concisely.
        """,
        tools=[analyze_symptoms],
        output_key="symptom_analysis"
    )
    
    # Diagnostic Refiner Agent (with exit capability)
    refiner_agent = Agent(
        name="diagnostic_refiner",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""
        You are a diagnostic expert that correlates symptoms to error codes.
        
        Symptom Analysis: {symptom_analysis}
        
        Your task:
        1. Review the symptoms identified
        2. Use correlate_error_code tool to determine the error code
        3. If root cause is found (root_cause_found: true), call exit_diagnostic_loop
        4. If not found, describe what additional analysis is needed
        
        IMPORTANT: Once you identify a clear error code, you MUST call exit_diagnostic_loop.
        """,
        tools=[
            correlate_error_code,
            exit_diagnostic_loop
        ],
        output_key="diagnostic_result"
    )
    
    # Create Loop Agent (iterative diagnosis)
    diagnostic_loop = LoopAgent(
        name="diagnostic_loop",
        description="Iteratively diagnoses robot issues until root cause found",
        sub_agents=[
            analyzer_agent,
            refiner_agent
        ],
        max_iterations=3  # Prevent infinite loops
    )
    
    return diagnostic_loop