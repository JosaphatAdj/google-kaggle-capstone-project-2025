# 🎯 COO Agent - Chief Operating Officer Agent

## Vue d'ensemble

Le **COO Agent** est l'orchestrateur principal du système multi-agents RoboNest. Il coordonne toutes les divisions (Support, Marketing, RH) et garantit une opération fluide, sécurisée et efficace du département automatisé.

## 🎭 Rôles et Responsabilités

### 1. **Délégation Intelligente de Tâches**
- Analyse les tâches entrantes
- Consulte RoboBrain (RAG) pour décisions éclairées
- Assigne au meilleur agent disponible
- Équilibre la charge de travail

### 2. **Supervision des Performances**
- Monitore l'état de tous les agents
- Collecte métriques en temps réel
- Détecte agents surchargés/sous-utilisés
- Propose rééquilibrage

### 3. **Gestion des Escalations**
- Valide critères d'escalation via RAG
- Détermine type d'escalation (HITL, technique, manager)
- Notifie parties appropriées
- Trace toutes les escalations

### 4. **Coordination Inter-Divisions**
- Facilite communication A2A
- Route messages entre divisions
- Garantit cohérence des workflows

### 5. **Rapports Opérationnels**
- Génère rapports de performance
- Analyse tendances
- Recommandations d'amélioration

## 🏗️ Architecture

```
COOAgent
├── Security Layer (JWT + Audit)
├── Communication Layer (Message Bus)
├── Intelligence Layer (RAG Tools)
└── Orchestration Logic
    ├── Task Delegation
    ├── Escalation Handling
    ├── Performance Monitoring
    └── Reporting
```

## 🔐 Sécurité

### Authentification
- Token JWT avec permissions wildcard `["*"]`
- Enregistré comme agent de type `coordinator`
- Audit complet de toutes les actions

### Permissions
Le COO Agent peut :
- ✅ Déléguer à tous les agents
- ✅ Accéder à tous les contextes RAG
- ✅ Gérer toutes les escalations
- ✅ Consulter tous les statuts agents
- ✅ Générer tous les rapports

## 📡 Communication A2A

### Topics Écoutés
- `task.new` - Nouvelles tâches à déléguer
- `task.completed` - Tâches terminées
- `task.failed` - Tâches échouées
- `escalation.request` - Demandes d'escalation
- `agent.status` - Mises à jour statut agents
- `system.alert` - Alertes système

### Topics Publiés
- `task.assigned.*` - Tâches déléguées
- `agent.heartbeat` - Heartbeat périodique
- `escalation.approved` - Escalations approuvées
- `escalation.rejected` - Escalations rejetées

## 🧠 Intégration RAG

Le COO Agent consulte RoboBrain pour :

### 1. **Assignation d'Agents**
```python
# Consulte: internal/architecture/agent_roles.md
assignment = coordinator_tools.determine_agent_assignment(
    task_description="Robot ne démarre plus",
    task_type="technical_issue",
    urgency="high"
)
# → Retourne: technical_support (confiance: 0.85)
```

### 2. **Validation Escalations**
```python
# Consulte: support/resolution_guides/escalation_criteria.md
escalation = coordinator_tools.check_escalation_policy(
    issue_type="battery_swollen",
    sentiment="angry",
    severity="critical"
)
# → Retourne: escalate=True, type=HITL, urgency=critical
```

### 3. **Workflows Opérationnels**
```python
# Consulte: internal/workflows/core_workflows.md
workflow = coordinator_tools.get_workflow_steps("ticket_lifecycle")
# → Retourne: 5 étapes avec agents et durées
```

## 🚀 Utilisation

### Démarrage Basique

```python
from agents.coordinator.coo_agent import COOAgent
from security import AuthManager, AuditLog
from communication.message_bus import MessageBus

# Setup infrastructure
auth = AuthManager()
audit = AuditLog()
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
```

### Envoi de Tâche

```python
from communication.message_bus import Message

task = Message(
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

await bus.publish(task, sender_token)
```

### Rapport de Performance

```python
report = coo.get_performance_report()

print(f"Tâches déléguées: {report['metrics']['tasks_delegated']}")
print(f"Tâches complétées: {report['metrics']['tasks_completed']}")
print(f"Escalations: {report['metrics']['escalations_handled']}")
```

