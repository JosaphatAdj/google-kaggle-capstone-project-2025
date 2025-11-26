"""
HTTP MCP Client methods for EmbeddedRobotAgent
Replace the stdio MCP connection with HTTP calls
"""
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8001"


async def send_alert_http(robot_id: str, error_code: str, severity: str, description: str, sensors: Dict[str, Any]) -> str:
    """Send alert via HTTP to MCP server"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/mcp/tools/submit_alert",
                params={
                    "robot_id": robot_id,
                    "error_code": error_code,
                    "severity": severity,
                    "description": description
                },
                json=sensors  # sensor_data in body
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Alert sent via HTTP MCP: {result['content']}")
                return result['content']
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ MCP Alert failed: {error_msg}")
                raise Exception(error_msg)
                
    except Exception as e:
        logger.error(f"❌ Failed to send alert: {e}")
        raise


async def poll_solution_http(robot_id: str) -> Dict[str, Any]:
    """Poll for solution via HTTP from MCP server"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/mcp/tools/poll_solution",
                params={"robot_id": robot_id}
            )
            
            if response.status_code == 200:
                solution = response.json()
                if solution:
                    logger.info(f"📥 Solution received via HTTP MCP")
                return solution
            else:
                logger.warning(f"⚠️ Poll failed: HTTP {response.status_code}")
                return None
                
    except Exception as e:
        logger.debug(f"Poll error: {e}")
        return None
