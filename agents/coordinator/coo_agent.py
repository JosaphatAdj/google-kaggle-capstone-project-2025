"""
COO Agent - Chief Operating Officer Agent
Orchestrateur principal du système multi-agents RoboNest

Responsabilités:
- Délégation intelligente des tâches
- Supervision des performances agents
- Gestion des escalations
- Coordination inter-divisions
- Génération de rapports opérationnels
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from pathlib import Path
import sys

# Ajouter root au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base.base_agent import BaseAgent
from communication.message_bus import MessageBus, Message
from communication.protocols import (
    MessageType, TaskPriority, TaskStatus,
    TaskDelegation, TaskResponse, TaskCompletion,
    EscalationRequest, StatusUpdate,
    MessageFactory, ProtocolValidator
)
from security import AuthManager, AuditLog, ActionType, AuditSeverity
from tools.coordinator.coordinator_tools import CoordinatorTools

logger = logging.getLogger(__name__)


class COOAgent(BaseAgent):
    """
    COO Agent - Orchestrateur du département automatisé
    
    Le COO Agent est le cerveau du système multi-agents. Il:
    1. Reçoit les demandes entrantes (tickets, tâches internes)
    2. Consulte RoboBrain (RAG) pour décisions éclairées
    3. Délègue intelligemment aux agents appropriés
    4. Supervise l'exécution et gère les escalations
    5. Génère des rapports de performance
    """
    
    def __init__(
        self,
        agent_id: str = "coo_agent_001",
        auth_manager: Optional[AuthManager] = None,
        audit_log: Optional[AuditLog] = None,
        message_bus: Optional[MessageBus] = None
    ):
        """
        Initialise le COO Agent
        
        Args:
            agent_id: ID unique du COO Agent
            auth_manager: Gestionnaire d'authentification
            audit_log: Système d'audit
            message_bus: Bus de communication A2A
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="coordinator",
            department="coordinator"
        )
        
        # Sécurité & Communication
        self.auth_manager = auth_manager or AuthManager()
        self.audit_log = audit_log or AuditLog()
        self.message_bus = message_bus
        
        # S'enregistrer et obtenir token
        self.token = self.auth_manager.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            department=self.department,
            metadata={"version": "1.0", "role": "orchestrator"}
        )
        
        # Tools spécialisés (RAG-powered)
        self.coordinator_tools = CoordinatorTools()
        
        # État interne
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Any] = {
            "tasks_delegated": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "escalations_handled": 0,
            "average_completion_time": 0.0
        }
        
        logger.info(f"✅ COO Agent initialisé: {self.agent_id}")
    
    async def start(self):
        """Démarre le COO Agent et ses subscriptions"""
        if not self.message_bus:
            logger.error("❌ Message bus non configuré")
            return
        
        # S'abonner aux topics pertinents
        await self._subscribe_to_topics()
        
        # Démarrer heartbeat
        asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"🚀 COO Agent démarré et opérationnel")
        
        self.audit_log.log_action(
            action_type=ActionType.AGENT_REGISTERED,
            agent_id=self.agent_id,
            details={"status": "started", "subscriptions": "active"},
            severity=AuditSeverity.INFO
        )
    
    async def _subscribe_to_topics(self):
        """S'abonner aux topics du message bus"""
        if not self.message_bus:
            return
        
        # S'abonner à tous les topics pertinents
        topics = [
            "task.new",              # Nouvelles tâches
            "task.completed",        # Tâches terminées
            "task.failed",           # Tâches échouées
            "escalation.request",    # Demandes d'escalation
            "agent.status",          # Statuts des agents
            "system.alert"           # Alertes système
        ]
        
        for topic in topics:
            self.message_bus.subscribe(
                topic=topic,
                agent_id=self.agent_id,
                token=self.token,
                handler=self._handle_message
            )
            logger.debug(f"✅ Abonné au topic: {topic}")
    
    async def _handle_message(self, message: Message):
        """
        Handler principal pour messages A2A
        
        Args:
            message: Message reçu du bus
        """
        try:
            topic = message.topic
            payload = message.payload
            
            logger.debug(f"📥 Message reçu: {topic} de {message.sender_id}")
            
            # Router selon le topic
            if topic == "task.new":
                await self._handle_new_task(payload)
            
            elif topic == "task.completed":
                await self._handle_task_completed(payload)
            
            elif topic == "task.failed":
                await self._handle_task_failed(payload)
            
            elif topic == "escalation.request":
                await self._handle_escalation_request(payload)
            
            elif topic == "agent.status":
                await self._handle_agent_status_update(payload)
            
            elif topic == "system.alert":
                await self._handle_system_alert(payload)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            self.audit_log.log_error(
                agent_id=self.agent_id,
                error_type=type(e).__name__,
                error_message=str(e),
                severity=AuditSeverity.ERROR
            )
    
    async def _handle_new_task(self, payload: Dict[str, Any]):
        """
        Gère une nouvelle tâche entrante
        
        Args:
            payload: Données de la tâche
        """
        task_id = payload.get("task_id")
        task_description = payload.get("description", "")
        task_type = payload.get("task_type", "general")
        urgency = payload.get("urgency", "normal")
        
        logger.info(f"📋 Nouvelle tâche: {task_id} ({task_type}, urgence: {urgency})")
        
        # 1. Consulter RAG pour déterminer l'agent approprié
        assignment = await self.coordinator_tools.determine_agent_assignment(
            task_description=task_description,
            task_type=task_type,
            urgency=urgency,
            context=payload.get("context")
        )
        
        assigned_agent_type = assignment["assigned_agent"]
        
        # 2. Vérifier si escalation immédiate nécessaire
        if "sentiment" in payload:
            escalation_check = await self.coordinator_tools.check_escalation_policy(
                issue_type=task_type,
                sentiment=payload.get("sentiment", "neutral"),
                severity=urgency,
                customer_tier=payload.get("customer_tier", "standard")
            )
            
            if escalation_check["escalate"]:
                logger.warning(
                    f"⚠️ Escalation immédiate requise: {escalation_check['reason']}"
                )
                await self._handle_immediate_escalation(task_id, escalation_check)
                return
        
        # 3. Déléguer la tâche
        await self._delegate_task(
            task_id=task_id,
            assigned_agent_type=assigned_agent_type,
            task_data=payload,
            assignment_reason=assignment["reason"]
        )
        
        # Métriques
        self.performance_metrics["tasks_delegated"] += 1
    
    async def _delegate_task(
        self,
        task_id: str,
        assigned_agent_type: str,
        task_data: Dict[str, Any],
        assignment_reason: str
    ):
        """
        Délègue une tâche à un agent
        
        Args:
            task_id: ID de la tâche
            assigned_agent_type: Type d'agent assigné
            task_data: Données de la tâche
            assignment_reason: Raison de l'assignation
        """
        try:
            # Trouver un agent disponible de ce type
            available_agent = await self._find_available_agent(assigned_agent_type)
            
            if not available_agent:
                logger.warning(
                    f"⚠️ Aucun agent {assigned_agent_type} disponible pour {task_id}"
                )
                # Mettre en queue ou escalader
                await self._queue_task(task_id, assigned_agent_type, task_data)
                return
            
            # Créer message de délégation
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL
            }
            
            delegation_msg = MessageFactory.create_task_delegation(
                sender_id=self.agent_id,
                receiver_id=available_agent,
                task_id=task_id,
                task_type=task_data.get("task_type", "general"),
                description=task_data.get("description", ""),
                priority=priority_map.get(task_data.get("urgency", "normal"), TaskPriority.NORMAL),
                context=task_data.get("context")
            )
            
            # Publier sur le bus
            if self.message_bus:
                msg = Message(
                    sender_id=self.agent_id,
                    topic=f"task.assigned.{assigned_agent_type}",
                    payload=delegation_msg.to_dict(),
                    priority=task_data.get("urgency", "normal"),
                    requires_ack=True,
                    correlation_id=task_id
                )
                
                await self.message_bus.publish(msg, self.token)
            
            # Enregistrer la tâche active
            self.active_tasks[task_id] = {
                "assigned_to": available_agent,
                "assigned_at": datetime.utcnow().isoformat(),
                "status": TaskStatus.ASSIGNED.value,
                "task_data": task_data,
                "assignment_reason": assignment_reason
            }
            
            logger.info(
                f"✅ Tâche {task_id} déléguée à {available_agent} "
                f"(raison: {assignment_reason})"
            )
            
            # Audit log
            self.audit_log.log_action(
                action_type=ActionType.TASK_DELEGATED,
                agent_id=self.agent_id,
                details={
                    "task_id": task_id,
                    "assigned_to": available_agent,
                    "reason": assignment_reason
                },
                target_agent=available_agent,
                resource=task_id,
                severity=AuditSeverity.INFO
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur délégation tâche {task_id}: {e}")
            self.audit_log.log_error(
                agent_id=self.agent_id,
                error_type=type(e).__name__,
                error_message=str(e)
            )
    
    async def _find_available_agent(
        self,
        agent_type: str
    ) -> Optional[str]:
        """
        Trouve un agent disponible d'un type donné
        
        Args:
            agent_type: Type d'agent recherché
        
        Returns:
            ID de l'agent disponible ou None
        """
        # Récupérer tous les agents de ce type
        agents = self.auth_manager.list_active_agents(department=None)
        
        # Filtrer par type
        matching_agents = [
            agent for agent in agents
            if agent["agent_type"] == agent_type
        ]
        
        if not matching_agents:
            return None
        
        # Trouver le moins chargé
        best_agent = None
        lowest_load = 1.0
        
        for agent in matching_agents:
            agent_id = agent["agent_id"]
            status = self.agent_status.get(agent_id, {})
            current_load = status.get("current_load", 0.5)
            
            if current_load < lowest_load:
                lowest_load = current_load
                best_agent = agent_id
        
        # Si tous surchargés (> 0.8), retourner None
        if lowest_load > 0.8:
            logger.warning(f"⚠️ Tous les agents {agent_type} sont surchargés")
            return None
        
        return best_agent or (matching_agents[0]["agent_id"] if matching_agents else None)
    
    async def _handle_task_completed(self, payload: Dict[str, Any]):
        """Gère la complétion d'une tâche"""
        task_id = payload.get("task_id")
        
        if task_id not in self.active_tasks:
            logger.warning(f"⚠️ Tâche inconnue complétée: {task_id}")
            return
        
        task_info = self.active_tasks[task_id]
        task_info["status"] = TaskStatus.COMPLETED.value
        task_info["completed_at"] = datetime.utcnow().isoformat()
        task_info["result"] = payload.get("result")
        
        logger.info(f"✅ Tâche complétée: {task_id} par {task_info['assigned_to']}")
        
        # Métriques
        self.performance_metrics["tasks_completed"] += 1
        
        # Calculer temps de complétion
        assigned_at = datetime.fromisoformat(task_info["assigned_at"])
        completed_at = datetime.fromisoformat(task_info["completed_at"])
        completion_time = (completed_at - assigned_at).total_seconds() / 60  # minutes
        
        # Mettre à jour moyenne
        total_completed = self.performance_metrics["tasks_completed"]
        current_avg = self.performance_metrics["average_completion_time"]
        self.performance_metrics["average_completion_time"] = (
            (current_avg * (total_completed - 1) + completion_time) / total_completed
        )
        
        # Nettoyer après un certain temps (garder historique)
        # Pour l'instant, on garde tout
        
        # Audit
        self.audit_log.log_action(
            action_type=ActionType.TASK_DELEGATED,
            agent_id=self.agent_id,
            details={
                "task_id": task_id,
                "completion_time_minutes": completion_time
            },
            severity=AuditSeverity.INFO
        )
    
    async def _handle_task_failed(self, payload: Dict[str, Any]):
        """Gère l'échec d'une tâche"""
        task_id = payload.get("task_id")
        error = payload.get("error")
        
        if task_id not in self.active_tasks:
            logger.warning(f"⚠️ Tâche inconnue échouée: {task_id}")
            return
        
        task_info = self.active_tasks[task_id]
        task_info["status"] = TaskStatus.FAILED.value
        task_info["failed_at"] = datetime.utcnow().isoformat()
        task_info["error"] = error
        
        logger.error(f"❌ Tâche échouée: {task_id} - {error}")
        
        # Métriques
        self.performance_metrics["tasks_failed"] += 1
        
        # Décider de la réaction: retry ou escalade
        retry_count = task_info.get("retry_count", 0)
        
        if retry_count < 2:  # Max 2 retries
            logger.info(f"🔄 Retry tâche {task_id} (tentative {retry_count + 1})")
            task_info["retry_count"] = retry_count + 1
            
            # Re-déléguer
            await self._delegate_task(
                task_id=task_id,
                assigned_agent_type=task_info["assigned_to"].split("_")[0],  # Extract type
                task_data=task_info["task_data"],
                assignment_reason="Retry après échec"
            )
        else:
            # Escalader
            logger.warning(f"⚠️ Tâche {task_id} échouée après 2 retries - escalade")
            await self._escalate_failed_task(task_id, task_info)
    
    async def _handle_escalation_request(self, payload: Dict[str, Any]):
        """Gère une demande d'escalation"""
        escalation_id = payload.get("escalation_id")
        escalation_type = payload.get("escalation_type")
        severity = payload.get("severity")
        reason = payload.get("reason")
        
        logger.warning(
            f"⚠️ Escalation reçue: {escalation_id} "
            f"(type: {escalation_type}, sévérité: {severity})"
        )
        
        # Métriques
        self.performance_metrics["escalations_handled"] += 1
        
        # Consulter RAG pour politique d'escalation
        escalation_decision = await self.coordinator_tools.check_escalation_policy(
            issue_type=escalation_type,
            sentiment=payload.get("sentiment", "neutral"),
            severity=severity
        )
        
        if escalation_decision["escalation_type"] == "HITL":
            # Escalade vers humain (email notification)
            await self._notify_human_escalation(payload, escalation_decision)
        else:
            # Escalade technique ou manager
            await self._handle_internal_escalation(payload, escalation_decision)
        
        # Audit
        self.audit_log.log_action(
            action_type=ActionType.TICKET_ESCALATED,
            agent_id=self.agent_id,
            details={
                "escalation_id": escalation_id,
                "type": escalation_type,
                "decision": escalation_decision
            },
            severity=AuditSeverity.WARNING
        )
    
    async def _handle_agent_status_update(self, payload: Dict[str, Any]):
        """Met à jour le statut d'un agent"""
        agent_id = payload.get("agent_id")
        
        if agent_id:
            self.agent_status[agent_id] = {
                "status": payload.get("agent_status", "unknown"),
                "current_load": payload.get("current_load", 0.0),
                "active_tasks": payload.get("active_tasks", 0),
                "last_update": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"📊 Statut agent mis à jour: {agent_id}")
    
    async def _handle_system_alert(self, payload: Dict[str, Any]):
        """Gère une alerte système"""
        alert_type = payload.get("alert_type")
        severity = payload.get("severity")
        
        logger.warning(f"🚨 Alerte système: {alert_type} (sévérité: {severity})")
        
        # Log dans audit
        self.audit_log.log_action(
            action_type=ActionType.ERROR_OCCURRED,
            agent_id=self.agent_id,
            details=payload,
            severity=AuditSeverity.WARNING if severity == "high" else AuditSeverity.ERROR
        )
    
    async def _queue_task(
        self,
        task_id: str,
        agent_type: str,
        task_data: Dict[str, Any]
    ):
        """Met une tâche en queue si aucun agent disponible"""
        logger.info(f"📥 Tâche {task_id} mise en queue pour {agent_type}")
        # TODO: Implémenter queue persistante
    
    async def _handle_immediate_escalation(
        self,
        task_id: str,
        escalation_info: Dict[str, Any]
    ):
        """Gère une escalation immédiate (critique)"""
        logger.critical(
            f"🚨 ESCALATION IMMÉDIATE: {task_id} - {escalation_info['reason']}"
        )
        # TODO: Notification email/SMS immédiate
    
    async def _escalate_failed_task(
        self,
        task_id: str,
        task_info: Dict[str, Any]
    ):
        """Escalade une tâche qui a échoué plusieurs fois"""
        logger.error(f"🚨 Escalade tâche échouée: {task_id}")
        # TODO: Notification manager + création ticket Jira
    
    async def _notify_human_escalation(
        self,
        escalation_data: Dict[str, Any],
        decision: Dict[str, Any]
    ):
        """Notifie un humain d'une escalation HITL"""
        logger.critical(f"👤 HITL requis: {escalation_data.get('escalation_id')}")
        # TODO: Envoi email via Gmail tool
    
    async def _handle_internal_escalation(
        self,
        escalation_data: Dict[str, Any],
        decision: Dict[str, Any]
    ):
        """Gère une escalation interne (non-HITL)"""
        logger.info(f"📈 Escalation interne: {decision['escalation_type']}")
        # TODO: Réassigner à agent senior
    
    async def _heartbeat_loop(self):
        """Envoie des heartbeats périodiques"""
        while True:
            try:
                await asyncio.sleep(60)  # Toutes les minutes
                
                if self.message_bus:
                    status_msg = Message(
                        sender_id=self.agent_id,
                        topic="agent.heartbeat",
                        payload={
                            "timestamp": datetime.utcnow().isoformat(),
                            "active_tasks": len(self.active_tasks),
                            "metrics": self.performance_metrics
                        }
                    )
                    await self.message_bus.publish(status_msg, self.token)
                
                logger.debug("💓 Heartbeat envoyé")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur heartbeat: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de performance du COO Agent
        
        Returns:
            Rapport complet
        """
        return {
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "active_tasks": len(self.active_tasks),
            "metrics": self.performance_metrics,
            "agent_status_summary": {
                "total_agents": len(self.agent_status),
                "agents_by_status": self._count_agents_by_status()
            }
        }
    
    def _count_agents_by_status(self) -> Dict[str, int]:
        """Compte les agents par statut"""
        counts = {"idle": 0, "busy": 0, "error": 0, "unknown": 0}
        
        for status_info in self.agent_status.values():
            status = status_info.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        
        return counts


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    import asyncio
    from security import AuthManager, AuditLog
    from communication.message_bus import MessageBus
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Setup
        auth = AuthManager()
        audit = AuditLog(log_dir="logs/audit_test")
        bus = MessageBus(auth, audit)
        
        await bus.start()
        
        # Créer COO Agent
        coo = COOAgent(
            agent_id="coo_agent_001",
            auth_manager=auth,
            audit_log=audit,
            message_bus=bus
        )
        
        await coo.start()
        
        print("\n" + "="*60)
        print("COO AGENT OPÉRATIONNEL")
        print("="*60)
        
        # Simuler une nouvelle tâche
        new_task = Message(
            sender_id="ticket_router_001",
            topic="task.new",
            payload={
                "task_id": "TASK-001",
                "task_type": "technical_issue",
                "description": "Robot ne démarre plus",
                "urgency": "high",
                "context": {"ticket_id": "TICKET-123"}
            }
        )
        
        await bus.publish(new_task, coo.token)
        
        # Attendre traitement
        await asyncio.sleep(2)
        
        # Rapport de performance
        report = coo.get_performance_report()
        print("\n" + "="*60)
        print("RAPPORT DE PERFORMANCE")
        print("="*60)
        print(f"Tâches actives: {report['active_tasks']}")
        print(f"Tâches déléguées: {report['metrics']['tasks_delegated']}")
        print(f"Tâches complétées: {report['metrics']['tasks_completed']}")
        
        await bus.stop()
        
        print("\n" + "="*60)
        print("✅ TEST TERMINÉ")
        print("="*60)
    
    asyncio.run(main())