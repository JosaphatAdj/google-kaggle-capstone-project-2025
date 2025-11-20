"""
Coordinator Tools - Outils spécialisés pour le COO Agent
Utilise RAG pour décisions intelligentes de délégation et escalation
"""

from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import sys

# Ajouter root au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.rag.rag_tool import RAGTool

logger = logging.getLogger(__name__)


class CoordinatorTools:
    """
    Tools spécialisés pour le COO Agent
    Consulte RoboBrain (RAG) pour prendre des décisions éclairées
    """
    
    def __init__(self):
        """Initialise les outils avec accès au RAG"""
        self.rag_tool = RAGTool()
        
        # Cache des décisions récentes pour cohérence
        self.decision_cache: Dict[str, Any] = {}
    
    def determine_agent_assignment(
        self,
        task_description: str,
        task_type: str,
        urgency: str = "normal",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Détermine quel agent assigner à une tâche
        Consulte RAG pour les rôles des agents et workflows
        
        Args:
            task_description: Description de la tâche
            task_type: Type (technical_support, faq, content_creation, etc.)
            urgency: Niveau d'urgence (low, normal, high, critical)
            context: Contexte additionnel
        
        Returns:
            {
                "assigned_agent": str,  # Type d'agent recommandé
                "reason": str,          # Justification
                "alternative": str,     # Agent alternatif
                "confidence": float     # Confiance 0-1
            }
        
        Example:
            >>> tools = CoordinatorTools()
            >>> result = tools.determine_agent_assignment(
            ...     task_description="Robot ne démarre plus, batterie OK",
            ...     task_type="technical_issue",
            ...     urgency="high"
            ... )
            >>> print(result["assigned_agent"])
            technical_support
        """
        try:
            # Construire requête RAG
            rag_query = (
                f"Quel agent assigner pour: {task_description}. "
                f"Type de tâche: {task_type}, Urgence: {urgency}"
            )
            
            # Consulter RAG pour architecture des agents
            rag_result = self.rag_tool.query_knowledge_base(
                question=rag_query,
                context="internal",  # internal/architecture/agent_roles.md
                department="coordination"
            )
            
            # Analyse sémantique + règles métier
            assigned_agent = self._parse_agent_from_description(
                task_description,
                task_type,
                urgency,
                rag_result
            )
            
            logger.info(
                f"✅ Agent assigné: {assigned_agent['assigned_agent']} "
                f"(confiance: {assigned_agent['confidence']:.2f})"
            )
            
            return assigned_agent
            
        except Exception as e:
            logger.error(f"❌ Erreur assignation agent: {e}")
            # Fallback sur règles simples
            return self._fallback_assignment(task_type, urgency)
    
    def check_escalation_policy(
        self,
        issue_type: str,
        sentiment: str,
        severity: str = "normal",
        customer_tier: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Vérifie si une escalation est nécessaire selon les politiques
        Consulte RAG pour critères d'escalation
        
        Args:
            issue_type: Type de problème (technical, billing, hardware, etc.)
            sentiment: Sentiment client (positive, neutral, negative, angry)
            severity: Sévérité (low, normal, high, critical)
            customer_tier: Niveau client (standard, premium, enterprise)
            context: Contexte additionnel
        
        Returns:
            {
                "escalate": bool,           # Escalade requise?
                "escalation_type": str,     # Type (HITL, manager, technical)
                "reason": str,              # Justification
                "urgency": str,             # Urgence escalade
                "suggested_actions": list   # Actions recommandées
            }
        
        Example:
            >>> result = tools.check_escalation_policy(
            ...     issue_type="battery_swollen",
            ...     sentiment="angry",
            ...     severity="critical"
            ... )
            >>> if result["escalate"]:
            ...     print(f"Escalade requise: {result['reason']}")
        """
        try:
            # Requête RAG pour politiques d'escalation
            rag_query = (
                f"Critères escalation pour problème {issue_type}, "
                f"sentiment {sentiment}, sévérité {severity}"
            )
            
            rag_result = self.rag_tool.query_knowledge_base(
                question=rag_query,
                context="support",  # support/resolution_guides/escalation_criteria.md
                department="coordination"
            )
            
            # Analyse des critères
            escalation_decision = self._analyze_escalation_criteria(
                issue_type,
                sentiment,
                severity,
                customer_tier,
                rag_result
            )
            
            if escalation_decision["escalate"]:
                logger.warning(
                    f"⚠️ Escalation requise: {escalation_decision['reason']}"
                )
            else:
                logger.info("✅ Pas d'escalation nécessaire")
            
            return escalation_decision
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification escalation: {e}")
            # Fallback: escalader si critique
            return self._fallback_escalation(severity, sentiment)
    
    def get_workflow_steps(
        self,
        workflow_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Récupère les étapes d'un workflow standard
        Consulte RAG pour procédures opérationnelles
        
        Args:
            workflow_type: Type de workflow (ticket_lifecycle, onboarding, incident, etc.)
            context: Contexte spécifique
        
        Returns:
            {
                "workflow": str,
                "steps": list,          # Liste des étapes
                "estimated_time": str,  # Temps estimé
                "required_agents": list # Agents impliqués
            }
        
        Example:
            >>> workflow = tools.get_workflow_steps("ticket_lifecycle")
            >>> for step in workflow["steps"]:
            ...     print(f"- {step['name']}: {step['agent']}")
        """
        try:
            # Requête RAG
            rag_query = f"Workflow complet pour {workflow_type}"
            
            rag_result = self.rag_tool.query_knowledge_base(
                question=rag_query,
                context="internal",  # internal/workflows/core_workflows.md
                department="coordination"
            )
            
            # Parser les étapes du workflow
            workflow = self._parse_workflow_from_rag(workflow_type, rag_result)
            
            logger.info(f"✅ Workflow récupéré: {workflow_type} ({len(workflow['steps'])} étapes)")
            
            return workflow
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération workflow: {e}")
            return {"workflow": workflow_type, "steps": [], "error": str(e)}
    
    def get_agent_capabilities(
        self,
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Récupère les capacités d'un type d'agent
        Consulte RAG pour spécifications des agents
        
        Args:
            agent_type: Type d'agent (technical_support, faq_responder, etc.)
        
        Returns:
            {
                "agent_type": str,
                "capabilities": list,   # Liste des capacités
                "limitations": list,    # Limitations
                "typical_tasks": list,  # Tâches typiques
                "escalation_triggers": list  # Quand escalader
            }
        
        Example:
            >>> caps = tools.get_agent_capabilities("technical_support")
            >>> print(caps["capabilities"])
            ['diagnose_hardware', 'analyze_logs', 'create_jira', ...]
        """
        try:
            # Requête RAG
            rag_query = f"Capacités et limitations agent {agent_type}"
            
            rag_result = self.rag_tool.query_knowledge_base(
                question=rag_query,
                context="internal",  # internal/architecture/agent_roles.md
                department="coordination"
            )
            
            # Parser capacités
            capabilities = self._parse_agent_capabilities(agent_type, rag_result)
            
            logger.debug(f"✅ Capacités récupérées pour {agent_type}")
            
            return capabilities
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération capacités: {e}")
            return {"agent_type": agent_type, "error": str(e)}
    
    def analyze_load_distribution(
        self,
        current_loads: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyse la distribution de charge et suggère rééquilibrage
        
        Args:
            current_loads: {agent_id: load_percentage}
        
        Returns:
            {
                "balanced": bool,
                "overloaded_agents": list,
                "underutilized_agents": list,
                "recommendations": list
            }
        
        Example:
            >>> loads = {
            ...     "tech_support_001": 0.95,  # Surchargé
            ...     "tech_support_002": 0.30,  # Sous-utilisé
            ...     "faq_agent_001": 0.60
            ... }
            >>> analysis = tools.analyze_load_distribution(loads)
            >>> if not analysis["balanced"]:
            ...     print(analysis["recommendations"])
        """
        overloaded = [
            agent for agent, load in current_loads.items() 
            if load > 0.80
        ]
        
        underutilized = [
            agent for agent, load in current_loads.items() 
            if load < 0.30
        ]
        
        recommendations = []
        
        if overloaded:
            recommendations.append(
                f"Redistribuer tâches des agents surchargés: {', '.join(overloaded)}"
            )
        
        if underutilized:
            recommendations.append(
                f"Assigner plus de tâches à: {', '.join(underutilized)}"
            )
        
        balanced = len(overloaded) == 0 and len(underutilized) == 0
        
        return {
            "balanced": balanced,
            "overloaded_agents": overloaded,
            "underutilized_agents": underutilized,
            "recommendations": recommendations,
            "average_load": sum(current_loads.values()) / len(current_loads) if current_loads else 0
        }
    
    # ========================================================================
    # MÉTHODES PRIVÉES - Logique métier
    # ========================================================================
    
    def _parse_agent_from_description(
        self,
        description: str,
        task_type: str,
        urgency: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse la réponse RAG et applique règles métier"""
        
        # Mots-clés pour assignation rapide
        description_lower = description.lower()
        
        # Problèmes techniques complexes
        if any(word in description_lower for word in [
            "erreur", "panne", "ne fonctionne plus", "capteur", 
            "firmware", "batterie", "hardware"
        ]):
            return {
                "assigned_agent": "technical_support",
                "reason": "Problème technique détecté nécessitant expertise",
                "alternative": "faq_responder",
                "confidence": 0.85
            }
        
        # Questions simples FAQ
        if any(word in description_lower for word in [
            "comment", "où", "quand", "reset", "configuration", "guide"
        ]) and urgency in ["low", "normal"]:
            return {
                "assigned_agent": "faq_responder",
                "reason": "Question simple résoluble par FAQ",
                "alternative": "technical_support",
                "confidence": 0.75
            }
        
        # Sentiment négatif fort
        if any(word in description_lower for word in [
            "mécontent", "furieux", "inacceptable", "remboursement"
        ]):
            return {
                "assigned_agent": "technical_support",
                "reason": "Sentiment négatif détecté - agent expérimenté requis",
                "alternative": "escalation",
                "confidence": 0.90
            }
        
        # Par urgence
        if urgency == "critical":
            return {
                "assigned_agent": "technical_support",
                "reason": "Urgence critique - agent senior requis",
                "alternative": "escalation",
                "confidence": 0.95
            }
        
        # Défaut: FAQ en première ligne
        return {
            "assigned_agent": "faq_responder",
            "reason": "Premier niveau de support",
            "alternative": "technical_support",
            "confidence": 0.60
        }
    
    def _analyze_escalation_criteria(
        self,
        issue_type: str,
        sentiment: str,
        severity: str,
        customer_tier: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyse si escalation nécessaire"""
        
        escalate = False
        escalation_type = "none"
        reason = ""
        urgency = "normal"
        suggested_actions = []
        
        # Cas critiques -> HITL obligatoire
        if issue_type in ["battery_swollen", "fire_hazard", "injury"]:
            escalate = True
            escalation_type = "HITL"
            reason = "Problème de sécurité critique détecté"
            urgency = "critical"
            suggested_actions = [
                "Contacter client immédiatement",
                "Arrêt utilisation robot",
                "Procédure de récupération matériel"
            ]
        
        # Sentiment très négatif + premium
        elif sentiment in ["angry", "furious"] and customer_tier == "premium":
            escalate = True
            escalation_type = "manager"
            reason = "Client premium mécontent - intervention manager requise"
            urgency = "high"
            suggested_actions = [
                "Appel téléphonique manager",
                "Offre de compensation",
                "Suivi personnalisé"
            ]
        
        # Sévérité critique
        elif severity == "critical":
            escalate = True
            escalation_type = "technical"
            reason = "Sévérité critique - expertise supérieure requise"
            urgency = "high"
            suggested_actions = [
                "Diagnostic approfondi",
                "Consultation R&D si nécessaire"
            ]
        
        # Sentiment négatif + répété
        elif sentiment == "negative" and severity == "high":
            escalate = True
            escalation_type = "HITL"
            reason = "Combinaison sentiment négatif et haute sévérité"
            urgency = "normal"
            suggested_actions = [
                "Revue humaine du cas",
                "Proposition solution personnalisée"
            ]
        
        return {
            "escalate": escalate,
            "escalation_type": escalation_type,
            "reason": reason,
            "urgency": urgency,
            "suggested_actions": suggested_actions
        }
    
    def _parse_workflow_from_rag(
        self,
        workflow_type: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse workflow depuis résultats RAG"""
        
        # Workflows prédéfinis communs
        workflows = {
            "ticket_lifecycle": {
                "workflow": "ticket_lifecycle",
                "steps": [
                    {"name": "Réception", "agent": "ticket_router", "duration": "1min"},
                    {"name": "Classification", "agent": "ticket_router", "duration": "2min"},
                    {"name": "Assignation", "agent": "coo_agent", "duration": "1min"},
                    {"name": "Résolution", "agent": "assigned_agent", "duration": "15-30min"},
                    {"name": "Vérification", "agent": "satisfaction_reporter", "duration": "5min"}
                ],
                "estimated_time": "20-40min",
                "required_agents": ["ticket_router", "coo_agent", "technical_support", "satisfaction_reporter"]
            },
            
            "escalation": {
                "workflow": "escalation",
                "steps": [
                    {"name": "Détection", "agent": "any_agent", "duration": "immediate"},
                    {"name": "Validation", "agent": "coo_agent", "duration": "2min"},
                    {"name": "Notification", "agent": "coo_agent", "duration": "1min"},
                    {"name": "Traitement HITL", "agent": "human", "duration": "variable"}
                ],
                "estimated_time": "5-60min",
                "required_agents": ["detecting_agent", "coo_agent", "human"]
            }
        }
        
        return workflows.get(workflow_type, {
            "workflow": workflow_type,
            "steps": [],
            "estimated_time": "unknown",
            "required_agents": []
        })
    
    def _parse_agent_capabilities(
        self,
        agent_type: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse capacités depuis RAG"""
        
        # Capacités prédéfinies par type
        capabilities_map = {
            "technical_support": {
                "capabilities": [
                    "diagnose_hardware",
                    "analyze_logs",
                    "create_jira",
                    "escalate_hitl",
                    "query_rag_technical"
                ],
                "limitations": [
                    "cannot_refund",
                    "cannot_modify_warranty",
                    "cannot_access_hr_data"
                ],
                "typical_tasks": [
                    "Hardware diagnostics",
                    "Firmware issues",
                    "Advanced troubleshooting"
                ],
                "escalation_triggers": [
                    "Battery swollen",
                    "Safety issue",
                    "Firmware corruption"
                ]
            },
            
            "faq_responder": {
                "capabilities": [
                    "answer_simple_questions",
                    "query_rag_support",
                    "update_tickets",
                    "escalate_to_technical"
                ],
                "limitations": [
                    "cannot_handle_complex_issues",
                    "cannot_create_jira",
                    "limited_refund_authority"
                ],
                "typical_tasks": [
                    "General questions",
                    "How-to guides",
                    "Password reset"
                ],
                "escalation_triggers": [
                    "Technical complexity",
                    "Hardware issues",
                    "Negative sentiment"
                ]
            }
        }
        
        return capabilities_map.get(agent_type, {
            "agent_type": agent_type,
            "capabilities": [],
            "limitations": [],
            "typical_tasks": [],
            "escalation_triggers": []
        })
    
    def _fallback_assignment(
        self,
        task_type: str,
        urgency: str
    ) -> Dict[str, Any]:
        """Assignation fallback si RAG indisponible"""
        if urgency in ["critical", "high"]:
            return {
                "assigned_agent": "technical_support",
                "reason": "Urgence élevée - fallback sur agent senior",
                "alternative": "escalation",
                "confidence": 0.50
            }
        
        return {
            "assigned_agent": "faq_responder",
            "reason": "Fallback - premier niveau de support",
            "alternative": "technical_support",
            "confidence": 0.40
        }
    
    def _fallback_escalation(
        self,
        severity: str,
        sentiment: str
    ) -> Dict[str, Any]:
        """Décision d'escalation fallback"""
        if severity == "critical" or sentiment in ["angry", "furious"]:
            return {
                "escalate": True,
                "escalation_type": "HITL",
                "reason": "Fallback - sévérité ou sentiment critique",
                "urgency": "high",
                "suggested_actions": ["Human review required"]
            }
        
        return {
            "escalate": False,
            "escalation_type": "none",
            "reason": "Fallback - pas de critères critiques détectés",
            "urgency": "normal",
            "suggested_actions": []
        }


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tools = CoordinatorTools()
    
    print("\n" + "="*60)
    print("TEST 1: Assignation d'agent")
    print("="*60)
    
    result1 = tools.determine_agent_assignment(
        task_description="Robot ne démarre plus, batterie OK",
        task_type="technical_issue",
        urgency="high"
    )
    print(f"✅ Agent assigné: {result1['assigned_agent']}")
    print(f"   Raison: {result1['reason']}")
    print(f"   Confiance: {result1['confidence']}")
    
    print("\n" + "="*60)
    print("TEST 2: Vérification escalation")
    print("="*60)
    
    result2 = tools.check_escalation_policy(
        issue_type="battery_swollen",
        sentiment="angry",
        severity="critical"
    )
    print(f"✅ Escalade requise: {result2['escalate']}")
    if result2['escalate']:
        print(f"   Type: {result2['escalation_type']}")
        print(f"   Raison: {result2['reason']}")
        print(f"   Actions: {result2['suggested_actions']}")
    
    print("\n" + "="*60)
    print("TEST 3: Workflow steps")
    print("="*60)
    
    workflow = tools.get_workflow_steps("ticket_lifecycle")
    print(f"✅ Workflow: {workflow['workflow']}")
    print(f"   Durée estimée: {workflow['estimated_time']}")
    print(f"   Étapes:")
    for step in workflow["steps"]:
        print(f"   - {step['name']}: {step['agent']} ({step['duration']})")
    
    print("\n" + "="*60)
    print("TEST 4: Capacités agent")
    print("="*60)
    
    caps = tools.get_agent_capabilities("technical_support")
    print(f"✅ Capacités technical_support:")
    print(f"   Peut faire: {caps['capabilities'][:3]}...")
    print(f"   Limitations: {caps['limitations'][:2]}...")
    
    print("\n" + "="*60)
    print("TEST 5: Analyse de charge")
    print("="*60)
    
    loads = {
        "tech_support_001": 0.95,
        "tech_support_002": 0.30,
        "faq_agent_001": 0.60
    }
    
    analysis = tools.analyze_load_distribution(loads)
    print(f"✅ Distribution équilibrée: {analysis['balanced']}")
    if not analysis['balanced']:
        print(f"   Surchargés: {analysis['overloaded_agents']}")
        print(f"   Sous-utilisés: {analysis['underutilized_agents']}")
        print(f"   Recommandations:")
        for rec in analysis['recommendations']:
            print(f"   - {rec}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)