## 📊 Métriques Trackées

```python
performance_metrics = {
    "tasks_delegated": 0,        # Total tâches assignées
    "tasks_completed": 0,        # Total tâches terminées
    "tasks_failed": 0,           # Total tâches échouées
    "escalations_handled": 0,    # Total escalations traitées
    "average_completion_time": 0.0  # Temps moyen (minutes)
}
```

## 🎬 Démonstration

Lancer la démo complète :

```bash
python scripts/start_coo_demo.py
```

La démo exécute 4 scénarios :
1. **Tâche Simple** - Question FAQ
2. **Problème Technique** - Diagnostic complexe
3. **Escalation Critique** - Batterie gonflée (HITL)
4. **Équilibrage de Charge** - Multiples tâches simultanées

## 🧪 Tests

### Tests Unitaires
```bash
pytest tests/unit/test_agents/test_coo_agent.py
```

### Tests d'Intégration
```bash
pytest tests/integration/test_coo_integration.py
```

## 📝 Logs & Audit

Tous les événements sont tracés :

```python
# Logs applicatifs
logs/agents/coo_agent_001.log

# Audit trail complet
logs/audit/audit_YYYY-MM-DD.jsonl
```

Format audit log :
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "action_type": "task_delegated",
  "agent_id": "coo_agent_001",
  "details": {
    "task_id": "TASK-001",
    "assigned_to": "tech_support_001",
    "reason": "Problème technique complexe"
  },
  "severity": "info"
}
```

## 🔄 Workflows Typiques

### 1. Workflow Ticket Support

```
Ticket Entrant
    ↓
COO Agent reçoit (task.new)
    ↓
Consulte RAG → Détermine agent
    ↓
Vérifie escalation nécessaire?
    ↓ Non
Délègue à agent approprié
    ↓
Agent traite et répond
    ↓
COO reçoit (task.completed)
    ↓
Met à jour métriques
```

### 2. Workflow Escalation

```
Agent détecte problème critique
    ↓
Envoie escalation.request
    ↓
COO reçoit et valide via RAG
    ↓
Détermine type escalation
    ↓
Si HITL → Notifie humain
Si technique → Réassigne agent senior
```

## 🛠️ Configuration

### Variables d'Environnement
```bash
# .env
COO_AGENT_ID=coo_agent_001
COO_HEARTBEAT_INTERVAL=60  # secondes
COO_MAX_RETRIES=2
COO_TASK_TIMEOUT=300  # secondes
```

### Configuration YAML
```yaml
# config/agents_config.yaml
coordinator:
  coo_agent:
    agent_type: coordinator
    department: coordinator
    permissions: ["*"]
    monitoring:
      heartbeat_interval: 60
      metrics_collection: true
    delegation:
      load_threshold: 0.80
      retry_attempts: 2
```

## 🚨 Gestion des Erreurs

### Tâche Échouée
- Retry automatique (max 2 fois)
- Après 2 échecs → Escalade vers manager
- Audit complet de l'échec

### Agent Indisponible
- Mise en queue de la tâche
- Tentative de réassignation toutes les 30s
- Alerte si queue > 10 tâches

### Escalation Critique
- Notification immédiate (email/SMS)
- Log CRITICAL dans audit
- Blocage tâche jusqu'à résolution humaine

## 📈 Optimisations Futures

- [ ] Cache RAG intelligent
- [ ] Prédiction de charge
- [ ] ML pour assignation optimale
- [ ] Dashboard temps réel
- [ ] Intégration alerting (PagerDuty, Slack)

## 🤝 Contribution

Pour ajouter un nouveau type de tâche :

1. Mettre à jour `coordinator_tools.py`
2. Ajouter mappings dans `_parse_agent_from_description()`
3. Documenter dans RAG (`agent_roles.md`)
4. Ajouter tests d'intégration

## 📚 Références

- [Architecture Multi-Agents](../../docs/architecture.md)
- [Protocoles A2A](../../communication/protocols.py)
- [Coordinator Tools](../../tools/coordinator/coordinator_tools.py)
- [Base RAG](../../rag/rag_engine.py)