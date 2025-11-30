# Agents - RoboNest System

Ce dossier contient tous les agents du système RoboNest utilisant Google ADK et Message Bus.

## Structure

```
agents/
├── main.py                          # Point d'entrée UNIQUE du système
├── base/                            # Classe BaseAgent
│   └── base_agent.py
├── alert_receiver/                  # Agent d'interface A2A
│   └── alert_receiver_a2a.py
├── coordinator/                     # Agent orchestrateur (COO)
│   └── coo_agent.py
└── support/
    └── technical_support_agent.py  # Agent de résolution technique
```

## 🚀 Lancement

**Point d'entrée unique:**
```bash
python agents/main.py
```

Ce script:
1. Crée UNE instance de Message Bus partagée
2. Initialise tous les agents avec cette instance
3. Expose Alert Receiver en A2A (port 8000)
4. Lance le serveur A2A

**Important:** NE PAS lancer les agents séparément ! Ils doivent tous partager la même instance de Message Bus.

## Agents

### Alert Receiver (`alert_receiver/`)

**Type:** LlmAgent + A2A Server  
**Port:** 8000

**Rôle:**
- Interface A2A avec robots externes
- Analyse et classification d'alertes
- Routing vers système interne via Message Bus

**Communication:**
- **Entrée:** A2A (robots)
- **Sortie interne:** Message Bus (`task.new`)
- **Entrée interne:** Message Bus (`solution.for_robot`)
- **Sortie:** A2A (robots)

### COO Agent (`coordinator/`)

**Type:** BaseAgent + CoordinatorTools

**Rôle:**
- Orchestration et routing intelligent
- Délégation de tâches aux agents spécialisés
- Forward de solutions vers Alert Receiver

**Communication:**
- Subscribe: `task.new`, `task.completed`
- Publish: `task.assigned.*`, `solution.for_robot`

### Technical Support Agent (`support/`)

**Type:** BaseAgent + RAG + External Tools

**Rôle:**
- Résolution de problèmes techniques robots
- Consultation RAG Knowledge Base
- Gestion HITL (escalations Gmail/Jira)

**Communication:**
- Subscribe: `task.assigned.technical_support`
- Publish: `task.completed`

## Workflow Complet

```
Robot
  ↓ (A2A)
Alert Receiver
  ↓ (Message Bus: task.new)
COO Agent
  ↓ (Message Bus: task.assigned.technical_support)
Technical Support Agent
  ├─ RAG (error resolution)
  ├─ Jira (ticket creation)
  └─ Gmail (HITL if needed)
  ↓ (Message Bus: task.completed)
COO Agent
  ↓ (Message Bus: solution.for_robot)
Alert Receiver
  ↓ (A2A)
Robot (execute actions)
```

## Configuration

**Variables d'environnement:**
```env
# Obligatoire
GOOGLE_API_KEY=votre_clé_api_gemini

# Optionnel (HITL)
GMAIL_SENDER_EMAIL=...
GMAIL_APP_PASSWORD=...
JIRA_SERVER=...
JIRA_API_TOKEN=...
```

## Documentation

- **Architecture complète:** [../docs/architecture.md](../docs/architecture.md)
- **Documentation agents:** [../docs/agents_documentation.md](../docs/agents_documentation.md)
- **Diagrammes:** [../docs/diagrams/message_bus_architecture.md](../docs/diagrams/message_bus_architecture.md)
- **Quick Start:** [../QUICKSTART.md](../QUICKSTART.md)

## Développement

### Ajouter un nouvel agent

1. **Créer classe** qui hérite de `BaseAgent`
2. **Implémenter** méthodes requises
3. **Ajouter dans `main.py`:**
```python
new_agent = NewAgent(
    agent_id="new_agent_001",
    auth_manager=shared_auth,
    message_bus=shared_bus  # ← Même instance !
)
await new_agent.start()
```

### Modifier routing

Éditer `tools/coordinator/coordinator_tools.py` dans `_parse_agent_from_description()`

## Tests

```bash
# Terminal 1 - Système complet
python agents/main.py

# Terminal 2 - Robot
python start_robot.py

# Terminal 3 - Simulateur
python start_simulator.py
```

Puis dans simulateur: taper `1` pour test E01 (roues bloquées)
