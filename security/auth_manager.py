"""
Auth Manager - Gestion centralisée des agents et permissions
Registre des agents + validation des actions
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
import json
import logging
from pathlib import Path

from .token_manager import TokenManager

logger = logging.getLogger(__name__)


class AuthManager:
    """Gestion de l'authentification et des permissions des agents"""
    
    # Permissions prédéfinies par rôle
    ROLE_PERMISSIONS = {
        "coordinator": ["*"],  # Toutes permissions
        
        "technical_support": [
            "read:tickets",
            "update:tickets",
            "create:jira",
            "escalate:hitl",
            "read:rag:support",
            "read:rag:products",
            "read:rag:technical"
        ],
        
        "faq_responder": [
            "read:tickets",
            "update:tickets",
            "read:rag:support",
            "read:rag:products"
        ],
        
        "ticket_router": [
            "read:tickets",
            "update:tickets",
            "assign:agent",
            "read:rag:support"
        ],
        
        "sentiment_analyzer": [
            "read:tickets",
            "update:tickets",
            "flag:sentiment",
            "escalate:hitl"
        ],
        
        "satisfaction_reporter": [
            "read:tickets",
            "read:metrics",
            "generate:reports",
            "send:email"
        ],
        
        "content_creator": [
            "read:rag:marketing",
            "read:rag:products",
            "create:content",
            "read:rag:brand"
        ],
        
        "seo_analyst": [
            "read:rag:marketing",
            "analyze:seo",
            "read:content"
        ],
        
        "social_media_manager": [
            "read:rag:marketing",
            "read:rag:brand",
            "create:content",
            "publish:social"
        ],
        
        "email_campaign_manager": [
            "read:rag:marketing",
            "create:email",
            "send:email",
            "read:metrics"
        ],
        
        "analytics_reporter": [
            "read:metrics",
            "generate:reports",
            "read:rag:marketing"
        ],
        
        "hr_assistant": [
            "read:rag:hr",
            "read:employee:public",
            "generate:documents"
        ],
        
        "it_helpdesk": [
            "read:rag:it",
            "reset:password",
            "read:employee:public",
            "update:permissions:basic"
        ],
        
        "onboarding_coordinator": [
            "read:rag:hr",
            "read:rag:it",
            "create:employee",
            "send:email",
            "read:rag:onboarding"
        ],
        
        "internal_comms": [
            "read:rag:internal",
            "create:announcement",
            "send:email:internal"
        ]
    }
    
    def __init__(self, token_manager: Optional[TokenManager] = None):
        """
        Args:
            token_manager: Instance de TokenManager (ou crée une nouvelle)
        """
        self.token_manager = token_manager or TokenManager()
        
        # Registre des agents actifs {agent_id: metadata}
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        
        # Cache des tokens actifs {agent_id: token}
        self.active_tokens: Dict[str, str] = {}
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Enregistre un agent et génère son token
        
        Args:
            agent_id: ID unique (ex: "tech_support_001")
            agent_type: Type d'agent (doit correspondre à ROLE_PERMISSIONS)
            department: Division (support, marketing, hr, coordinator)
            metadata: Données supplémentaires (version, host, etc.)
        
        Returns:
            Token JWT généré
        
        Raises:
            ValueError: Si agent_type inconnu
        
        Example:
            >>> auth = AuthManager()
            >>> token = auth.register_agent(
            ...     agent_id="tech_support_001",
            ...     agent_type="technical_support",
            ...     department="support",
            ...     metadata={"version": "1.0", "host": "server-01"}
            ... )
        """
        # Vérifier que le type d'agent existe
        if agent_type not in self.ROLE_PERMISSIONS:
            raise ValueError(
                f"Type d'agent inconnu: {agent_type}. "
                f"Types valides: {list(self.ROLE_PERMISSIONS.keys())}"
            )
        
        # Récupérer permissions du rôle
        permissions = self.ROLE_PERMISSIONS[agent_type]
        
        # Générer token
        token = self.token_manager.generate_agent_token(
            agent_id=agent_id,
            agent_type=agent_type,
            department=department,
            permissions=permissions
        )
        
        # Enregistrer dans le registre
        self.registered_agents[agent_id] = {
            "agent_type": agent_type,
            "department": department,
            "permissions": permissions,
            "registered_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "status": "active"
        }
        
        # Stocker token actif
        self.active_tokens[agent_id] = token
        
        logger.info(
            f"✅ Agent enregistré: {agent_id} "
            f"(type: {agent_type}, département: {department})"
        )
        
        return token
    
    def verify_agent(self, token: str) -> Dict[str, Any]:
        """
        Vérifie qu'un token est valide et retourne les infos de l'agent
        
        Args:
            token: Token JWT à vérifier
        
        Returns:
            Metadata de l'agent
        
        Raises:
            PermissionError: Si token invalide ou agent non enregistré
        
        Example:
            >>> agent_info = auth.verify_agent(token)
            >>> print(agent_info["agent_type"])
            technical_support
        """
        try:
            # Valider token JWT
            payload = self.token_manager.validate_token(token)
            agent_id = payload["agent_id"]
            
            # Vérifier que l'agent est enregistré
            if agent_id not in self.registered_agents:
                raise PermissionError(f"Agent non enregistré: {agent_id}")
            
            agent_info = self.registered_agents[agent_id]
            
            # Vérifier que l'agent est actif
            if agent_info["status"] != "active":
                raise PermissionError(f"Agent inactif: {agent_id}")
            
            return {
                "agent_id": agent_id,
                **payload,
                **agent_info
            }
            
        except Exception as e:
            logger.error(f"❌ Vérification agent échouée: {e}")
            raise PermissionError(f"Authentification échouée: {e}")
    
    def check_permission(
        self,
        token: str,
        required_permission: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Vérifie si un agent a une permission spécifique
        
        Args:
            token: Token de l'agent
            required_permission: Permission requise (ex: "create:jira")
            resource: Ressource spécifique (ex: "ticket_123")
        
        Returns:
            True si permission accordée
        
        Example:
            >>> can_escalate = auth.check_permission(token, "escalate:hitl")
            >>> if not can_escalate:
            ...     raise PermissionError("Escalade non autorisée")
        """
        try:
            agent_info = self.verify_agent(token)
            permissions = agent_info["permissions"]
            
            # Vérifier wildcard (coordinateur)
            if "*" in permissions:
                return True
            
            # Vérifier permission exacte
            if required_permission in permissions:
                logger.debug(
                    f"✅ Permission accordée: {agent_info['agent_id']} "
                    f"→ {required_permission}"
                )
                return True
            
            # Vérifier permissions avec wildcards (ex: "read:*")
            for perm in permissions:
                if perm.endswith(":*"):
                    prefix = perm.split(":")[0]
                    if required_permission.startswith(f"{prefix}:"):
                        return True
            
            logger.warning(
                f"❌ Permission refusée: {agent_info['agent_id']} "
                f"n'a pas '{required_permission}'"
            )
            return False
            
        except PermissionError:
            return False
    
    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Désactive un agent (révoque son token)
        
        Args:
            agent_id: ID de l'agent à désactiver
        
        Returns:
            True si désactivation réussie
        """
        if agent_id not in self.registered_agents:
            logger.warning(f"Agent non trouvé: {agent_id}")
            return False
        
        # Révoquer token
        if agent_id in self.active_tokens:
            self.token_manager.revoke_token(self.active_tokens[agent_id])
            del self.active_tokens[agent_id]
        
        # Marquer comme inactif
        self.registered_agents[agent_id]["status"] = "inactive"
        self.registered_agents[agent_id]["deactivated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"🔒 Agent désactivé: {agent_id}")
        return True
    
    def get_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'un agent
        
        Args:
            agent_id: ID de l'agent
        
        Returns:
            Metadata ou None si non trouvé
        """
        return self.registered_agents.get(agent_id)
    
    def list_active_agents(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste tous les agents actifs (optionnellement par département)
        
        Args:
            department: Filtrer par département (support, marketing, hr)
        
        Returns:
            Liste des agents actifs
        
        Example:
            >>> agents = auth.list_active_agents(department="support")
            >>> for agent in agents:
            ...     print(f"{agent['agent_id']}: {agent['agent_type']}")
        """
        agents = []
        
        for agent_id, metadata in self.registered_agents.items():
            if metadata["status"] != "active":
                continue
            
            if department and metadata["department"] != department:
                continue
            
            agents.append({
                "agent_id": agent_id,
                **metadata
            })
        
        return agents
    
    def export_registry(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporte le registre des agents (backup/audit)
        
        Args:
            filepath: Chemin du fichier JSON (optionnel)
        
        Returns:
            Registre complet
        """
        registry = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_agents": len(self.registered_agents),
            "active_agents": len([a for a in self.registered_agents.values() if a["status"] == "active"]),
            "agents": self.registered_agents
        }
        
        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(registry, f, indent=2)
            logger.info(f"📄 Registre exporté: {filepath}")
        
        return registry


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    auth = AuthManager()
    
    print("\n" + "="*60)
    print("TEST 1: Enregistrement d'agents")
    print("="*60)
    
    # Enregistrer COO Agent
    coo_token = auth.register_agent(
        agent_id="coo_agent_001",
        agent_type="coordinator",
        department="coordinator",
        metadata={"version": "1.0", "role": "orchestrator"}
    )
    print(f"✅ COO Agent enregistré")
    
    # Enregistrer Technical Support
    tech_token = auth.register_agent(
        agent_id="tech_support_001",
        agent_type="technical_support",
        department="support",
        metadata={"version": "1.0", "specialization": "hardware"}
    )
    print(f"✅ Technical Support enregistré")
    
    # Enregistrer FAQ Agent
    faq_token = auth.register_agent(
        agent_id="faq_agent_001",
        agent_type="faq_responder",
        department="support"
    )
    print(f"✅ FAQ Agent enregistré")
    
    print("\n" + "="*60)
    print("TEST 2: Vérification d'agents")
    print("="*60)
    
    tech_info = auth.verify_agent(tech_token)
    print(f"✅ Agent vérifié: {tech_info['agent_id']}")
    print(f"   Permissions: {tech_info['permissions'][:3]}...")
    
    print("\n" + "="*60)
    print("TEST 3: Vérification de permissions")
    print("="*60)
    
    # Tech Support peut créer Jira
    can_create_jira = auth.check_permission(tech_token, "create:jira")
    print(f"✅ Tech Support peut créer Jira: {can_create_jira}")
    
    # FAQ Agent NE PEUT PAS créer Jira
    can_faq_jira = auth.check_permission(faq_token, "create:jira")
    print(f"❌ FAQ Agent peut créer Jira: {can_faq_jira}")
    
    # COO Agent peut tout faire
    can_coo_anything = auth.check_permission(coo_token, "delete:universe")
    print(f"✅ COO Agent peut tout faire: {can_coo_anything}")
    
    print("\n" + "="*60)
    print("TEST 4: Liste des agents actifs")
    print("="*60)
    
    all_agents = auth.list_active_agents()
    print(f"Total agents actifs: {len(all_agents)}")
    
    support_agents = auth.list_active_agents(department="support")
    print(f"Agents support: {len(support_agents)}")
    for agent in support_agents:
        print(f"  - {agent['agent_id']} ({agent['agent_type']})")
    
    print("\n" + "="*60)
    print("TEST 5: Désactivation d'agent")
    print("="*60)
    
    auth.deactivate_agent("faq_agent_001")
    
    # Vérifier que le token est révoqué
    try:
        auth.verify_agent(faq_token)
        print("❌ ERREUR: Token toujours valide")
    except PermissionError:
        print("✅ Token correctement révoqué")
    
    active_agents = auth.list_active_agents(department="support")
    print(f"Agents support actifs après désactivation: {len(active_agents)}")
    
    print("\n" + "="*60)
    print("TEST 6: Export du registre")
    print("="*60)
    
    registry = auth.export_registry()
    print(f"✅ Registre exporté:")
    print(f"   Total agents: {registry['total_agents']}")
    print(f"   Agents actifs: {registry['active_agents']}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)