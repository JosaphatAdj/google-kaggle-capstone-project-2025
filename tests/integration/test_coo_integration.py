"""
Test d'intégration COO Agent
Teste l'orchestration complète avec sécurité, communication et RAG
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Ajouter root au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.coordinator.coo_agent import COOAgent
from security import AuthManager, AuditLog
from communication.message_bus import MessageBus, Message
import logging

logging.basicConfig(level=logging.INFO)


class TestCOOIntegration:
    """Tests d'intégration du COO Agent"""
    
    @pytest.fixture
    async def setup_system(self):
        """Setup complet du système"""
        # Infrastructure
        auth = AuthManager()
        audit = AuditLog(log_dir="logs/test")
        bus = MessageBus(auth, audit)
        
        await bus.start()
        
        # COO Agent
        coo = COOAgent(
            agent_id="coo_test_001",
            auth_manager=auth,
            audit_log=audit,
            message_bus=bus
        )
        
        await coo.start()
        
        # Enregistrer des agents simulés
        tech_token = auth.register_agent(
            agent_id="tech_support_test_001",
            agent_type="technical_support",
            department="support"
        )
        
        faq_token = auth.register_agent(
            agent_id="faq_test_001",
            agent_type="faq_responder",
            department="support"
        )
        
        yield {
            "coo": coo,
            "auth": auth,
            "audit": audit,
            "bus": bus,
            "tech_token": tech_token,
            "faq_token": faq_token
        }
        
        # Cleanup
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_task_delegation(self, setup_system):
        """Test délégation de tâche simple"""
        system = await setup_system
        coo = system["coo"]
        bus = system["bus"]
        
        # Simuler nouvelle tâche
        task_msg = Message(
            sender_id="test_router",
            topic="task.new",
            payload={
                "task_id": "TEST-001",
                "task_type": "technical_issue",
                "description": "Robot ne démarre plus",
                "urgency": "high"
            }
        )
        
        await bus.publish(task_msg, coo.token)
        await asyncio.sleep(1)
        
        # Vérifier que tâche a été déléguée
        assert "TEST-001" in coo.active_tasks
        assert coo.performance_metrics["tasks_delegated"] > 0
    
    @pytest.mark.asyncio
    async def test_escalation_handling(self, setup_system):
        """Test gestion d'escalation"""
        system = await setup_system
        coo = system["coo"]
        bus = system["bus"]
        
        # Simuler escalation
        escalation_msg = Message(
            sender_id="tech_support_test_001",
            topic="escalation.request",
            payload={
                "escalation_id": "ESC-001",
                "escalation_type": "technical",
                "severity": "critical",
                "reason": "Batterie gonflée",
                "ticket_id": "TICKET-123"
            }
        )
        
        await bus.publish(escalation_msg, system["tech_token"])
        await asyncio.sleep(1)
        
        # Vérifier que escalation a été traitée
        assert coo.performance_metrics["escalations_handled"] > 0
    
    @pytest.mark.asyncio
    async def test_agent_status_monitoring(self, setup_system):
        """Test monitoring statut agents"""
        system = await setup_system
        coo = system["coo"]
        bus = system["bus"]
        
        # Simuler status update
        status_msg = Message(
            sender_id="tech_support_test_001",
            topic="agent.status",
            payload={
                "agent_id": "tech_support_test_001",
                "agent_status": "busy",
                "current_load": 0.75,
                "active_tasks": 3
            }
        )
        
        await bus.publish(status_msg, system["tech_token"])
        await asyncio.sleep(0.5)
        
        # Vérifier que statut a été enregistré
        assert "tech_support_test_001" in coo.agent_status
        assert coo.agent_status["tech_support_test_001"]["current_load"] == 0.75
    
    @pytest.mark.asyncio
    async def test_performance_report(self, setup_system):
        """Test génération rapport de performance"""
        system = await setup_system
        coo = system["coo"]
        
        # Générer rapport
        report = coo.get_performance_report()
        
        # Vérifier structure
        assert "agent_id" in report
        assert "metrics" in report
        assert "active_tasks" in report
        assert "agent_status_summary" in report
    
    @pytest.mark.asyncio
    async def test_task_completion_flow(self, setup_system):
        """Test flow complet: nouvelle tâche → délégation → complétion"""
        system = await setup_system
        coo = system["coo"]
        bus = system["bus"]
        
        # 1. Nouvelle tâche
        task_msg = Message(
            sender_id="test_router",
            topic="task.new",
            payload={
                "task_id": "TEST-COMPLETE-001",
                "task_type": "faq",
                "description": "Comment reset password?",
                "urgency": "normal"
            }
        )
        
        await bus.publish(task_msg, coo.token)
        await asyncio.sleep(1)
        
        # 2. Simuler complétion
        completion_msg = Message(
            sender_id="faq_test_001",
            topic="task.completed",
            payload={
                "task_id": "TEST-COMPLETE-001",
                "status": "completed",
                "result": {"answer": "Voici la procédure..."}
            }
        )
        
        await bus.publish(completion_msg, system["faq_token"])
        await asyncio.sleep(1)
        
        # Vérifier que tâche marquée comme complétée
        if "TEST-COMPLETE-001" in coo.active_tasks:
            assert coo.active_tasks["TEST-COMPLETE-001"]["status"] == "completed"
        
        assert coo.performance_metrics["tasks_completed"] > 0


def test_coordinator_tools_integration():
    """Test intégration CoordinatorTools avec RAG"""
    from tools.coordinator.coordinator_tools import CoordinatorTools
    
    tools = CoordinatorTools()
    
    # Test assignation agent
    result = tools.determine_agent_assignment(
        task_description="Robot ne démarre plus",
        task_type="technical_issue",
        urgency="high"
    )
    
    assert "assigned_agent" in result
    assert result["assigned_agent"] in ["technical_support", "faq_responder"]
    
    # Test vérification escalation
    escalation = tools.check_escalation_policy(
        issue_type="battery_swollen",
        sentiment="angry",
        severity="critical"
    )
    
    assert "escalate" in escalation
    assert escalation["escalate"] == True  # Batterie gonflée = escalade obligatoire


def test_security_integration():
    """Test intégration sécurité"""
    from security import AuthManager, TokenManager, AuditLog, ActionType
    
    # Setup
    token_manager = TokenManager()
    auth = AuthManager(token_manager)
    audit = AuditLog(log_dir="logs/test")
    
    # Enregistrer agent
    token = auth.register_agent(
        agent_id="test_agent_001",
        agent_type="technical_support",
        department="support"
    )
    
    # Vérifier token
    agent_info = auth.verify_agent(token)
    assert agent_info["agent_id"] == "test_agent_001"
    
    # Vérifier permission
    can_create_jira = auth.check_permission(token, "create:jira")
    assert can_create_jira == True
    
    # Log action
    audit.log_action(
        action_type=ActionType.TICKET_CREATED,
        agent_id="test_agent_001",
        details={"test": "integration"}
    )
    
    # Vérifier log
    logs = audit.query_logs(agent_id="test_agent_001", limit=1)
    assert len(logs) > 0


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTS D'INTÉGRATION COO AGENT")
    print("="*60)
    
    # Test synchrone tools
    print("\nTest 1: Coordinator Tools")
    test_coordinator_tools_integration()
    print("✅ Coordinator Tools OK")
    
    print("\nTest 2: Security Integration")
    test_security_integration()
    print("✅ Security Integration OK")
    
    # Tests async (nécessitent pytest-asyncio)
    print("\n" + "="*60)
    print("Pour tests async complets, exécuter: pytest tests/integration/test_coo_integration.py")
    print("="*60)