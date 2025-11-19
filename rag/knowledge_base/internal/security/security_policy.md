# Politique de Sécurité Entreprise

## Principes de Base (Security by Design)
- **Confidentialité** : Données accessibles selon rôle uniquement
- **Intégrité** : Données non modifiables sans autorisation
- **Disponibilité** : Services sécurisés mais accessibles
- **Auditabilité** : Toutes actions sensibles tracées
- **Séparation des rôles** : Permissions granulaires

## Authentification des Agents
**Identité numérique complète :**
- Certificat interne RoboNest
- Clé privée stockée dans coffre sécurisé
- Token rotatif (rotation 24h)
- Permissions associées au rôle

**Empreinte d'agent (agent fingerprint) :**
- Nom de l'agent
- Version du modèle
- Horodatage
- ID conversationnel

## Classification des Données
**Niveau 1 — Public interne** : Procédures simples, guides travail
**Niveau 2 — Confidentiel interne** : Workflows, tickets, documents non publics  
**Niveau 3 — Sensible** : RH, IT, architecture technique
**Niveau 4 — Critique** : Accès admin, firmware, certificats