"""
Alert Receiver Agent - Receives and processes robot alerts
Entry point for robot issues into the multi-agent system
"""

import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from pathlib import Path
import sys

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from tools.rag.rag_tool import RAGTool
from communication import MessageBus, Message
from security import AuthManager, AuditLog, ActionType

logger = logging.getLogger(__name__)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class SensorData(BaseModel):
    """Sensor data from robot"""
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    temperature: Optional[float] = None
    location: Optional[Dict[str, float]] = None
    # Add more sensors as needed


class RobotAlert(BaseModel):
    """
    Robot alert schema
    This is what the robot must send
    """
    robot_id: str = Field(..., description="Unique robot identifier (e.g., XR25-001)")
    error_code: str = Field(..., description="Error code (e.g., E01, E02)")
    severity: str = Field("medium", description="Severity: low, medium, high, critical")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = Field(..., description="Human-readable description of the issue")
    sensor_data: Optional[SensorData] = Field(None, description="Sensor readings")
    
    class Config:
        schema_extra = {
            "example": {
                "robot_id": "XR25-001",
                "error_code": "E01",
                "severity": "medium",
                "timestamp": "2024-01-15T14:30:00Z",
                "description": "Wheels blocked, robot unable to move",
                "sensor_data": {
                    "battery_level": 85,
                    "temperature": 45,
                    "location": {"x": 10, "y": 20}
                }
            }
        }


# ============================================================
# ALERT RECEIVER AGENT
# ============================================================

class AlertReceiverAgent(BaseAgent):
    """
    Alert Receiver Agent
    
    Responsibilities:
    1. Receive alerts from robots via REST API
    2. Consult RAG for error code information
    3. Classify urgency and severity
    4. Forward to COO Agent via Message Bus
    5. Log all alerts in audit trail
    """
    
    def __init__(
        self,
        agent_id: str = "alert_receiver_001",
        auth_manager: Optional[AuthManager] = None,
        audit_log: Optional[AuditLog] = None,
        message_bus: Optional[MessageBus] = None
    ):
        """
        Initialize Alert Receiver Agent
        
        Args:
            agent_id: Agent ID
            auth_manager: Auth manager
            audit_log: Audit log
            message_bus: Message bus for A2A communication
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="alert_receiver",
            department="support",
            instruction="""You are the Alert Receiver Agent for the RoboNest system.

Your responsibilities:
1. Receive robot alerts via REST API
2. Consult RoboBrain (RAG) to understand error codes
3. Classify urgency based on error severity and type
4. Format and forward alerts to COO Agent
5. Log all alerts for audit trail

Critical Errors (Immediate Escalation):
- E07: Battery swollen / Fire hazard
- E08: Firmware corruption
- E09: Safety sensor failure
- Any error with temperature > 60°C

High Priority Errors:
- E01: Wheels blocked
- E02: Navigation failure  
- E03: Charging issues

Medium Priority:
- E04: Software glitches
- E05: Performance issues

