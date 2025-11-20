#!/usr/bin/env python3
"""
Script de démonstration COO Agent
Lance le système complet et simule des scénarios réels
"""

import asyncio
import sys
from pathlib import Path
import logging
from datetime import datetime

# Ajouter root au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator.coo_agent import COOAgent
from security import AuthManager, AuditLog
from communication.message_bus import MessageBus, Message
from tools.coordinator.coordinator_tools import CoordinatorTools

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class COODemoSystem:
    """Système de démonstration du COO Agent"""
    
    def __init__(self):
        """Initialise le système"""
        logger.info("🚀 Initialisation du système de démonstration...")
        
        # Infrastructure
        self.auth = AuthManager()
        self.audit = AuditLog(log_dir="logs/demo")
        self.bus = MessageBus(self.auth, self.audit)
        
        # COO Agent
        self.coo = COOAgent(
            agent_id="coo_demo_001",
            auth_manager=self.auth,
            audit_log=self.audit,
            message_bus=self.bus
        )
        
        # Enregistrer agents simulés
        self._register_demo_agents()
        
        logger.info("✅ Système initialisé")
    
    def _register_demo_agents(self):
        """Enregistre des agents pour la démo"""
        
        # Technical Support Agents
        self.tech_token_1 = self.auth.register_agent(
            agent_id="tech_support_demo_001",
            agent_type="technical_support",
            department="support",
            metadata={"specialization": "hardware"}
        )
        
        self.tech_token_2 = self.auth.register_agent(
            agent_id="tech_support_demo_002",
            agent_type="technical_support",
            department="support",
            metadata={"specialization": "software"}
        )
        
        # FAQ Agents
        self.faq_token = self.auth.register_agent(
            agent_id="faq_demo_001",
            agent_type="faq_responder",
            department="support"
        )
        
        # Sentiment Analyzer
        self.sentiment_token = self.auth.register_agent(
            agent_id="sentiment_demo_001",
            agent_type="sentiment_analyzer",
            department="support"
        )
        
        logger.info("✅ Agents démo enregistrés")
    
    async def start(self):
        """Démarre le système"""
        logger.info("🎬 Démarrage du système...")
        
        await self.bus.start()
        await self.coo.start()
        
        # Simuler status updates des agents
        await self._simulate_agent_status_updates()
        
        logger.info("✅ Système démarré et opérationnel")
    
    async def _simulate_agent_status_updates(self):
        """Simule des mises à jour de statut des agents"""
        
        # Tech Support 1 - Moyennement chargé
        await self.bus.publish(
            Message(
                sender_id="tech_support_demo_001",
                topic="agent.status",
                payload={
                    "agent_id": "tech_support_demo_001",
                    "agent_status": "busy",
                    "current_load": 0.60,
                    "active_tasks": 2
                }
            ),
            self.tech_token_1
        )
        
        # Tech Support 2 - Peu chargé
        await self.bus.publish(
            Message(
                sender_id="tech_support_demo_002",
                topic="agent.status",
                payload={
                    "agent_id": "tech_support_demo_002",
                    "agent_status": "idle",
                    "current_load": 0.20,
                    "active_tasks": 0
                }
            ),
            self.tech_token_2
        )
        
        # FAQ Agent - Disponible
        await self.bus.publish(
            Message(
                sender_id="faq_demo_001",
                topic="agent.status",
                payload={
                    "agent_id": "faq_demo_001",
                    "agent_status": "idle",
                    "current_load": 0.10,
                    "active_tasks": 0
                }
            ),
            self.faq_token
        )
        
        await asyncio.sleep(0.5)
    
    async def run_scenario_1_simple_task(self):
        """Scénario 1: Tâche simple FAQ"""
        print("\n" + "="*60)
        print("SCÉNARIO 1: Tâche Simple (FAQ)")
        print("="*60)
        
        task = Message(
            sender_id="demo_router",
            topic="task.new",
            payload={
                "task_id": "DEMO-001",
                "task_type": "general_question",
                "description": "Comment configurer le Wi-Fi sur mon robot?",
                "urgency": "normal",
                "context": {
                    "customer_tier": "standard"
                }
            }
        )
        
        await self.bus.publish(task, self.coo.token)
        await asyncio.sleep(2)
        
        print("✅ Tâche déléguée à FAQ Agent")
        
        # Simuler complétion
        await self.bus.publish(
            Message(
                sender_id="faq_demo_001",
                topic="task.completed",
                payload={
                    "task_id": "DEMO-001",
                    "status": "completed",
                    "result": {
                        "answer": "Procédure de configuration Wi-Fi fournie",
                        "resolution_time": 3
                    }
                }
            ),
            self.faq_token
        )
        
        await asyncio.sleep(1)
        print("✅ Tâche complétée par FAQ Agent")
    
    async def run_scenario_2_technical_issue(self):
        """Scénario 2: Problème technique complexe"""
        print("\n" + "="*60)
        print("SCÉNARIO 2: Problème Technique Complexe")
        print("="*60)
        
        task = Message(
            sender_id="demo_router",
            topic="task.new",
            payload={
                "task_id": "DEMO-002",
                "task_type": "technical_issue",
                "description": "Robot ne démarre plus, batterie chargée à 100%",
                "urgency": "high",
                "context": {
                    "customer_tier": "premium",
                    "robot_model": "XR25"
                }
            }
        )
        
        await self.bus.publish(task, self.coo.token)
        await asyncio.sleep(2)
        
        print("✅ Tâche déléguée à Technical Support Agent")
        
        # Simuler diagnostic
        await asyncio.sleep(1)
        print("🔍 Diagnostic en cours...")
        
        # Simuler complétion
        await self.bus.publish(
            Message(
                sender_id="tech_support_demo_002",
                topic="task.completed",
                payload={
                    "task_id": "DEMO-002",
                    "status": "completed",
                    "result": {
                        "diagnosis": "Carte mère défaillante",
                        "action_taken": "Ticket Jira créé pour R&D",
                        "jira_id": "ROBO-456"
                    }
                }
            ),
            self.tech_token_2
        )
        
        await asyncio.sleep(1)
        print("✅ Diagnostic complété - Ticket Jira créé")
    
    async def run_scenario_3_escalation(self):
        """Scénario 3: Escalation critique"""
        print("\n" + "="*60)
        print("SCÉNARIO 3: Escalation Critique (HITL)")
        print("="*60)
        
        # Tâche critique
        task = Message(
            sender_id="demo_router",
            topic="task.new",
            payload={
                "task_id": "DEMO-003",
                "task_type": "safety_issue",
                "description": "Batterie gonflée détectée, robot dégage chaleur",
                "urgency": "critical",
                "sentiment": "angry",
                "context": {
                    "customer_tier": "enterprise"
                }
            }
        )
        
        await self.bus.publish(task, self.coo.token)
        await asyncio.sleep(2)
        
        print("⚠️ Escalation automatique détectée")
        
        # Agent détecte problème et escalade
        escalation = Message(
            sender_id="tech_support_demo_001",
            topic="escalation.request",
            payload={
                "escalation_id": "ESC-DEMO-001",
                "escalation_type": "safety",
                "severity": "critical",
                "ticket_id": "DEMO-003",
                "reason": "Risque sécurité - batterie gonflée",
                "suggested_action": "HITL_required",
                "sentiment": "angry"
            }
        )
        
        await self.bus.publish(escalation, self.tech_token_1)
        await asyncio.sleep(2)
        
        print("🚨 HITL notifié - Intervention humaine requise")
        print("📧 Email envoyé au support manager")
    
    async def run_scenario_4_load_balancing(self):
        """Scénario 4: Équilibrage de charge"""
        print("\n" + "="*60)
        print("SCÉNARIO 4: Équilibrage de Charge")
        print("="*60)
        
        # Créer plusieurs tâches simultanément
        tasks = [
            ("DEMO-LB-001", "Comment reset password app?", "normal"),
            ("DEMO-LB-002", "Robot aspire mal", "high"),
            ("DEMO-LB-003", "Erreur E04 firmware", "high"),
            ("DEMO-LB-004", "Où acheter accessoires?", "low")
        ]
        
        print(f"📥 Envoi de {len(tasks)} tâches simultanées...")
        
        for task_id, description, urgency in tasks:
            task = Message(
                sender_id="demo_router",
                topic="task.new",
                payload={
                    "task_id": task_id,
                    "task_type": "mixed",
                    "description": description,
                    "urgency": urgency
                }
            )
            await self.bus.publish(task, self.coo.token)
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(3)
        
        # Analyser distribution
        tools = CoordinatorTools()
        loads = {
            "tech_support_demo_001": 0.85,
            "tech_support_demo_002": 0.45,
            "faq_demo_001": 0.30
        }
        
        analysis = tools.analyze_load_distribution(loads)
        
        print("\n📊 Analyse de la charge:")
        print(f"   Charge moyenne: {analysis['average_load']:.2f}")
        
        if not analysis["balanced"]:
            print("   ⚠️ Déséquilibre détecté")
            print(f"   Surchargés: {analysis['overloaded_agents']}")
            print(f"   Sous-utilisés: {analysis['underutilized_agents']}")
            print("   Recommandations:")
            for rec in analysis['recommendations']:
                print(f"   - {rec}")
        else:
            print("   ✅ Charge bien distribuée")
    
    async def show_performance_report(self):
        """Affiche le rapport de performance"""
        print("\n" + "="*60)
        print("RAPPORT DE PERFORMANCE COO AGENT")
        print("="*60)
        
        report = self.coo.get_performance_report()
        
        print(f"\n📊 Métriques:")
        print(f"   Agent ID: {report['agent_id']}")
        print(f"   Tâches actives: {report['active_tasks']}")
        print(f"   Tâches déléguées: {report['metrics']['tasks_delegated']}")
        print(f"   Tâches complétées: {report['metrics']['tasks_completed']}")
        print(f"   Tâches échouées: {report['metrics']['tasks_failed']}")
        print(f"   Escalations traitées: {report['metrics']['escalations_handled']}")
        
        if report['metrics']['tasks_completed'] > 0:
            avg_time = report['metrics']['average_completion_time']
            print(f"   Temps moyen complétion: {avg_time:.1f} minutes")
        
        print(f"\n👥 Agents supervisés:")
        summary = report['agent_status_summary']
        print(f"   Total: {summary['total_agents']}")
        print(f"   Par statut: {summary['agents_by_status']}")
    
    async def show_audit_summary(self):
        """Affiche résumé des logs d'audit"""
        print("\n" + "="*60)
        print("RÉSUMÉ AUDIT LOG")
        print("="*60)
        
        # Logs COO Agent
        coo_logs = self.audit.query_logs(
            agent_id="coo_demo_001",
            limit=10
        )
        
        print(f"\n📝 Dernières actions COO Agent ({len(coo_logs)}):")
        for log in coo_logs[:5]:
            print(f"   [{log['timestamp'][:19]}] {log['action_type']}")
            if 'task_id' in log.get('details', {}):
                print(f"      → Task: {log['details']['task_id']}")
        
        # Logs de tous les agents
        all_logs = self.audit.query_logs(limit=20)
        print(f"\n📋 Total d'actions enregistrées: {len(all_logs)}")
    
    async def stop(self):
        """Arrête le système"""
        logger.info("🛑 Arrêt du système...")
        await self.bus.stop()
        logger.info("✅ Système arrêté")


async def main():
    """Point d'entrée principal"""
    
    print("\n" + "="*80)
    print(" " * 20 + "🤖 DÉMONSTRATION COO AGENT 🤖")
    print("="*80)
    
    # Créer système
    demo = COODemoSystem()
    
    # Démarrer
    await demo.start()
    
    # Attendre stabilisation
    await asyncio.sleep(1)
    
    # Exécuter scénarios
    await demo.run_scenario_1_simple_task()
    await asyncio.sleep(2)
    
    await demo.run_scenario_2_technical_issue()
    await asyncio.sleep(2)
    
    await demo.run_scenario_3_escalation()
    await asyncio.sleep(2)
    
    await demo.run_scenario_4_load_balancing()
    await asyncio.sleep(2)
    
    # Rapports
    await demo.show_performance_report()
    await demo.show_audit_summary()
    
    # Arrêter
    await demo.stop()
    
    print("\n" + "="*80)
    print(" " * 25 + "✅ DÉMONSTRATION TERMINÉE")
    print("="*80)
    print("\n📁 Consultez les logs dans: logs/demo/")
    print("📊 Tous les événements ont été audités et tracés")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())