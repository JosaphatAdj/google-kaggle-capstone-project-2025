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
    5. Receive solutions from COO/TechSupport and forward to Robot
    6. Log all alerts in audit trail
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
5. Receive solutions and forward them to the robot

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
        
        # Track active alerts to map task_id -> robot_id
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # Queue for solutions waiting to be polled by robots
        self.solution_queue: Dict[str, Dict[str, Any]] = {}

        
        logger.info(f"✅ Alert Receiver Agent initialized: {self.agent_id}")
    
    async def start(self):
        """Start the agent and subscribe to topics"""
        if not self.message_bus:
            logger.error("❌ Message bus not configured for Alert Receiver")
            return
            
        # Subscribe to task completion (to receive solutions)
        self.message_bus.subscribe(
            topic="task.completed",
            agent_id=self.agent_id,
            token=self.token,
            handler=self._handle_message
        )
        
        logger.info(f"✅ Alert Receiver Agent started and listening")

    async def _handle_message(self, message: Message):
        """Handle incoming messages"""
        try:
            if message.topic == "task.completed":
                await self._handle_task_completed(message.payload)
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")

    async def _handle_task_completed(self, payload: Dict[str, Any]):
        """
        Handle task completion - check if it's a robot alert resolution
        """
        task_id = payload.get("task_id")
        result = payload.get("result", {})
        
        # Check if this is an alert we are tracking
        # Or if the task_id starts with ALERT-
        if task_id and task_id.startswith("ALERT-"):
            logger.info(f"📥 Received resolution for {task_id}")
            
            # Extract solution details
            # The result structure from TechSupport is:
            # { "result": { "action": "...", "ticket_id": "...", ... } }
            # Or sometimes nested depending on how BaseAgent wraps it.
            # Let's assume TechSupport returns the solution dict directly as 'result'
            
            solution = result.get("result") if isinstance(result, dict) and "result" in result else result
            
            if not solution:
                logger.warning(f"⚠️ No solution found in task result for {task_id}")
                return

            # Find robot_id from active alerts or parse from task_id
            robot_id = None
            if task_id in self.active_alerts:
                robot_id = self.active_alerts[task_id]["robot_id"]
                # Clean up
                del self.active_alerts[task_id]
            else:
                # Try to parse ALERT-ROBOTID-TIMESTAMP
                parts = task_id.split("-")
                if len(parts) >= 3:
                    robot_id = f"{parts[1]}-{parts[2]}" # Assuming XR25-001 format
            
            if robot_id:
                await self.send_solution_to_robot(robot_id, solution)
            else:
                logger.error(f"❌ Could not determine robot_id for task {task_id}")

    async def send_solution_to_robot(self, robot_id: str, solution: Dict[str, Any]):
        """
        Queue solution for robot to poll
        """
        logger.info(f"🚀 Queuing solution for robot {robot_id}: {solution.get('action')}")
        
        # Construct payload for robot
        payload = {
            "action": solution.get("action", "unknown"),
            "error_code": solution.get("error_code", "UNKNOWN"),
            "ticket_id": solution.get("ticket_id", "UNKNOWN"),
            "agent_id": solution.get("agent_id", "tech_support"),
            "details": solution.get("details", {}),
            "requires_hitl": solution.get("requires_hitl", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in queue
        self.solution_queue[robot_id] = payload
        logger.info(f"✅ Solution queued for {robot_id}")


    async def query_error_code(self, error_code: str) -> dict:
        """Query RAG for error code information"""
        try:
            rag_result = await self.rag_tool.query_knowledge_base(
                question=f"What is error code {error_code}? What are the causes and solutions?",
                context="products",
                department="technical"
            )
            return {"error_code": error_code, "details": rag_result}
        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return {"error_code": error_code, "details": {"error": "RAG query failed"}, "fallback": True}
    
    def classify_error(self, error_code: str, severity: str, sensor_data: Optional[dict] = None) -> dict:
        """Classify error urgency"""
        critical_codes = ["E07", "E08", "E09"]
        temperature = sensor_data.get("temperature", 0) if sensor_data else 0
        
        if error_code in critical_codes or temperature > 60:
            return {"urgency": "critical", "escalate_immediately": True, "reason": "Safety hazard detected"}
        
        high_priority_codes = ["E01", "E02", "E03"]
        if error_code in high_priority_codes or severity == "high":
            return {"urgency": "high", "escalate_immediately": False, "reason": "High priority issue"}
        
        return {"urgency": "medium", "escalate_immediately": False, "reason": "Standard issue"}
    
    async def process_alert(self, alert: RobotAlert) -> Dict[str, Any]:
        """Process incoming robot alert"""
        import time
        start_time = time.time()
    
        logger.info(f"🚨 Alert received: {alert.robot_id} - {alert.error_code}")
    
        try:
            # 1. Query RAG
            error_info = await self.query_error_code(alert.error_code)
        
            # 2. Classify
            classification = self.classify_error(
                error_code=alert.error_code,
                severity=alert.severity,
                sensor_data=alert.sensor_data.dict() if alert.sensor_data else None
            )
        
            #3. Build task for COO
            task_id = f"ALERT-{alert.robot_id}-{int(time.time())}"
        
            # Build context for delegated agent (TechnicalSupportAgent)
            context = {
                "robot_id": alert.robot_id,
                "error_code": alert.error_code,
                "sensor_data": alert.sensor_data.dict() if alert.sensor_data else {},
                "error_details": error_info,
                "classification": classification,
                "escalate_immediately": classification["escalate_immediately"]
            }
        
            task_data = {
                "task_id": task_id,
                "task_type": "robot_alert",
                "robot_id": alert.robot_id,
                "error_code": alert.error_code,
                "severity": classification["urgency"],
                "description": alert.description,
                "timestamp": alert.timestamp,
                "context": context,  # For TechnicalSupportAgent to extract error_code
                "sensor_data": alert.sensor_data.dict() if alert.sensor_data else {},
                "error_details": error_info,
                "classification": classification,
                "escalate_immediately": classification["escalate_immediately"]
            }
        
            # Store active alert
            self.active_alerts[task_id] = {
                "robot_id": alert.robot_id,
                "timestamp": time.time()
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
                logger.info(f"✅ Alert forwarded to COO: {task_id}")
        
            # 5. Audit log
            self.audit_log.log_action(
                action_type=ActionType.MESSAGE_RECEIVED,
                agent_id=self.agent_id,
                details={"robot_id": alert.robot_id, "error_code": alert.error_code},
                severity=ActionType.TICKET_CREATED
            )
        
            # 6. Update metrics
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
        
            return {
                "status": "success",
                "task_id": task_id,
                "urgency": classification["urgency"],
                "forwarded_to": "coo_agent",
                "message": "Alert received and processing started. Solution will be sent to robot asynchronously."
            }
        
        except Exception as e:
            logger.error(f"❌ Alert processing failed: {e}")
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            return {"status": "failed", "error": str(e)}
       
        
            
            
           
            
            
            
            
       
    
    async def process_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process generic task (for BaseAgent compatibility)"""
        return {"status": "success", "message": "Alert Receiver processes alerts via REST API"}



# ============================================================
# MCP SERVER
# ============================================================

from mcp.server.fastmcp import FastMCP, Context

# Initialize FastMCP
mcp = FastMCP("RoboNest Alert Receiver")

# Global agent instance
alert_agent: Optional[AlertReceiverAgent] = None

async def get_agent() -> AlertReceiverAgent:
    """Get or initialize the agent"""
    global alert_agent
    if alert_agent is None:
        # Initialize dependencies
        auth_manager = AuthManager()
        audit_log = AuditLog()
        message_bus = MessageBus(auth_manager=auth_manager, audit_log=audit_log)
        
        # Start Message Bus
        await message_bus.start()
        
        # Initialize Agent
        alert_agent = AlertReceiverAgent(
            auth_manager=auth_manager,
            audit_log=audit_log,
            message_bus=message_bus
        )
        
        # Start Agent (subscribe to topics)
        await alert_agent.start()
        logger.info("✅ Alert Receiver Agent initialized via MCP")
        
    return alert_agent

@mcp.tool()
async def submit_alert(
    robot_id: str,
    error_code: str,
    severity: str,
    description: str,
    sensor_data: Dict[str, Any],
    ctx: Context = None
) -> str:
    """
    Submit a robot alert to the system.
    
    Args:
        robot_id: Unique robot identifier (e.g., XR25-001)
        error_code: Error code (e.g., E01, E02)
        severity: Severity (low, medium, high, critical)
        description: Description of the issue
        sensor_data: Sensor readings (battery, temperature, etc.)
    """
    agent = await get_agent()
    
    # Create RobotAlert object
    alert = RobotAlert(
        robot_id=robot_id,
        error_code=error_code,
        severity=severity,
        description=description,
        sensor_data=SensorData(**sensor_data)
    )
    
    # Process
    result = await agent.process_alert(alert)
    
    if result["status"] == "success":
        if ctx:
            ctx.info(f"Alert processed: {result['task_id']}")
        return f"Alert received. Task ID: {result['task_id']}"
    else:
        raise RuntimeError(f"Failed to process alert: {result.get('error')}")

@mcp.tool()
async def poll_solution(robot_id: str) -> Optional[Dict[str, Any]]:
    """
    Check for pending solutions for a robot.
    
    Args:
        robot_id: Robot identifier
        
    Returns:
        Solution dictionary or None if no solution
    """
    agent = await get_agent()
    
    # Check internal queue (we need to implement a queue in the agent)
    # For now, we'll check the active_alerts or a new solution_queue
    if hasattr(agent, "solution_queue") and robot_id in agent.solution_queue:
        solution = agent.solution_queue.pop(robot_id)
        return solution
        
    return None

if __name__ == "__main__":
    # Run MCP server
    logging.basicConfig(level=logging.INFO)
    mcp.run()