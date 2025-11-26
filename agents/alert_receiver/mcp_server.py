"""
MCP Server HTTP pour AlertReceiver
Expose les tools MCP via FastAPI sur port 8001
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global agent reference (set by start_system)
alert_receiver_agent = None


class MCPToolCall(BaseModel):
    """MCP Tool Call request"""
    tool: str
    arguments: Dict[str, Any]


class MCPToolResult(BaseModel):
    """MCP Tool Call result"""
    content: str
    success: bool


app = FastAPI(
    title="AlertReceiver MCP Server",
    description="MCP tools for robot alerts",
    version="1.0.0"
)


def set_agent(agent):
    """Set the global agent reference"""
    global alert_receiver_agent
    alert_receiver_agent = agent
    logger.info("✅ AlertReceiver agent set in MCP server")


@app.post("/mcp/tools/submit_alert", response_model=MCPToolResult)
async def submit_alert(
    robot_id: str,
    error_code: str,
    severity: str,
    description: str,
    sensor_data: Dict[str, Any]
) -> MCPToolResult:
    """Submit a robot alert"""
    if not alert_receiver_agent:
        raise HTTPException(status_code=500, detail="AlertReceiver not initialized")
    
    try:
        # Import models from alert_receiver_agent
        from agents.alert_receiver.alert_receiver_agent import RobotAlert, SensorData
        
        # Create alert
        alert = RobotAlert(
            robot_id=robot_id,
            error_code=error_code,
            severity=severity,
            description=description,
            sensor_data=SensorData(**sensor_data)
        )
        
        # Process via agent
        result = await alert_receiver_agent.process_alert(alert)
        
        if result["status"] == "success":
            message = f"Alert received. Task ID: {result['task_id']}"
            logger.info(f"✅ MCP Alert processed: {message}")
            return MCPToolResult(content=message, success=True)
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"❌ MCP submit_alert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/poll_solution", response_model=Dict[str, Any])
async def poll_solution(robot_id: str) -> Optional[Dict[str, Any]]:
    """Poll for pending solution"""
    if not alert_receiver_agent:
        raise HTTPException(status_code=500, detail="AlertReceiver not initialized")
    
    try:
        # Check queue
        if hasattr(alert_receiver_agent, "solution_queue") and robot_id in alert_receiver_agent.solution_queue:
            solution = alert_receiver_agent.solution_queue.pop(robot_id)
            logger.info(f"✅ MCP Solution polled for {robot_id}")
            return solution
        
        return None
        
    except Exception as e:
        logger.error(f"❌ MCP poll_solution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "agent_ready": alert_receiver_agent is not None
    }
