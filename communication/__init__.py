"""
Communication Module - Infrastructure de communication A2A
"""

from .message_bus import MessageBus, Message
from .protocols import (
    MessageType,
    TaskPriority,
    TaskStatus,
    A2AMessage,
    TaskDelegation,
    TaskResponse,
    TaskCompletion,
    EscalationRequest,
    DataShare,
    KnowledgeQuery,
    KnowledgeResponse,
    StatusUpdate,
    ProtocolValidator,
    MessageFactory
)

__all__ = [
    "MessageBus",
    "Message",
    "MessageType",
    "TaskPriority",
    "TaskStatus",
    "A2AMessage",
    "TaskDelegation",
    "TaskResponse",
    "TaskCompletion",
    "EscalationRequest",
    "DataShare",
    "KnowledgeQuery",
    "KnowledgeResponse",
    "StatusUpdate",
    "ProtocolValidator",
    "MessageFactory"
]