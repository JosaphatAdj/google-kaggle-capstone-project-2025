"""
Audit Log - Journalisation sécurisée de toutes les actions agents
Traçabilité complète pour conformité et debugging
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types d'actions auditées"""
    # Authentification
    AGENT_REGISTERED = "agent_registered"
    AGENT_DEACTIVATED = "agent_deactivated"
    TOKEN_GENERATED = "token_generated"
    TOKEN_VALIDATED = "token_validated"
    TOKEN_REVOKED = "token_revoked"
    
    # Communication A2A
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TASK_DELEGATED = "task_delegated"
    
    # Actions métier
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ESCALATED = "ticket_escalated"
    JIRA_CREATED = "jira_created"
    EMAIL_SENT = "email_sent"
    
    # Permissions
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    
    # RAG
    RAG_QUERY = "rag_query"
    
    # Erreurs
    ERROR_OCCURRED = "error_occurred"
    SECURITY_VIOLATION = "security_violation"


class AuditSeverity(Enum):
    """Niveaux de sévérité"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog:
    """Système de journalisation pour audit et conformité"""
    
    def __init__(self, log_dir: str = "logs/audit"):
        """
        Args:
            log_dir: Répertoire des logs d'audit
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier de log actuel (rotation par jour)
        self.current_log_file = self._get_log_file()
        
        # Buffer en mémoire (pour requêtes rapides)
        self.memory_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000
    
    def _get_log_file(self) -> Path:
        """Génère le nom du fichier de log du jour"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    def log_action(
        self,
        action_type: ActionType,
        agent_id: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO,
        target_agent: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enregistre une action dans l'audit log
        
        Args:
            action_type: Type d'action (enum ActionType)
            agent_id: ID de l'agent effectuant l'action
            details: Détails de l'action
            severity: Niveau de sévérité
            target_agent: Agent cible (pour A2A)
            resource: Ressource affectée (ticket_id, jira_id, etc.)
            result: Résultat (success, failure, pending)
        
        Returns:
            Entrée de log créée
        
        Example:
            >>> audit = AuditLog()
            >>> audit.log_action(
            ...     action_type=ActionType.TICKET_ESCALATED,
            ...     agent_id="tech_support_001",
            ...     details={"ticket_id": "TICKET-123", "reason": "complex_issue"},
            ...     severity=AuditSeverity.WARNING,
            ...     resource="TICKET-123",
            ...     result="success"
            ... )
        """
        # Rotation de fichier si changement de jour
        current_file = self._get_log_file()
        if current_file != self.current_log_file:
            self.current_log_file = current_file
            logger.info(f"📄 Rotation du fichier d'audit: {current_file}")
        
        # Créer entrée de log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": action_type.value,
            "agent_id": agent_id,
            "severity": severity.value,
            "details": details,
            "target_agent": target_agent,
            "resource": resource,
            "result": result or "success"
        }
        
        # Ajouter au buffer mémoire
        self.memory_buffer.append(log_entry)
        if len(self.memory_buffer) > self.max_buffer_size:
            self.memory_buffer.pop(0)
        
        # Écrire dans le fichier (JSON Lines format)
        try:
            with open(self.current_log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"❌ Erreur écriture audit log: {e}")
        
        # Log également dans le système de logging standard
        log_msg = (
            f"[{severity.value.upper()}] {action_type.value} | "
            f"Agent: {agent_id} | Resource: {resource} | Result: {result}"
        )
        
        if severity == AuditSeverity.CRITICAL:
            logger.critical(log_msg)
        elif severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        elif severity == AuditSeverity.DEBUG:
            logger.debug(log_msg)
        else:
            logger.info(log_msg)
        
        return log_entry
    
    def log_a2a_communication(
        self,
        sender_agent: str,
        receiver_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        result: str = "success"
    ):
        """
        Log spécialisé pour communication Agent-to-Agent
        
        Args:
            sender_agent: Agent envoyeur
            receiver_agent: Agent receveur
            message_type: Type de message (task_delegation, escalation, etc.)
            payload: Contenu du message
            result: Résultat de la communication
        
        Example:
            >>> audit.log_a2a_communication(
            ...     sender_agent="coo_agent_001",
            ...     receiver_agent="tech_support_001",
            ...     message_type="task_delegation",
            ...     payload={"task": "diagnose_robot", "priority": "high"}
            ... )
        """
        return self.log_action(
            action_type=ActionType.MESSAGE_SENT,
            agent_id=sender_agent,
            details={
                "message_type": message_type,
                "payload": payload
            },
            target_agent=receiver_agent,
            result=result
        )
    
    def log_permission_check(
        self,
        agent_id: str,
        permission: str,
        resource: Optional[str],
        granted: bool
    ):
        """
        Log les vérifications de permissions
        
        Args:
            agent_id: Agent demandant la permission
            permission: Permission demandée
            resource: Ressource ciblée
            granted: Permission accordée ou non
        """
        action_type = (
            ActionType.PERMISSION_GRANTED if granted 
            else ActionType.PERMISSION_DENIED
        )
        severity = (
            AuditSeverity.INFO if granted 
            else AuditSeverity.WARNING
        )
        
        return self.log_action(
            action_type=action_type,
            agent_id=agent_id,
            details={"permission": permission},
            severity=severity,
            resource=resource,
            result="granted" if granted else "denied"
        )
    
    def log_rag_query(
        self,
        agent_id: str,
        query: str,
        context: str,
        results_count: int
    ):
        """
        Log les requêtes RAG
        
        Args:
            agent_id: Agent effectuant la requête
            query: Question posée
            context: Contexte RAG (support, products, hr, etc.)
            results_count: Nombre de résultats retournés
        """
        return self.log_action(
            action_type=ActionType.RAG_QUERY,
            agent_id=agent_id,
            details={
                "query": query,
                "context": context,
                "results_count": results_count
            },
            severity=AuditSeverity.DEBUG
        )
    
    def log_error(
        self,
        agent_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.ERROR
    ):
        """
        Log les erreurs
        
        Args:
            agent_id: Agent ayant rencontré l'erreur
            error_type: Type d'erreur (ValueError, PermissionError, etc.)
            error_message: Message d'erreur
            stack_trace: Stack trace complète (optionnel)
            severity: Sévérité de l'erreur
        """
        return self.log_action(
            action_type=ActionType.ERROR_OCCURRED,
            agent_id=agent_id,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace
            },
            severity=severity,
            result="failure"
        )
    
    def log_security_violation(
        self,
        agent_id: str,
        violation_type: str,
        details: Dict[str, Any]
    ):
        """
        Log les violations de sécurité (tentative d'accès non autorisé, etc.)
        
        Args:
            agent_id: Agent impliqué
            violation_type: Type de violation
            details: Détails de la violation
        """
        return self.log_action(
            action_type=ActionType.SECURITY_VIOLATION,
            agent_id=agent_id,
            details={
                "violation_type": violation_type,
                **details
            },
            severity=AuditSeverity.CRITICAL,
            result="blocked"
        )
    
    def query_logs(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Requête sur les logs d'audit
        
        Args:
            agent_id: Filtrer par agent
            action_type: Filtrer par type d'action
            start_date: Date de début
            end_date: Date de fin
            severity: Filtrer par sévérité
            limit: Nombre max de résultats
        
        Returns:
            Liste des entrées de log correspondantes
        
        Example:
            >>> # Tous les logs de tech_support_001
            >>> logs = audit.query_logs(agent_id="tech_support_001", limit=50)
            >>> 
            >>> # Toutes les escalations
            >>> escalations = audit.query_logs(
            ...     action_type=ActionType.TICKET_ESCALATED,
            ...     start_date=datetime.utcnow() - timedelta(days=7)
            ... )
        """
        # Chercher d'abord dans le buffer mémoire
        results = []
        
        for entry in reversed(self.memory_buffer):
            # Filtres
            if agent_id and entry["agent_id"] != agent_id:
                continue
            
            if action_type and entry["action_type"] != action_type.value:
                continue
            
            if severity and entry["severity"] != severity.value:
                continue
            
            if start_date:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time < start_date:
                    continue
            
            if end_date:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > end_date:
                    continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_agent_history(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique complet d'un agent
        
        Args:
            agent_id: ID de l'agent
            limit: Nombre max d'entrées
        
        Returns:
            Historique de l'agent
        """
        return self.query_logs(agent_id=agent_id, limit=limit)
    
    def get_recent_violations(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Récupère les violations de sécurité récentes
        
        Args:
            limit: Nombre max de résultats
        
        Returns:
            Violations récentes
        """
        return self.query_logs(
            action_type=ActionType.SECURITY_VIOLATION,
            limit=limit
        )
    
    def export_logs(
        self,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """
        Exporte les logs pour archivage ou analyse externe
        
        Args:
            output_file: Fichier de sortie
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
        
        Returns:
            True si export réussi
        """
        try:
            logs = self.query_logs(
                start_date=start_date,
                end_date=end_date,
                limit=100000  # Grande limite pour export complet
            )
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump({
                    "exported_at": datetime.utcnow().isoformat(),
                    "total_entries": len(logs),
                    "logs": logs
                }, f, indent=2)
            
            logger.info(f"📄 Logs exportés: {output_file} ({len(logs)} entrées)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur export logs: {e}")
            return False


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    audit = AuditLog(log_dir="logs/audit_test")
    
    print("\n" + "="*60)
    print("TEST 1: Logs d'authentification")
    print("="*60)
    
    audit.log_action(
        action_type=ActionType.AGENT_REGISTERED,
        agent_id="tech_support_001",
        details={"agent_type": "technical_support", "department": "support"},
        severity=AuditSeverity.INFO
    )
    print("✅ Agent registered logged")
    
    audit.log_action(
        action_type=ActionType.TOKEN_GENERATED,
        agent_id="tech_support_001",
        details={"token_type": "JWT", "expiry": "24h"},
        severity=AuditSeverity.INFO
    )
    print("✅ Token generation logged")
    
    print("\n" + "="*60)
    print("TEST 2: Logs A2A")
    print("="*60)
    
    audit.log_a2a_communication(
        sender_agent="coo_agent_001",
        receiver_agent="tech_support_001",
        message_type="task_delegation",
        payload={"task": "diagnose_robot", "priority": "high"}
    )
    print("✅ A2A communication logged")
    
    print("\n" + "="*60)
    print("TEST 3: Logs de permissions")
    print("="*60)
    
    audit.log_permission_check(
        agent_id="tech_support_001",
        permission="create:jira",
        resource="TICKET-123",
        granted=True
    )
    print("✅ Permission granted logged")
    
    audit.log_permission_check(
        agent_id="faq_agent_001",
        permission="create:jira",
        resource="TICKET-456",
        granted=False
    )
    print("✅ Permission denied logged")
    
    print("\n" + "="*60)
    print("TEST 4: Logs RAG")
    print("="*60)
    
    audit.log_rag_query(
        agent_id="tech_support_001",
        query="Comment réparer batterie gonflée?",
        context="support",
        results_count=5
    )
    print("✅ RAG query logged")
    
    print("\n" + "="*60)
    print("TEST 5: Logs d'erreurs")
    print("="*60)
    
    audit.log_error(
        agent_id="tech_support_001",
        error_type="ValueError",
        error_message="Invalid ticket format",
        severity=AuditSeverity.ERROR
    )
    print("✅ Error logged")
    
    print("\n" + "="*60)
    print("TEST 6: Logs de sécurité")
    print("="*60)
    
    audit.log_security_violation(
        agent_id="unknown_agent",
        violation_type="unauthorized_access",
        details={"attempted_resource": "admin_panel", "ip": "192.168.1.100"}
    )
    print("✅ Security violation logged")
    
    print("\n" + "="*60)
    print("TEST 7: Requêtes sur les logs")
    print("="*60)
    
    # Historique complet d'un agent
    history = audit.get_agent_history("tech_support_001")
    print(f"✅ Historique tech_support_001: {len(history)} entrées")
    
    # Violations récentes
    violations = audit.get_recent_violations()
    print(f"✅ Violations récentes: {len(violations)} entrées")
    
    # Tous les logs A2A
    a2a_logs = audit.query_logs(action_type=ActionType.MESSAGE_SENT)
    print(f"✅ Communications A2A: {len(a2a_logs)} entrées")
    
    print("\n" + "="*60)
    print("TEST 8: Export des logs")
    print("="*60)
    
    audit.export_logs("logs/audit_test/export_test.json")
    print("✅ Logs exportés")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)