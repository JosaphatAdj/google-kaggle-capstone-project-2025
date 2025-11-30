# Agents Documentation

Documentation des agents du système RoboNest.

## Table des Matières

- [Architecture Générale](#architecture-générale)
- [Agent Alert Receiver](#agent-alert-receiver)
- [Agent COO (Orchestrateur)](#agent-coo-orchestrateur)
- [Agent Technical Support](#agent-technical-support)
- [Message Bus](#message-bus)
- [Diagrammes](#diagrammes)

---

## Architecture Générale

Le système RoboNest utilise une architecture distribuée basée sur Message Bus avec un point d'entrée unique.

### Point d'Entrée: `agents/main.py`

**Responsabilités:**
- Créer UNE instance de Message Bus partagée
- Initialiser tous les agents avec cette instance
- Exposer Alert Receiver en A2A (port 8000)
- Lancer le serveur A2A

**Agents créés:**
1. Alert Receiver (A2A + Message Bus)
2. COO Agent (Orchestrateur)
3. Technical Support Agent (Résolveur)

---

## Agent Alert Receiver

**Fichier:** `agents/alert_receiver/alert_receiver_a2a.py`

### Rôle
- Interface A2A avec robots externes
- Analyse et classification des alertes
- Routing vers système interne via Message Bus

### Caractéristiques
- **Type:** LlmAgent (Gemini 2.0 Flash Lite)
- **Exposition:** A2A Server (port 8000)
- **Communication:** A2A (externe) + Message Bus (interne)

### Workflow
1. Reçoit alerte robot via A2A
2. Utilise `query_error_code()` pour consulter RAG
3. Utilise `classify_error()` pour déterminer urgence
4. Publie sur Message Bus: `topic="task.new"`
5. Attend solution du COO via `topic="solution.for_robot"`
6. Retourne solution au robot via A2A

### Tools Disponibles
- `query_error_code(error_code)` - Consulte base de connaissances
- `classify_error(error_code, description)` - Détermine urgence
- `process_robot_alert(...)` - Publie sur Message Bus
- `get_pending_solution(robot_id)` - Récupère solution pour robot

### Topics Message Bus

**Subscribes:**
- `solution.for_robot` - Reçoit solutions du COO

**Publishes:**
- `task.new` - Envoie nouvelles tâches au COO

---

## Agent COO (Orchestrateur)

**Fichier:** `agents/coordinator/coo_agent.py`

### Rôle
- Orchestration et routing intelligent
- Délégation de tâches aux agents spécialisés
- Supervision et métriques

### Caractéristiques
- **Type:** BaseAgent
- **Outils:** CoordinatorTools (RAG-powered)
- **Communication:** Message Bus uniquement

### Workflow
1. Reçoit `task.new` du Message Bus
2. Utilise `determine_agent_assignment()` pour routing
   - `task_type="robot_alert"` → `"technical_support"`
3. Publie `task.assigned.technical_support`
4. Reçoit `task.completed` de Technical Support
5. Si `task_type="robot_alert"`:
   - Forward solution via `solution.for_robot`

### CoordinatorTools

**Méthodes principales:**
```python
determine_agent_assignment(
    task_description: str,
    task_type: str,
    urgency: str
) -> Dict[str, Any]
```

**Routing Rules:**
- `task_type="robot_alert"` → **technical_support** (prioritaire)
- Urgence "critical" → **technical_support**
- Mots-clés techniques → **technical_support**
- Questions simples → **faq_responder**

### Topics Message Bus

**Subscribes:**
- `task.new` - Nouvelles tâches
- `task.completed` - Tâches terminées

**Publishes:**
- `task.assigned.*` - Délégations
- `solution.for_robot` - Forward solutions à Alert Receiver

---

## Agent Technical Support

**Fichier:** `agents/support/technical_support_agent.py`

### Rôle
- Résolution de problèmes techniques robots
- Consultation RAG pour solutions
- Gestion HITL (escalations)
- Création tickets Jira et notifications Gmail

### Caractéristiques
- **Type:** BaseAgent
- **Spécialisation:** Support technique robots
- **Communication:** Message Bus uniquement

### Workflow
1. Reçoit `task.assigned.technical_support`
2. Exécute `process_task()`:
   - Analyse error_code et contexte
   - Détermine actions depuis RAG ou heuristiques
   - Crée ticket Jira pour tracking
   - Si `requires_hitl=true`: envoie email Gmail
3. Retourne solution JSON:
```json
{
  "actions": ["clean_wheels", "recalibrate_motors"],
  "error_code": "E01",
  "ticket_id": "ROB-123",
  "requires_hitl": false,
  "is_temporary_solution": false
}
```
4. Publie `task.completed`

### Tools Disponibles
- RAG Tool - Consultation knowledge base
- `create_jira_ticket()` - Création tickets
- `update_jira_ticket()` - Mise à jour tickets
- `send_escalation_email()` - Notifications HITL

### Règles de Résolution

**Erreurs critiques (HITL automatique):**
- E07: Battery Critical/Swollen
- E08: Firmware Corruption
- E09: Safety Sensor Failure

**Résolution automatique:**
- E01: Wheels Blocked → `["clean_wheels", "recalibrate_motors"]`
- E02: Navigation Error → `["reset_navigation", "reboot_sensors"]`
- E03: Charging Issue → `["charge_battery", "return_to_dock"]`
- E04: Software Error → `["restart_service", "reboot"]`
- E05: Performance Degraded → `["clear_cache", "optimize_memory"]`
- E06: Communication Lost → `["reconnect_wifi", "reset_network"]`

### Topics Message Bus

**Subscribes:**
- `task.assigned.technical_support` - Tâches assignées

**Publishes:**
- `task.completed` - Solutions

---

## Message Bus

**Fichier:** `communication/message_bus.py`

### Caractéristiques
- **Instance:** UNIQUE, créée dans `agents/main.py`
- **Partagée:** Tous les agents utilisent la même instance
- **Pattern:** Pub/Sub asynchrone

### Topics Utilisés

| Topic | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `task.new` | Alert Receiver | COO Agent | Task data |
| `task.assigned.technical_support` | COO Agent | Technical Support | Assignment |
| `task.completed` | Technical Support | COO Agent | Solution |
| `solution.for_robot` | COO Agent | Alert Receiver | Solution + robot_id |

### Sécurité
- **AuthManager:** Authentification agents
- **AuditLog:** Traçabilité actions
- **Tokens:** Requis pour publish/subscribe

---

## Diagrammes

### Architecture Complète
Voir [docs/diagrams/message_bus_architecture.md](../diagrams/message_bus_architecture.md)

**Inclut:**
- Diagramme de séquence complet
- Architecture des composants
- Topics Message Bus
- Formats de messages

### Flow Simplifié

```
Robot → Alert Receiver → COO → Technical Support → COO → Alert Receiver → Robot
         (A2A)          (Bus)  (Bus)               (Bus)   (Bus)          (A2A)
```

---

## Fichiers Clés

```
agents/
├── main.py                          # Point d'entrée UNIQUE
├── alert_receiver/
│   └── alert_receiver_a2a.py        # Alert Receiver (A2A + Bus)
├── coordinator/
│   └── coo_agent.py                 # COO Agent (Orchestrateur)
└── support/
    └── technical_support_agent.py   # Technical Support Agent
```

---

## Développement

### Ajouter un Nouvel Agent

1. **Créer l'agent** dans `agents/[category]/`
2. **Hériter de** `BaseAgent`
3. **Initialiser** avec `message_bus` partagé
4. **Subscribe** aux topics pertinents
5. **Ajouter dans** `agents/main.py`:
```python
new_agent = NewAgent(
    agent_id="new_agent_001",
    auth_manager=shared_auth,
    message_bus=shared_bus
)
await new_agent.start()
```

### Modifier Routing

Éditer `tools/coordinator/coordinator_tools.py`:

```python
def _parse_agent_from_description(...):
    if task_type == "mon_nouveau_type":
        return {
            "assigned_agent": "mon_agent",
            "reason": "...",
            "confidence": 0.90
        }
```

---

## Tests

### Test Complet
```bash
# Terminal 1
python agents/main.py

# Terminal 2
python start_robot.py

# Terminal 3
python start_simulator.py
# Puis option 1 (E01)
```

### Vérifier Logs
- Alert Receiver: "📤 Forwarding alert to COO"
- COO: "✅ Agent assigné: technical_support"
- Technical Support: "✅ Task completed"
- COO: "📤 Solution forwarded"

---

## Ressources

- [Architecture Générale](../architecture.md)
- [RAG Documentation](../rag_documentation.md)
- [API Documentation](../api_documentation.md)
- [Setup Guide](../setup_guide.md)
