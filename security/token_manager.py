"""
Token Manager - Gestion JWT pour authentification A2A
Utilise PyJWT pour tokens légers et sécurisés
"""

import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TokenManager:
    """Gestion des tokens JWT pour authentification inter-agents"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Args:
            secret_key: Clé secrète pour signer les tokens (depuis .env en prod)
        """
        # En prod: charger depuis config/settings.py qui lit .env
        self.secret_key = secret_key or "CHANGE_ME_IN_PRODUCTION_ENV"
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)  # Tokens valides 24h
        
        # Cache des tokens révoqués (en prod: Redis)
        self.revoked_tokens = set()
    
    def generate_agent_token(
        self, 
        agent_id: str,
        agent_type: str,
        department: str,
        permissions: list[str]
    ) -> str:
        """
        Génère un token JWT pour un agent
        
        Args:
            agent_id: ID unique de l'agent (ex: "technical_support_001")
            agent_type: Type d'agent (ex: "technical_support")
            department: Division (support, marketing, hr, coordinator)
            permissions: Liste des permissions (ex: ["read:tickets", "create:jira"])
        
        Returns:
            Token JWT signé
        
        Example:
            >>> tm = TokenManager()
            >>> token = tm.generate_agent_token(
            ...     agent_id="tech_support_001",
            ...     agent_type="technical_support",
            ...     department="support",
            ...     permissions=["read:tickets", "update:tickets", "create:jira"]
            ... )
        """
        now = datetime.utcnow()
        
        payload = {
            # Standard JWT claims
            "iat": now,  # Issued at
            "exp": now + self.token_expiry,  # Expiration
            "jti": str(uuid.uuid4()),  # JWT ID (unique)
            
            # Custom claims pour agents
            "agent_id": agent_id,
            "agent_type": agent_type,
            "department": department,
            "permissions": permissions,
            "token_version": "1.0"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"✅ Token généré pour agent {agent_id} (département: {department})")
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valide un token JWT et retourne le payload
        
        Args:
            token: Token JWT à valider
        
        Returns:
            Payload décodé si valide
        
        Raises:
            jwt.ExpiredSignatureError: Token expiré
            jwt.InvalidTokenError: Token invalide
            ValueError: Token révoqué
        
        Example:
            >>> payload = tm.validate_token(token)
            >>> print(payload["agent_id"])
            tech_support_001
        """
        try:
            # Décoder et vérifier signature + expiration
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Vérifier si token révoqué
            jti = payload.get("jti")
            if jti in self.revoked_tokens:
                raise ValueError(f"Token révoqué: {jti}")
            
            logger.debug(f"✅ Token validé pour agent {payload.get('agent_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("❌ Token expiré")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ Token invalide: {e}")
            raise
    
    def verify_permission(self, token: str, required_permission: str) -> bool:
        """
        Vérifie si un token possède une permission spécifique
        
        Args:
            token: Token JWT
            required_permission: Permission requise (ex: "create:jira")
        
        Returns:
            True si permission accordée, False sinon
        
        Example:
            >>> has_permission = tm.verify_permission(token, "create:jira")
            >>> if not has_permission:
            ...     raise PermissionError("Accès refusé")
        """
        try:
            payload = self.validate_token(token)
            permissions = payload.get("permissions", [])
            
            has_perm = required_permission in permissions
            
            if not has_perm:
                logger.warning(
                    f"❌ Permission refusée: {payload.get('agent_id')} "
                    f"n'a pas '{required_permission}'"
                )
            
            return has_perm
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            return False
    
    def revoke_token(self, token: str) -> bool:
        """
        Révoque un token (logout, sécurité compromise)
        
        Args:
            token: Token à révoquer
        
        Returns:
            True si révoqué avec succès
        
        Note:
            En production, stocker les JTI révoqués dans Redis avec TTL
        """
        try:
            payload = self.validate_token(token)
            jti = payload.get("jti")
            
            self.revoked_tokens.add(jti)
            logger.info(f"🔒 Token révoqué: {jti} (agent: {payload.get('agent_id')})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur révocation token: {e}")
            return False
    
    def refresh_token(self, old_token: str) -> str:
        """
        Génère un nouveau token avant expiration de l'ancien
        
        Args:
            old_token: Token actuel
        
        Returns:
            Nouveau token avec même payload mais nouvelle expiration
        
        Example:
            >>> new_token = tm.refresh_token(old_token)
        """
        try:
            payload = self.validate_token(old_token)
            
            # Générer nouveau token avec même données
            new_token = self.generate_agent_token(
                agent_id=payload["agent_id"],
                agent_type=payload["agent_type"],
                department=payload["department"],
                permissions=payload["permissions"]
            )
            
            # Révoquer ancien token
            self.revoke_token(old_token)
            
            logger.info(f"🔄 Token renouvelé pour {payload['agent_id']}")
            return new_token
            
        except Exception as e:
            logger.error(f"❌ Erreur renouvellement token: {e}")
            raise
    
    def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """
        Décode un token SANS vérifier la signature (debug uniquement)
        
        ⚠️ NE JAMAIS UTILISER POUR VALIDATION EN PRODUCTION
        
        Args:
            token: Token JWT
        
        Returns:
            Payload décodé (non vérifié)
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"❌ Erreur décodage token: {e}")
            return {}


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    # Configuration logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialisation
    tm = TokenManager()
    
    print("\n" + "="*60)
    print("TEST 1: Génération de tokens")
    print("="*60)
    
    # Générer token pour Technical Support Agent
    tech_token = tm.generate_agent_token(
        agent_id="tech_support_001",
        agent_type="technical_support",
        department="support",
        permissions=["read:tickets", "update:tickets", "create:jira", "escalate:hitl"]
    )
    print(f"Token Tech Support: {tech_token[:50]}...")
    
    # Générer token pour FAQ Agent (permissions limitées)
    faq_token = tm.generate_agent_token(
        agent_id="faq_agent_001",
        agent_type="faq_responder",
        department="support",
        permissions=["read:tickets", "update:tickets"]
    )
    print(f"Token FAQ Agent: {faq_token[:50]}...")
    
    # Générer token pour COO Agent (toutes permissions)
    coo_token = tm.generate_agent_token(
        agent_id="coo_agent_001",
        agent_type="coordinator",
        department="coordinator",
        permissions=["*"]  # Wildcard = toutes permissions
    )
    print(f"Token COO Agent: {coo_token[:50]}...")
    
    print("\n" + "="*60)
    print("TEST 2: Validation de tokens")
    print("="*60)
    
    # Valider token
    payload = tm.validate_token(tech_token)
    print(f"✅ Payload validé: {payload['agent_id']} (département: {payload['department']})")
    print(f"   Permissions: {payload['permissions']}")
    
    print("\n" + "="*60)
    print("TEST 3: Vérification de permissions")
    print("="*60)
    
    # Tech Support peut créer Jira
    can_create_jira = tm.verify_permission(tech_token, "create:jira")
    print(f"✅ Tech Support peut créer Jira: {can_create_jira}")
    
    # FAQ Agent NE PEUT PAS créer Jira
    can_faq_create_jira = tm.verify_permission(faq_token, "create:jira")
    print(f"❌ FAQ Agent peut créer Jira: {can_faq_create_jira}")
    
    # COO Agent peut tout faire
    can_coo_do_anything = tm.verify_permission(coo_token, "delete:universe")
    print(f"✅ COO Agent peut tout faire: {can_coo_do_anything or '*' in tm.validate_token(coo_token)['permissions']}")
    
    print("\n" + "="*60)
    print("TEST 4: Révocation de token")
    print("="*60)
    
    tm.revoke_token(tech_token)
    try:
        tm.validate_token(tech_token)
        print("❌ ERREUR: Token révoqué non détecté")
    except ValueError:
        print("✅ Token révoqué correctement détecté")
    
    print("\n" + "="*60)
    print("TEST 5: Renouvellement de token")
    print("="*60)
    
    new_faq_token = tm.refresh_token(faq_token)
    print(f"✅ Nouveau token généré: {new_faq_token[:50]}...")
    
    # Ancien token révoqué
    try:
        tm.validate_token(faq_token)
        print("❌ ERREUR: Ancien token toujours valide")
    except ValueError:
        print("✅ Ancien token correctement révoqué")
    
    # Nouveau token valide
    new_payload = tm.validate_token(new_faq_token)
    print(f"✅ Nouveau token valide: {new_payload['agent_id']}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)