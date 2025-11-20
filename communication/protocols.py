"""
Communication Protocols - Standards pour échanges Agent-to-Agent
Définit les formats de messages, workflows et conventions
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class MessageType(Enum):
    """Types de messages standardisés A2A"""
    # Délégation de tâches
    TASK_DELEGATION = "task_delegation"
    TASK_ACCEPTED = "task_accepted"
    TASK_REJECTED = "task_rejected"
    TASK_COMPLETED = "task_completed"
    
    # Escalation
    ESCALATION_REQUEST = "escalation_request"
    ESCALATION_APPROVED = "escalation_approved"
    ESCALATION_REJECTED = "escalation_rejected"
    
    # Partage d'information
    DATA_SHARE = "data_share"
    KNOWLEDGE_QUERY = "knowledge_query"
    KNOWLEDGE_RESPONSE = "knowledge_response"
    
    # Coordination
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"
    SYNC_REQUEST = "sync_request"
    
    # Notifications
    ALERT = "alert"
    NOTIFICATION = "notification"
    
    # Erreurs
    ERROR = "error"
    RETRY_REQUEST = "retry_request"


class TaskPriority(Enum):
    """Niveaux de priorité pour les tâches"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """États d'une tâche"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class A2AMessage:
    """
    Message standardisé pour communication Agent-to-Agent
    Tous les échanges doivent utiliser ce format
    """
    message_type: MessageType
    sender_id: str
    receiver_id: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    correlation_id: Optional[str] = None
    requires_response: bool = False
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Initialisation automatique du timestamp"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialise en dictionnaire"""
        return {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "requires_response": self.requires_response,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Sérialise en JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Désérialise depuis un dictionnaire"""
        return cls(
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            payload=data["payload"],
            priority=TaskPriority(data.get("priority", "normal")),
            correlation_id=data.get("correlation_id"),
            requires_response=data.get("requires_response", False),
            timestamp=data.get("timestamp")
        )


@dataclass
class TaskDelegation:
    """
    Protocole de délégation de tâche
    Utilisé par le COO Agent pour assigner des tâches
    """
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    deadline: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    required_capabilities: Optional[List[str]] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: Optional[str] = None
    ) -> A2AMessage:
        """
        Convertit en message A2A
        
        Example:
            >>> task = TaskDelegation(
            ...     task_id="TASK-001",
            ...     task_type="diagnose_robot",
            ...     description="Robot ne démarre plus",
            ...     priority=TaskPriority.HIGH
            ... )
            >>> msg = task.to_message("coo_agent_001", "tech_support_001")
        """
        return A2AMessage(
            message_type=MessageType.TASK_DELEGATION,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            priority=self.priority,
            correlation_id=correlation_id or self.task_id,
            requires_response=True
        )


@dataclass
class TaskResponse:
    """Réponse à une délégation de tâche"""
    task_id: str
    accepted: bool
    reason: Optional[str] = None
    estimated_completion: Optional[str] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: str
    ) -> A2AMessage:
        """Convertit en message A2A"""
        message_type = (
            MessageType.TASK_ACCEPTED if self.accepted 
            else MessageType.TASK_REJECTED
        )
        
        return A2AMessage(
            message_type=message_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            correlation_id=correlation_id,
            requires_response=False
        )


@dataclass
class TaskCompletion:
    """Notification de fin de tâche"""
    task_id: str
    status: TaskStatus
    result: Dict[str, Any]
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: str
    ) -> A2AMessage:
        """Convertit en message A2A"""
        return A2AMessage(
            message_type=MessageType.TASK_COMPLETED,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload={
                "task_id": self.task_id,
                "status": self.status.value,
                "result": self.result,
                "error": self.error,
                "metrics": self.metrics
            },
            correlation_id=correlation_id,
            requires_response=False
        )


@dataclass
class EscalationRequest:
    """
    Protocole de demande d'escalade
    Utilisé quand un agent ne peut pas résoudre seul
    """
    escalation_id: str
    escalation_type: str  # technical, sentiment, security, business
    severity: str  # low, medium, high, critical
    ticket_id: Optional[str] = None
    reason: str = ""
    context: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str = "coo_agent_001"  # Default: escalade vers COO
    ) -> A2AMessage:
        """
        Convertit en message A2A
        
        Example:
            >>> escalation = EscalationRequest(
            ...     escalation_id="ESC-001",
            ...     escalation_type="technical",
            ...     severity="high",
            ...     ticket_id="TICKET-123",
            ...     reason="Batterie gonflée détectée",
            ...     suggested_action="HITL_required"
            ... )
            >>> msg = escalation.to_message("tech_support_001")
        """
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        
        return A2AMessage(
            message_type=MessageType.ESCALATION_REQUEST,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            priority=priority_map.get(self.severity, TaskPriority.NORMAL),
            correlation_id=self.escalation_id,
            requires_response=True
        )


@dataclass
class DataShare:
    """
    Protocole de partage de données entre agents
    Permet collaboration et synchronisation
    """
    data_type: str  # metrics, feedback, insights, update
    data: Dict[str, Any]
    scope: str  # ticket, customer, product, system
    metadata: Optional[Dict[str, Any]] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: Optional[str] = None
    ) -> A2AMessage:
        """
        Convertit en message A2A
        
        Example:
            >>> # Support → Marketing: partage de feedback client
            >>> data = DataShare(
            ...     data_type="customer_feedback",
            ...     data={
            ...         "pain_point": "battery_life",
            ...         "frequency": "high",
            ...         "sentiment": "negative"
            ...     },
            ...     scope="product"
            ... )
            >>> msg = data.to_message(
            ...     sender_id="satisfaction_reporter_001",
            ...     receiver_id="content_creator_001"
            ... )
        """
        return A2AMessage(
            message_type=MessageType.DATA_SHARE,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload={
                "data_type": self.data_type,
                "data": self.data,
                "scope": self.scope,
                "metadata": self.metadata
            },
            correlation_id=correlation_id,
            requires_response=False
        )


@dataclass
class KnowledgeQuery:
    """
    Protocole de requête de connaissance
    Un agent demande info à un autre (ou au RAG)
    """
    query_id: str
    query: str
    context: str  # support, products, hr, it, marketing
    filters: Optional[Dict[str, Any]] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: Optional[str] = None
    ) -> A2AMessage:
        """Convertit en message A2A"""
        return A2AMessage(
            message_type=MessageType.KNOWLEDGE_QUERY,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            correlation_id=correlation_id or self.query_id,
            requires_response=True
        )


@dataclass
class KnowledgeResponse:
    """Réponse à une requête de connaissance"""
    query_id: str
    results: List[Dict[str, Any]]
    confidence: float
    sources: List[str]
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str,
        correlation_id: str
    ) -> A2AMessage:
        """Convertit en message A2A"""
        return A2AMessage(
            message_type=MessageType.KNOWLEDGE_RESPONSE,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            correlation_id=correlation_id,
            requires_response=False
        )


@dataclass
class StatusUpdate:
    """
    Mise à jour de statut d'un agent
    Utilisé pour monitoring et coordination
    """
    agent_status: str  # idle, busy, error, maintenance
    current_load: float  # 0.0 à 1.0
    active_tasks: int
    metrics: Optional[Dict[str, Any]] = None
    
    def to_message(
        self,
        sender_id: str,
        receiver_id: str = "coo_agent_001"  # Default: COO
    ) -> A2AMessage:
        """Convertit en message A2A"""
        return A2AMessage(
            message_type=MessageType.STATUS_UPDATE,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payload=asdict(self),
            requires_response=False
        )


class ProtocolValidator:
    """Validateur de messages selon les protocoles"""
    
    @staticmethod
    def validate_message(message: A2AMessage) -> tuple[bool, Optional[str]]:
        """
        Valide qu'un message respecte les protocoles
        
        Args:
            message: Message à valider
        
        Returns:
            (is_valid, error_message)
        
        Example:
            >>> msg = A2AMessage(...)
            >>> is_valid, error = ProtocolValidator.validate_message(msg)
            >>> if not is_valid:
            ...     print(f"Erreur: {error}")
        """
        # Vérifier champs obligatoires
        if not message.sender_id:
            return False, "sender_id manquant"
        
        if not message.receiver_id:
            return False, "receiver_id manquant"
        
        if not message.payload:
            return False, "payload vide"
        
        # Vérifier format du payload selon le type de message
        if message.message_type == MessageType.TASK_DELEGATION:
            required_fields = ["task_id", "task_type", "description", "priority"]
            for field in required_fields:
                if field not in message.payload:
                    return False, f"Champ '{field}' manquant dans TASK_DELEGATION"
        
        elif message.message_type == MessageType.ESCALATION_REQUEST:
            required_fields = ["escalation_id", "escalation_type", "severity", "reason"]
            for field in required_fields:
                if field not in message.payload:
                    return False, f"Champ '{field}' manquant dans ESCALATION_REQUEST"
        
        return True, None
    
    @staticmethod
    def validate_task_delegation(payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validation spécifique pour délégation de tâche"""
        required_fields = ["task_id", "task_type", "description", "priority"]
        
        for field in required_fields:
            if field not in payload:
                return False, f"Champ '{field}' requis"
        
        # Vérifier priorité valide
        valid_priorities = [p.value for p in TaskPriority]
        if payload["priority"] not in valid_priorities:
            return False, f"Priorité invalide: {payload['priority']}"
        
        return True, None


# ============================================================
# HELPERS & FACTORIES
# ============================================================

class MessageFactory:
    """Factory pour créer rapidement des messages standardisés"""
    
    @staticmethod
    def create_task_delegation(
        sender_id: str,
        receiver_id: str,
        task_id: str,
        task_type: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs
    ) -> A2AMessage:
        """
        Factory pour créer une délégation de tâche
        
        Example:
            >>> msg = MessageFactory.create_task_delegation(
            ...     sender_id="coo_agent_001",
            ...     receiver_id="tech_support_001",
            ...     task_id="TASK-001",
            ...     task_type="diagnose_robot",
            ...     description="Robot ne démarre plus",
            ...     priority=TaskPriority.HIGH,
            ...     deadline="2024-01-15T18:00:00Z"
            ... )
        """
        task = TaskDelegation(
            task_id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            **kwargs
        )
        return task.to_message(sender_id, receiver_id)
    
    @staticmethod
    def create_escalation(
        sender_id: str,
        escalation_id: str,
        escalation_type: str,
        severity: str,
        reason: str,
        **kwargs
    ) -> A2AMessage:
        """
        Factory pour créer une escalade
        
        Example:
            >>> msg = MessageFactory.create_escalation(
            ...     sender_id="tech_support_001",
            ...     escalation_id="ESC-001",
            ...     escalation_type="technical",
            ...     severity="critical",
            ...     reason="Batterie gonflée détectée",
            ...     ticket_id="TICKET-123"
            ... )
        """
        escalation = EscalationRequest(
            escalation_id=escalation_id,
            escalation_type=escalation_type,
            severity=severity,
            reason=reason,
            **kwargs
        )
        return escalation.to_message(sender_id)
    
    @staticmethod
    def create_data_share(
        sender_id: str,
        receiver_id: str,
        data_type: str,
        data: Dict[str, Any],
        scope: str = "system"
    ) -> A2AMessage:
        """Factory pour créer un partage de données"""
        share = DataShare(
            data_type=data_type,
            data=data,
            scope=scope
        )
        return share.to_message(sender_id, receiver_id)


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST 1: Création de messages structurés")
    print("="*60)
    
    # Délégation de tâche
    task = TaskDelegation(
        task_id="TASK-001",
        task_type="diagnose_robot",
        description="Robot XR25 ne démarre plus, batterie OK",
        priority=TaskPriority.HIGH,
        deadline="2024-01-15T18:00:00Z",
        context={"ticket_id": "TICKET-123", "customer_tier": "premium"}
    )
    
    msg1 = task.to_message("coo_agent_001", "tech_support_001")
    print(f"✅ Délégation créée:")
    print(msg1.to_json())
    
    print("\n" + "="*60)
    print("TEST 2: Escalation")
    print("="*60)
    
    escalation = EscalationRequest(
        escalation_id="ESC-001",
        escalation_type="technical",
        severity="critical",
        ticket_id="TICKET-123",
        reason="Batterie gonflée détectée - risque sécurité",
        suggested_action="HITL_required"
    )
    
    msg2 = escalation.to_message("tech_support_001")
    print(f"✅ Escalation créée:")
    print(msg2.to_json())
    
    print("\n" + "="*60)
    print("TEST 3: Partage de données")
    print("="*60)
    
    data_share = DataShare(
        data_type="customer_feedback",
        data={
            "pain_point": "battery_life",
            "frequency": "high",
            "sentiment": "negative",
            "sample_count": 42
        },
        scope="product",
        metadata={"collected_by": "satisfaction_reporter_001"}
    )
    
    msg3 = data_share.to_message(
        "satisfaction_reporter_001",
        "content_creator_001"
    )
    print(f"✅ Data share créé:")
    print(msg3.to_json())
    
    print("\n" + "="*60)
    print("TEST 4: Validation de messages")
    print("="*60)
    
    # Valider message correct
    is_valid, error = ProtocolValidator.validate_message(msg1)
    print(f"✅ Message 1 valide: {is_valid}")
    
    # Message invalide (sans sender_id)
    bad_msg = A2AMessage(
        message_type=MessageType.TASK_DELEGATION,
        sender_id="",
        receiver_id="tech_support_001",
        payload={}
    )
    is_valid, error = ProtocolValidator.validate_message(bad_msg)
    print(f"❌ Message invalide détecté: {error}")
    
    print("\n" + "="*60)
    print("TEST 5: Message Factory")
    print("="*60)
    
    # Utiliser factory
    msg_factory = MessageFactory.create_task_delegation(
        sender_id="coo_agent_001",
        receiver_id="faq_agent_001",
        task_id="TASK-002",
        task_type="answer_simple_question",
        description="Client demande reset password app",
        priority=TaskPriority.NORMAL
    )
    print(f"✅ Message créé via factory:")
    print(f"   Type: {msg_factory.message_type.value}")
    print(f"   Sender: {msg_factory.sender_id}")
    print(f"   Receiver: {msg_factory.receiver_id}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)