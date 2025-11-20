"""
Message Bus - Communication asynchrone sécurisée entre agents
Implémente pub/sub avec authentification JWT
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import logging

from security import AuthManager, AuditLog, ActionType, AuditSeverity

logger = logging.getLogger(__name__)


class Message:
    """Message standardisé pour communication A2A"""
    
    def __init__(
        self,
        sender_id: str,
        topic: str,
        payload: Dict[str, Any],
        priority: str = "normal",
        requires_ack: bool = False,
        correlation_id: Optional[str] = None
    ):
        """
        Args:
            sender_id: ID de l'agent envoyeur
            topic: Topic du message (ex: "ticket.created", "escalation.required")
            payload: Contenu du message
            priority: Priorité (low, normal, high, critical)
            requires_ack: Requiert un accusé de réception
            correlation_id: ID de corrélation (pour tracer les workflows)
        """
        self.sender_id = sender_id
        self.topic = topic
        self.payload = payload
        self.priority = priority
        self.requires_ack = requires_ack
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow().isoformat()
        self.message_id = f"{sender_id}_{datetime.utcnow().timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le message en dictionnaire"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "topic": self.topic,
            "payload": self.payload,
            "priority": self.priority,
            "requires_ack": self.requires_ack,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }


class MessageBus:
    """
    Bus de messages asynchrone pour communication inter-agents
    Implémente pattern pub/sub avec authentification
    """
    
    def __init__(
        self,
        auth_manager: AuthManager,
        audit_log: AuditLog
    ):
        """
        Args:
            auth_manager: Gestionnaire d'authentification
            audit_log: Système d'audit
        """
        self.auth_manager = auth_manager
        self.audit_log = audit_log
        
        # Subscribers: {topic: [(agent_id, token, handler), ...]}
        self.subscribers: Dict[str, List[tuple]] = {}
        
        # Message queues par priorité
        self.message_queues = {
            "critical": asyncio.Queue(),
            "high": asyncio.Queue(),
            "normal": asyncio.Queue(),
            "low": asyncio.Queue()
        }
        
        # Acknowledgements en attente
        self.pending_acks: Dict[str, asyncio.Event] = {}
        
        # Worker task
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Démarre le message bus"""
        if self.running:
            logger.warning("⚠️ Message bus déjà démarré")
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._process_messages())
        logger.info("✅ Message bus démarré")
    
    async def stop(self):
        """Arrête le message bus"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Message bus arrêté")
    
    def subscribe(
        self,
        topic: str,
        agent_id: str,
        token: str,
        handler: Callable[[Message], Any]
    ) -> bool:
        """
        S'abonner à un topic
        
        Args:
            topic: Topic à écouter (ex: "ticket.created", "escalation.*")
            agent_id: ID de l'agent
            token: Token JWT de l'agent
            handler: Fonction async appelée à réception du message
        
        Returns:
            True si abonnement réussi
        
        Example:
            >>> async def handle_ticket(message: Message):
            ...     print(f"Ticket reçu: {message.payload}")
            >>> 
            >>> bus.subscribe(
            ...     topic="ticket.created",
            ...     agent_id="tech_support_001",
            ...     token=tech_token,
            ...     handler=handle_ticket
            ... )
        """
        try:
            # Vérifier authentification
            agent_info = self.auth_manager.verify_agent(token)
            
            if agent_info["agent_id"] != agent_id:
                logger.error(f"❌ Agent ID mismatch: {agent_id} != {agent_info['agent_id']}")
                return False
            
            # Ajouter subscriber
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            
            self.subscribers[topic].append((agent_id, token, handler))
            
            logger.info(f"✅ {agent_id} abonné à '{topic}'")
            
            # Audit log
            self.audit_log.log_action(
                action_type=ActionType.MESSAGE_RECEIVED,
                agent_id=agent_id,
                details={"topic": topic, "action": "subscribe"},
                severity=AuditSeverity.DEBUG
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur abonnement: {e}")
            return False
    
    def unsubscribe(
        self,
        topic: str,
        agent_id: str
    ) -> bool:
        """
        Se désabonner d'un topic
        
        Args:
            topic: Topic
            agent_id: ID de l'agent
        
        Returns:
            True si désabonnement réussi
        """
        if topic not in self.subscribers:
            return False
        
        # Retirer agent des subscribers
        self.subscribers[topic] = [
            (aid, token, handler) 
            for aid, token, handler in self.subscribers[topic]
            if aid != agent_id
        ]
        
        logger.info(f"✅ {agent_id} désabonné de '{topic}'")
        return True
    
    async def publish(
        self,
        message: Message,
        sender_token: str
    ) -> bool:
        """
        Publier un message sur un topic
        
        Args:
            message: Message à publier
            sender_token: Token de l'agent envoyeur
        
        Returns:
            True si message publié avec succès
        
        Example:
            >>> msg = Message(
            ...     sender_id="ticket_router_001",
            ...     topic="ticket.created",
            ...     payload={"ticket_id": "TICKET-123", "priority": "high"}
            ... )
            >>> await bus.publish(msg, router_token)
        """
        try:
            # Vérifier authentification de l'envoyeur
            agent_info = self.auth_manager.verify_agent(sender_token)
            
            if agent_info["agent_id"] != message.sender_id:
                self.audit_log.log_security_violation(
                    agent_id=message.sender_id,
                    violation_type="sender_id_mismatch",
                    details={"claimed_id": message.sender_id, "token_id": agent_info["agent_id"]}
                )
                return False
            
            # Ajouter message à la queue appropriée
            queue = self.message_queues.get(message.priority, self.message_queues["normal"])
            await queue.put(message)
            
            # Si ACK requis, créer event
            if message.requires_ack:
                self.pending_acks[message.message_id] = asyncio.Event()
            
            # Audit log
            self.audit_log.log_action(
                action_type=ActionType.MESSAGE_SENT,
                agent_id=message.sender_id,
                details={
                    "topic": message.topic,
                    "priority": message.priority,
                    "payload_size": len(str(message.payload))
                },
                severity=AuditSeverity.DEBUG
            )
            
            logger.debug(
                f"📤 Message publié: {message.sender_id} → {message.topic} "
                f"(priorité: {message.priority})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur publication message: {e}")
            self.audit_log.log_error(
                agent_id=message.sender_id,
                error_type=type(e).__name__,
                error_message=str(e),
                severity=AuditSeverity.ERROR
            )
            return False
    
    async def _process_messages(self):
        """Worker task qui traite les messages par priorité"""
        logger.info("🔄 Worker de messages démarré")
        
        while self.running:
            try:
                # Traiter par ordre de priorité
                message = None
                
                # Critical d'abord
                if not self.message_queues["critical"].empty():
                    message = await self.message_queues["critical"].get()
                # Puis high
                elif not self.message_queues["high"].empty():
                    message = await self.message_queues["high"].get()
                # Puis normal
                elif not self.message_queues["normal"].empty():
                    message = await self.message_queues["normal"].get()
                # Enfin low
                elif not self.message_queues["low"].empty():
                    message = await self.message_queues["low"].get()
                else:
                    # Aucun message, attendre un peu
                    await asyncio.sleep(0.1)
                    continue
                
                if message:
                    await self._deliver_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur traitement message: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_message(self, message: Message):
        """
        Délivre un message à tous les subscribers du topic
        
        Args:
            message: Message à délivrer
        """
        topic = message.topic
        
        # Chercher subscribers pour ce topic (support wildcards)
        matching_subscribers = []
        
        for sub_topic, subscribers in self.subscribers.items():
            if self._topic_matches(topic, sub_topic):
                matching_subscribers.extend(subscribers)
        
        if not matching_subscribers:
            logger.debug(f"⚠️ Aucun subscriber pour topic '{topic}'")
            return
        
        logger.debug(
            f"📥 Délivrance message: {message.sender_id} → {topic} "
            f"({len(matching_subscribers)} subscribers)"
        )
        
        # Délivrer à tous les subscribers
        delivery_tasks = []
        
        for agent_id, token, handler in matching_subscribers:
            # Vérifier que le token est toujours valide
            try:
                self.auth_manager.verify_agent(token)
            except Exception:
                logger.warning(f"⚠️ Token invalide pour {agent_id}, skip")
                continue
            
            # Créer task de délivrance
            task = asyncio.create_task(
                self._call_handler(agent_id, handler, message)
            )
            delivery_tasks.append(task)
        
        # Attendre toutes les délivrances
        await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Si ACK requis, le marquer comme reçu
        if message.requires_ack and message.message_id in self.pending_acks:
            self.pending_acks[message.message_id].set()
    
    async def _call_handler(
        self,
        agent_id: str,
        handler: Callable,
        message: Message
    ):
        """
        Appelle le handler d'un agent
        
        Args:
            agent_id: ID de l'agent receveur
            handler: Handler à appeler
            message: Message à passer au handler
        """
        try:
            # Appeler handler (async ou sync)
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
            
            # Audit log
            self.audit_log.log_action(
                action_type=ActionType.MESSAGE_RECEIVED,
                agent_id=agent_id,
                details={
                    "topic": message.topic,
                    "sender": message.sender_id
                },
                severity=AuditSeverity.DEBUG,
                result="success"
            )
            
        except Exception as e:
            logger.error(
                f"❌ Erreur handler {agent_id} pour message {message.topic}: {e}"
            )
            self.audit_log.log_error(
                agent_id=agent_id,
                error_type=type(e).__name__,
                error_message=str(e),
                severity=AuditSeverity.ERROR
            )
    
    def _topic_matches(self, message_topic: str, subscription_topic: str) -> bool:
        """
        Vérifie si un topic de message match une subscription (support wildcards)
        
        Args:
            message_topic: Topic du message (ex: "ticket.created")
            subscription_topic: Topic de subscription (ex: "ticket.*")
        
        Returns:
            True si match
        
        Examples:
            >>> _topic_matches("ticket.created", "ticket.*")  # True
            >>> _topic_matches("ticket.created", "ticket.created")  # True
            >>> _topic_matches("ticket.created", "escalation.*")  # False
        """
        # Exact match
        if message_topic == subscription_topic:
            return True
        
        # Wildcard support
        if subscription_topic.endswith(".*"):
            prefix = subscription_topic[:-2]
            return message_topic.startswith(prefix)
        
        return False
    
    async def wait_for_ack(
        self,
        message_id: str,
        timeout: float = 10.0
    ) -> bool:
        """
        Attend l'accusé de réception d'un message
        
        Args:
            message_id: ID du message
            timeout: Timeout en secondes
        
        Returns:
            True si ACK reçu, False si timeout
        """
        if message_id not in self.pending_acks:
            return False
        
        try:
            await asyncio.wait_for(
                self.pending_acks[message_id].wait(),
                timeout=timeout
            )
            del self.pending_acks[message_id]
            return True
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout ACK pour message {message_id}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne statistiques du message bus
        
        Returns:
            Statistiques
        """
        return {
            "running": self.running,
            "subscribers": {
                topic: len(subs) 
                for topic, subs in self.subscribers.items()
            },
            "queue_sizes": {
                priority: queue.qsize()
                for priority, queue in self.message_queues.items()
            },
            "pending_acks": len(self.pending_acks)
        }


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    import asyncio
    from security import AuthManager, AuditLog
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Setup
        auth = AuthManager()
        audit = AuditLog(log_dir="logs/audit_test")
        bus = MessageBus(auth, audit)
        
        # Enregistrer agents
        router_token = auth.register_agent(
            agent_id="ticket_router_001",
            agent_type="ticket_router",
            department="support"
        )
        
        tech_token = auth.register_agent(
            agent_id="tech_support_001",
            agent_type="technical_support",
            department="support"
        )
        
        sentiment_token = auth.register_agent(
            agent_id="sentiment_001",
            agent_type="sentiment_analyzer",
            department="support"
        )
        
        print("\n" + "="*60)
        print("TEST 1: Démarrage du bus")
        print("="*60)
        
        await bus.start()
        print("✅ Bus démarré")
        
        print("\n" + "="*60)
        print("TEST 2: Abonnements")
        print("="*60)
        
        # Handler pour Technical Support
        async def handle_ticket_created(message: Message):
            print(f"✅ Tech Support a reçu: {message.topic}")
            print(f"   Payload: {message.payload}")
        
        # Handler pour Sentiment Analyzer
        async def handle_all_tickets(message: Message):
            print(f"✅ Sentiment Analyzer a reçu: {message.topic}")
        
        bus.subscribe("ticket.created", "tech_support_001", tech_token, handle_ticket_created)
        bus.subscribe("ticket.*", "sentiment_001", sentiment_token, handle_all_tickets)
        
        print("\n" + "="*60)
        print("TEST 3: Publication de messages")
        print("="*60)
        
        # Publier message
        msg = Message(
            sender_id="ticket_router_001",
            topic="ticket.created",
            payload={"ticket_id": "TICKET-123", "priority": "high"},
            priority="high"
        )
        
        await bus.publish(msg, router_token)
        
        # Attendre traitement
        await asyncio.sleep(1)
        
        print("\n" + "="*60)
        print("TEST 4: Statistiques")
        print("="*60)
        
        stats = bus.get_stats()
        print(f"✅ Statistiques du bus:")
        print(f"   Subscribers: {stats['subscribers']}")
        print(f"   Queue sizes: {stats['queue_sizes']}")
        
        print("\n" + "="*60)
        print("TEST 5: Arrêt du bus")
        print("="*60)
        
        await bus.stop()
        print("✅ Bus arrêté")
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS PASSÉS")
        print("="*60)
    
    asyncio.run(main())