#!/usr/bin/env python3
"""
Point d'entrée pour lancer tout le système RoboNest
Lance: MessageBus, COO Agent, AlertReceiverAgent (MCP Server), TechnicalSupportAgent
"""

import asyncio
import sys
import logging
from pathlib import Path

# Ajouter root au path
sys.path.insert(0, str(Path(__file__).parent))

from agents.coordinator.coo_agent import COOAgent
from agents.alert_receiver.alert_receiver_agent import AlertReceiverAgent
from agents.support.technical_support_agent import TechnicalSupportAgent
from security import AuthManager, AuditLog
from communication.message_bus import MessageBus

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RoboNestSystem:
    """Système complet RoboNest"""
    
    def __init__(self):
        """Initialise le système"""
        logger.info("🚀 Initialisation du système RoboNest...")
        
        # Infrastructure
        self.auth = AuthManager()
        self.audit = AuditLog(log_dir="logs/system")
        self.bus = MessageBus(self.auth, self.audit)
        
        # Agents
        self.alert_receiver = None
        self.coo = None
        self.tech_support = None
        
        logger.info("✅ Infrastructure initialisée")
    
    async def start(self):
        """Démarre tous les agents"""
        logger.info("🎬 Démarrage du système...")
        
        # 1. Démarrer Message Bus
        await self.bus.start()
        logger.info("✅ Message Bus démarré")
        
        # 2. Alert Receiver Agent (MCP Server)
        self.alert_receiver = AlertReceiverAgent(
            agent_id="alert_receiver_001",
            auth_manager=self.auth,
            audit_log=self.audit,
            message_bus=self.bus
        )
        await self.alert_receiver.start()
        logger.info("✅ Alert Receiver Agent démarré (MCP Server)")
        
        # 3. COO Agent
        self.coo = COOAgent(
            agent_id="coo_agent_001",
            auth_manager=self.auth,
            audit_log=self.audit,
            message_bus=self.bus
        )
        await self.coo.start()
        logger.info("✅ COO Agent démarré")
        
        # 4. Technical Support Agent
        self.tech_support = TechnicalSupportAgent(
            agent_id="tech_support_001",
            auth_manager=self.auth,
            message_bus=self.bus
        )
        await self.tech_support.start()
        logger.info("✅ Technical Support Agent démarré")
        
        logger.info("\n" + "="*60)
        logger.info("🎉 SYSTÈME ROBONEST OPÉRATIONNEL")
        logger.info("="*60)
        logger.info("Les agents sont prêts à recevoir des alertes")
        
        # 5. Start MCP HTTP Server for robot connections
        logger.info("🌐 Démarrage du serveur MCP HTTP sur port 8001...")
        await self._start_mcp_server()
        
        logger.info("Lancez le robot séparément avec:")
        logger.info("  python embedded_robot/robot_agent.py")
        logger.info("="*60 + "\n")
    
    async def _start_mcp_server(self):
        """Start MCP HTTP server for robot connections"""
        import uvicorn
        from agents.alert_receiver import mcp_server
        
        # Set the global agent reference in MCP server
        mcp_server.set_agent(self.alert_receiver)
        
        # Configure uvicorn
        config = uvicorn.Config(
            mcp_server.app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run in background task
        self.mcp_server_task = asyncio.create_task(server.serve())
        
        # Wait a bit for server to start
        await asyncio.sleep(1)
        logger.info("✅ MCP HTTP Server démarré sur http://localhost:8001")
    
    async def run_forever(self):
        """Garde le système en cours d'exécution"""
        try:
            # Boucle infinie d'attente
            while True:
                await asyncio.sleep(10)
                
                # Optionnel: afficher des stats périodiquement
                if hasattr(self.coo, 'get_performance_report'):
                    report = self.coo.get_performance_report()
                    logger.info(f"📊 Tâches actives: {report['active_tasks']}, "
                              f"Déléguées: {report['metrics']['tasks_delegated']}, "
                              f"Complétées: {report['metrics']['tasks_completed']}")
        
        except KeyboardInterrupt:
            logger.info("\n⚠️ Interruption détectée (Ctrl+C)")
    
    async def stop(self):
        """Arrête le système proprement"""
        logger.info("🛑 Arrêt du système...")
        
        if self.bus:
            await self.bus.stop()
        
        logger.info("✅ Système arrêté proprement")


async def main():
    """Point d'entrée principal"""
    
    print("\n" + "="*80)
    print(" " * 25 + "🤖 ROBONEST SYSTEM 🤖")
    print("="*80)
    print()
    
    # Créer et démarrer le système
    system = RoboNestSystem()
    await system.start()
    
    # Garder le système actif
    try:
        await system.run_forever()
    finally:
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