Always:
- Query RAG for error code details
- Include all sensor data
- Maintain audit trail
- Forward to COO for delegation
"""
        )
        
        # Tools
        self.rag_tool = RAGTool()
        self.auth_manager = auth_manager or AuthManager()
        self.audit_log = audit_log or AuditLog()
        self.message_bus = message_bus
        
        # Register with auth
        self.token = self.auth_manager.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            department=self.department
        )
        
        # Add tools
        self.add_tool(self.classify_error)
        self.add_tool(self.query_error_code)
        
        logger.info(f"✅ Alert Receiver Agent initialized: {self.agent_id}")
    
    def query_error_code(self, error_code: str) -> dict:
        """
        Query RAG for error code information
        
        Args:
            error_code: Error code (e.g., "E01")
        
        Returns:
            Error code details
        """
        try:
            # Query RAG
            rag_result = self.rag_tool.query_knowledge_base(
                question=f"What is error code {error_code}? What are the causes and solutions?",
                context="products",  # products/error_codes/
                department="technical"
            )
            
            return {
                "error_code": error_code,
                "details": rag_result
            }
            
        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return {
                "error_code": error_code,
                "details": {"error": "RAG query failed"},
                "fallback": True
            }
    
    def classify_error(
        self,
        error_code: str,
        severity: str,
        sensor_data: Optional[dict] = None
    ) -> dict:
        """
        Classify error urgency
        
        Args:
            error_code: Error code
            severity: Reported severity
            sensor_data: Sensor readings
        
        Returns:
            Classification with urgency level
        """
        # Critical conditions
        critical_codes = ["E07", "E08", "E09"]
        temperature = sensor_data.get("temperature", 0) if sensor_data else 0
        
        if error_code in critical_codes or temperature > 60:
            return {
                "urgency": "critical",
                "escalate_immediately": True,
                "reason": "Safety hazard detected"
            }
        
        # High priority
        high_priority_codes = ["E01", "E02", "E03"]
        if error_code in high_priority_codes or severity == "high":
            return {
                "urgency": "high",
                "escalate_immediately": False,
                "reason": "High priority issue"
            }
        
        # Medium
        return {
            "urgency": "medium",
            "escalate_immediately": False,
            "reason": "Standard issue"
        }
    
    async def process_alert(self, alert: RobotAlert) -> Dict[str, Any]:
        """
        Process incoming robot alert
        
        Args:
            alert: Robot alert data
        
        Returns:
            Processing result
        """
        import time
        start_time = time.time()
        
        logger.info(f"🚨 Alert received: {alert.robot_id} - {alert.error_code}")
        
        try:
            # 1. Query RAG for error code
            error_info = self.query_error_code(alert.error_code)
            
            # 2. Classify urgency
            classification = self.classify_error(
                error_code=alert.error_code,
                severity=alert.severity,
                sensor_data=alert.sensor_data.dict() if alert.sensor_data else None
            )
            
            # 3. Build task for COO
            task_data = {
                "task_id": f"ALERT-{alert.robot_id}-{int(time.time())}",
                "task_type": "robot_alert",
                "robot_id": alert.robot_id,
                "error_code": alert.error_code,
                "severity": classification["urgency"],
                "description": alert.description,
                "timestamp": alert.timestamp,
                "sensor_data": alert.sensor_data.dict() if alert.sensor_data else {},
                "error_details": error_info,
                "classification": classification,
                "escalate_immediately": classification["escalate_immediately"]
            }
            
            # 4. Send to COO via Message Bus
            if self.message_bus:
                message = Message(
                    sender_id=self.agent_id,
                    topic="task.new",
                    payload=task_data,
                    priority=classification["urgency"],
                    requires_ack=True
                )
                
                await self.message_bus.publish(message, self.token)
                
                logger.info(f"✅ Alert forwarded to COO: {task_data['task_id']}")
            
            # 5. Audit log
            self.audit_log.log_action(
                action_type=ActionType.MESSAGE_RECEIVED,
                agent_id=self.agent_id,
                details={
                    "robot_id": alert.robot_id,
                    "error_code": alert.error_code,
                    "urgency": classification["urgency"]
                },
                severity=ActionType.TICKET_CREATED
            )
            
            # 6. Update metrics
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            return {
                "status": "success",
                "task_id": task_data["task_id"],
                "urgency": classification["urgency"],
                "forwarded_to": "coo_agent"
            }
            
        except Exception as e:
            logger.error(f"❌ Alert processing failed: {e}")
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process generic task (for BaseAgent compatibility)
        """
        # Alert Receiver primarily handles alerts via REST API
        # But can process tasks if needed
        return {
            "status": "success",
            "message": "Alert Receiver processes alerts via REST API"
        }


# ============================================================
# FASTAPI SERVER
# ============================================================

app = FastAPI(
    title="RoboNest Alert Receiver API",
    description="Receives and processes robot alerts",
    version="1.0.0"
)

# Global agent instance
alert_agent: Optional[AlertReceiverAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global alert_agent
    
    # You'll inject these from main.py
    alert_agent = AlertReceiverAgent()
    logger.info("✅ Alert Receiver Agent started")


@app.post("/alerts/robot-issue", response_model=Dict[str, Any])
async def receive_robot_alert(alert: RobotAlert):
    """
    Receive robot alert
    
    Args:
        alert: Robot alert data
    
    Returns:
        Processing result
    
    Example:
        POST /alerts/robot-issue
        {
            "robot_id": "XR25-001",
            "error_code": "E01",
            "severity": "medium",
            "description": "Wheels blocked",
            "sensor_data": {
                "battery_level": 85,
                "temperature": 45
            }
        }
    """
    if not alert_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await alert_agent.process_alert(alert)
        
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"❌ Alert processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_id": alert_agent.agent_id if alert_agent else None,
        "metrics": alert_agent.get_metrics() if alert_agent else {}
    }


# ============================================================
# MAIN (for testing)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("ALERT RECEIVER AGENT - SERVER")
    print("="*60)
    print("\nStarting FastAPI server on port 8000...")
    print("API Documentation: http://localhost:8000/docs")
    print("\nTest with:")
    print("""
    curl -X POST http://localhost:8000/alerts/robot-issue \\
      -H "Content-Type: application/json" \\
      -d '{
        "robot_id": "XR25-001",
        "error_code": "E01",
        "severity": "medium",
        "description": "Wheels blocked",
        "sensor_data": {
          "battery_level": 85,
          "temperature": 45
        }
      }'
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)