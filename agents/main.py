"""
Main System - Single entry point for entire system
Creates: Message Bus + COO + Technical Support + Alert Receiver (A2A)
"""
import asyncio
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from communication.message_bus import MessageBus
from security import AuthManager, AuditLog
from agents.coordinator.coo_agent import COOAgent
from agents.support.technical_support_agent import TechnicalSupportAgent

# Pour Alert Receiver A2A
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google import genai
from google.genai import types
import uvicorn

# Import de la fonction de création Alert Receiver
from agents.alert_receiver.alert_receiver_a2a import (
    create_alert_receiver_agent, 
    initialize_infrastructure,
    alert_state
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Single entry point - creates ONE Message Bus for all agents"""
    
    logger.info("\n" + "="*70)
    logger.info("  🚀 ROBONEST - UNIFIED SYSTEM STARTUP")
    logger.info("="*70)
    
    try:
        # 1. Initialize infrastructure (ONE Message Bus)
        logger.info("\n📦 Initializing shared infrastructure...")
        await initialize_infrastructure()  # Crée LE Message Bus
        
        shared_bus = alert_state.message_bus  # Référence partagée
        shared_auth = alert_state.auth_manager
        shared_audit = alert_state.audit_log
        
        logger.info("✅ Shared Message Bus created")
        
        # 2. Start COO Agent (using shared bus)
        logger.info("\n🧠 Starting COO Agent...")
        coo_agent = COOAgent(
            agent_id="coo_agent_001",
            auth_manager=shared_auth,
            audit_log=shared_audit,
            message_bus=shared_bus  # ← MÊME instance
        )
        await coo_agent.start()
        logger.info("✅ COO Agent operational")
        
        # 3. Start Technical Support Agent (using shared bus)
        logger.info("\n🔧 Starting Technical Support Agent...")
        tech_support = TechnicalSupportAgent(
            agent_id="tech_support_001",
            auth_manager=shared_auth,
            message_bus=shared_bus  # ← MÊME instance
        )
        await tech_support.start()
        logger.info("✅ Technical Support Agent operational")
        
        # 4. Create Alert Receiver Agent (using shared bus - already done in initialize)
        logger.info("\n📡 Creating Alert Receiver Agent...")
        retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )
        
        alert_receiver = create_alert_receiver_agent(retry_config)
        logger.info("✅ Alert Receiver Agent created")
        
        # 5. Expose Alert Receiver as A2A server
        logger.info("\n🌐 Exposing Alert Receiver via A2A...")
        app = to_a2a(alert_receiver, port=8000)
        logger.info("✅ A2A Server configured on port 8000")
        
        # 6. System ready
        logger.info("\n" + "="*70)
        logger.info("  ✅ UNIFIED SYSTEM OPERATIONAL")
        logger.info("="*70)
        logger.info("\n📋 Active Services:")
        logger.info("   • Message Bus (SHARED)")
        logger.info("   • COO Agent")
        logger.info("   • Technical Support Agent")
        logger.info("   • Alert Receiver (A2A Server on :8000)")
        logger.info("\n💡 All agents share the SAME Message Bus instance")
        logger.info("="*70 + "\n")
        
        # 7. Launch A2A server (blocking)
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Shutdown signal received...")
        
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        raise
        
    finally:
        logger.info("🧹 Cleaning up...")
        if 'shared_bus' in locals():
            await shared_bus.stop()
        logger.info("✅ System stopped\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass