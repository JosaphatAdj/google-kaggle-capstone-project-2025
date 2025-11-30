# RoboNest System - Architecture

Architecture distribuée pour système de support robotique autonome utilisant Google ADK et Message Bus.

## Vue d'Ensemble

RoboNest est un système de support automatisé pour robots, utilisant:
- **Google ADK** pour agents intelligents (LlmAgent)
- **Message Bus** pour communication interne asynchrone
- **A2A Protocol** pour communication externe (robots)
- **RAG (Retrieval-Augmented Generation)** pour résolution problèmes

---

## Architecture Globale

```
┌─────────────┐
│   Robot     │ (Embedded System)
│  (A2A Client)│
└──────┬──────┘
       │ A2A HTTP
       ↓
┌──────────────────────────────────────────────────────┐
│          agents/main.py (Single Entry Point)          │
│                                                        │
│  ┌─────────────────────────────────────────────────┐ │
│  │          Shared Infrastructure                  │ │
│  │  • Message Bus (SINGLE instance)               │ │
│  │  • AuthManager                                 │ │
│  │  • AuditLog                                    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐│
│  │Alert Receiver│  │ COO Agent   │  │Technical     ││
│  │  (A2A+Bus)   │  │(Orchestrator)  │Support Agent ││
│  └──────────────┘  └─────────────┘  └───────────────┘│
└──────────────────────────────────────────────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                 │
                 ↓
       ┌──────────────────┐
       │  External Tools  │
       │  • RAG (KB)     │
       │  • Gmail (HITL) │
       │  • Jira (Tickets)│
       └──────────────────┘
```

---

## Composants Principaux

### 1. Point d'Entrée: `agents/main.py`

**Responsabilité unique:** Créer et orchestrer TOUS les composants du système.

**Initialisation:**
1. Appelle `initialize_infrastructure()` → Crée Message Bus + Auth + Audit
2. Crée COO Agent avec Message Bus partagé
3. Crée Technical Support Agent avec Message Bus partagé
4. Crée Alert Receiver Agent
5. Expose Alert Receiver en A2A (port 8000)
6. Lance serveur A2A (blocking)

**Résultat:** Tous les agents partagent la MÊME instance de Message Bus.

---

### 2. Alert Receiver Agent

**Type:** LlmAgent (Gemini 2.0 Flash Lite) + A2A Server  
**Fichier:** `agents/alert_receiver/alert_receiver_a2a.py`  
**Port:** 8000 (A2A)

**Rôle:**
- Interface entre robots externes (A2A) et système interne (Message Bus)
- Analyse et classification d'alertes
- Ne résout PAS les problèmes (routage uniquement)

**Flux entrant (Robot):**
1. Robot envoie alerte via A2A
2. `query_error_code()` consulte RAG
3. `classify_error()` détermine urgence
4. `process_robot_alert()` publie sur Message Bus
5. Retourne ACK au robot

**Flux sortant (Solution):**
1. Reçoit solution du COO via Message Bus
2. Queue dans `solution_queue[robot_id]`
3. Robot poll via `get_pending_solution()`
4. Retourne solution JSON via A2A

---

### 3. COO Agent (Orchestrateur)

**Type:** BaseAgent + CoordinatorTools (RAG-powered)  
**Fichier:** `agents/coordinator/coo_agent.py`

**Rôle:**
- Routing intelligent de tâches
- Délégation aux agents spécialisés
- Supervision et forward de solutions

**Flux tâches:**
1. Reçoit `task.new` du Message Bus
2. `determine_agent_assignment()` consulte RAG
3. Route selon `task_type`:
   - `"robot_alert"` → `technical_support` (prioritaire)
   - Autres types → Autres agents
4. Publie `task.assigned.[agent_type]`

**Flux solutions:**
1. Reçoit `task.completed` de l'agent
2. Si `task_type == "robot_alert"`:
   - Extrait `robot_id` et `solution`
   - Publie `solution.for_robot` vers Alert Receiver

---

### 4. Technical Support Agent

**Type:** BaseAgent + RAG + External Tools  
**Fichier:** `agents/support/technical_support_agent.py`

**Rôle:**
- Résolution de problèmes robots
- Consultation RAG pour solutions
- Gestion HITL (Human-In-The-Loop)

**Flux résolution:**
1. Reçoit `task.assigned.technical_support`
2. `process_task()`:
   - Analyse error_code et contexte
   - Détermine solution (RAG ou heuristique)
   - Crée ticket Jira pour tracking
   - Si HITL requis: `send_escalation_email()`
3. Retourne solution JSON:
```json
{
  "actions": ["action1", "action2"],
  "error_code": "E01",
  "ticket_id": "ROB-XXX",
  "requires_hitl": false,
  "is_temporary_solution": false
}
```
4. Publie `task.completed`

---

## Communication

### Message Bus (Interne)

**Topics:**

| Topic | Publisher | Subscriber | Payload |
|-------|-----------|------------|---------|
| `task.new` | Alert Receiver | COO | Nouvelle alerte |
| `task.assigned.technical_support` | COO | Technical Support | Tâche assignée |
| `task.completed` | Technical Support | COO | Solution |
| `solution.for_robot` | COO | Alert Receiver | Solution + robot_id |

**Sécurité:**
- AuthManager: Tokens pour publish/subscribe
- AuditLog: Traçabilité complète

### A2A Protocol (Externe)

**Endpoints Alert Receiver:**
- `POST /sessions/{session_id}/turn` - Envoi alerte
- Agent Card: `GET /.well-known/agent-card.json`

**Format alerte:**
```json
{
  "robot_id": "XR25-001",
  "error_code": "E01",
  "description": "Wheels blocked",
  "sensor_data": {...}
}
```

**Format solution:**
```json
{
  "actions": ["clean_wheels", "recalibrate_motors"],
  "requires_hitl": false
}
```

---

## Outils Externes

### RAG Tool

**Fichier:** `tools/rag/rag_tool.py`

**Base de connaissances:**
- `rag/knowledge_base/products/error_codes/` - Codes erreur robots
- `rag/knowledge_base/internal/architecture/` - Rôles agents
- `rag/knowledge_base/support/resolution_guides/` - Guides résolution

**Utilisateurs:**
- Alert Receiver (classification)
- COO Agent (routing)
- Technical Support (résolution)

### Gmail Tool (HITL)

**Fichier:** `tools/gmail/gmail_tool.py`

**Usage:**
- Notifications HITL pour erreurs critiques
- E07 (Battery Critical), E08 (Firmware), E09 (Safety)

**Configuration:** `.env`
```env
GMAIL_SENDER_EMAIL=...
GMAIL_APP_PASSWORD=...
```

### Jira Tool (Tracking)

**Fichier:** `tools/jira/jira_tool.py`

**Usage:**
- Création tickets pour chaque alerte
- Tracking résolutions

**Configuration:** `.env`
```env
JIRA_SERVER=https://company.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=ROB
```

---

## Sécurité

### AuthManager

**Fichier:** `security/auth_manager.py`

**Fonctionnalités:**
- Enregistrement agents
- Génération tokens
- Validation permissions

### AuditLog

**Fichier:** `security/audit_log.py`

**Logs:**
- Messages reçus/envoyés
- Actions agents
- Erreurs système

---

## Déploiement

### Prérequis

```bash
pip install -r requirements.txt
```

**Dépendances clés:**
- `google-adk` - Agents + A2A
- `google-generativeai` - Gemini API
- `fastapi` - A2A Server
- `uvicorn` - ASGI Server

### Configuration

**Créer `.env`:**
```env
GOOGLE_API_KEY=votre_clé_api_gemini

# Optionnel (HITL)
GMAIL_SENDER_EMAIL=...
GMAIL_APP_PASSWORD=...
JIRA_SERVER=...
JIRA_API_TOKEN=...
```

### Lancement

**Production (1 terminal):**
```bash
python agents/main.py
```

**Développement (3 terminaux):**
```bash
# Terminal 1 - Système
python agents/main.py

# Terminal 2 - Robot
python start_robot.py

# Terminal 3 - Simulateur
python start_simulator.py
```

---

## Scaling

### Horizontal

**Agents parallèles:**
```python
# Créer plusieurs instances Technical Support
tech_support_1 = TechnicalSupportAgent(agent_id="tech_support_001", ...)
tech_support_2 = TechnicalSupportAgent(agent_id="tech_support_002", ...)
tech_support_3 = TechnicalSupportAgent(agent_id="tech_support_003", ...)
```

**Load balancing:** COO Agent distribue automatiquement

### Vertical

**Message Bus distribué:**
- Remplacer in-memory par Redis
- Modifier `communication/message_bus.py`

---

## Monitoring

### Logs

**Format:**
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Fichiers:**
- `agents/main.py` - Système principal
- `start_robot.py` - Robot embarqué
- `start_simulator.py` - Console simulation

### Métriques COO

```python
{
  "tasks_received": 42,
  "tasks_delegated": 40,
  "tasks_completed": 38,
  "tasks_failed": 2,
  "average_response_time": "2.3s"
}
```

---

## Ressources

- **QUICKSTART:** [QUICKSTART.md](../QUICKSTART.md)
- **Diagrammes:** [docs/diagrams/message_bus_architecture.md](diagrams/message_bus_architecture.md)
- **Agents:** [docs/agents_documentation.md](agents_documentation.md)
- **RAG:** [docs/rag_documentation.md](rag_documentation.md)
- **API:** [docs/api_documentation.md](api_documentation.md)

---

## Design Patterns

### Pub/Sub (Message Bus)
- Découplage agents
- Communication asynchrone
- Scalabilité

### Single Entry Point
- Une instance Message Bus
- Tous agents partagent
- Garantie communication

### Agent Specialization
- Alert Receiver: Routing
- COO: Orchestration
- Technical Support: Résolution

### RAG-Powered Decisions
- COO routing depuis knowledge base
- Technical Support solutions depuis RAG
- Évolutif sans code changes
