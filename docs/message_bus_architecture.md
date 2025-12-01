# Architecture Message Bus - RoboNest System

Ce diagramme illustre le workflow complet du système RoboNest utilisant Message Bus pour la communication entre agents.

## Flow Principal: Robot Alert → Resolution

```mermaid
sequenceDiagram
    participant R as Robot (Embedded)
    participant AR as Alert Receiver<br/>(A2A Server)
    participant MB as Message Bus
    participant COO as COO Agent<br/>(Orchestrator)
    participant TS as Technical Support<br/>Agent
    
    Note over R,TS: Phase 1: Alert Detection & Routing
    R->>AR: [A2A] POST /sessions/xxx/turn<br/>Alert E01 (wheels blocked)
    activate AR
    AR->>AR: query_error_code(RAG)<br/>classify_error()
    AR->>MB: publish(topic="task.new")<br/>task_type="robot_alert"
    AR->>R: [A2A] ACK: "Alert received,<br/>forwarded to support"
    deactivate AR
    
    Note over MB,COO: Phase 2: Task Assignment
    MB->>COO: notify: task.new
    activate COO
    COO->>COO: determine_agent_assignment()<br/>→ "technical_support"
    COO->>MB: publish(topic="task.assigned.<br/>technical_support")
    deactivate COO
    
    Note over MB,TS: Phase 3: Problem Resolution
    MB->>TS: notify: task.assigned
    activate TS
    TS->>TS: process_task()<br/>Query RAG KB<br/>Determine solution
    TS->>TS: create_jira_ticket()<br/>(if needed)
    TS->>TS: send_escalation_email()<br/>(if HITL required)
    TS->>MB: publish(topic="task.completed")<br/>solution JSON
    deactivate TS
    
    Note over COO,AR: Phase 4: Solution Forwarding
    MB->>COO: notify: task.completed
    activate COO
    COO->>COO: Check task_type="robot_alert"<br/>Extract robot_id
    COO->>MB: publish(topic="solution.for_robot")<br/>robot_id + solution
    deactivate COO
    
    MB->>AR: notify: solution.for_robot
    activate AR
    AR->>AR: Queue solution[robot_id]
    deactivate AR
    
    Note over R,AR: Phase 5: Execution
    R->>AR: [A2A] get_pending_solution(robot_id)
    activate AR
    AR->>R: [A2A] Solution JSON:<br/>{"actions": ["clean_wheels",<br/>"recalibrate_motors"]}
    deactivate AR
    
    R->>R: Execute actions<br/>✓ clean_wheels()<br/>✓ recalibrate_motors()
    
    Note over R,TS: ✅ Alert Resolved
```

## Architecture des Composants

```mermaid
graph TB
    subgraph "External"
        Robot[🤖 Robot<br/>Embedded System]
    end
    
    subgraph "Entry Point: agents/main.py"
        Main[🚀 Main System<br/>Single Entry Point]
    end
    
    subgraph "Shared Infrastructure"
        MB[📬 Message Bus<br/>SINGLE Instance]
        Auth[🔐 AuthManager]
        Audit[📋 AuditLog]
    end
    
    subgraph "Internal Agents"
        AR[📡 Alert Receiver<br/>A2A + LlmAgent]
        COO[🧠 COO Agent<br/>Orchestrator]
        TS[🔧 Technical Support<br/>Agent]
    end
    
    subgraph "External Tools"
        RAG[📚 RAG Tool<br/>Knowledge Base]
        Gmail[📧 Gmail Tool<br/>HITL Notifications]
        Jira[🎫 Jira Tool<br/>Ticket Creation]
    end
    
    Robot -.A2A Protocol.-> AR
    Main -->|Creates & Shares| MB
    Main -->|Creates & Shares| Auth
    Main -->|Creates & Shares| Audit
    Main -->|Initializes| AR
    Main -->|Initializes| COO
    Main -->|Initializes| TS
    
    AR -->|Subscribes| MB
    COO -->|Subscribes| MB
    TS -->|Subscribes| MB
    
    AR -->|Uses| RAG
    TS -->|Uses| RAG
    TS -->|Uses| Gmail
    TS -->|Uses| Jira
    COO -->|Uses| RAG
    
    style Main fill:#4CAF50,stroke:#2E7D32,color:#fff
    style MB fill:#2196F3,stroke:#1565C0,color:#fff
    style Robot fill:#FF9800,stroke:#E65100,color:#fff
```

## Topics Message Bus

```mermaid
graph LR
    subgraph "Message Bus Topics"
        T1[task.new]
        T2[task.assigned.<br/>technical_support]
        T3[task.completed]
        T4[solution.for_robot]
    end
    
    AR[Alert Receiver] -->|Publishes| T1
    COO[COO Agent] -->|Subscribes| T1
    COO -->|Publishes| T2
    TS[Technical Support] -->|Subscribes| T2
    TS -->|Publishes| T3
    COO -->|Subscribes| T3
    COO -->|Publishes| T4
    AR -->|Subscribes| T4
    
    style T1 fill:#E1F5FE,stroke:#0277BD
    style T2 fill:#F3E5F5,stroke:#6A1B9A
    style T3 fill:#E8F5E9,stroke:#2E7D32
    style T4 fill:#FFF3E0,stroke:#E65100
```

## Format des Messages

### task.new (Alert Receiver → COO)
```json
{
  "task_id": "ALERT-XR25-001-1733012345",
  "task_type": "robot_alert",
  "robot_id": "XR25-001",
  "error_code": "E01",
  "severity": "medium",
  "description": "Wheels blocked - unable to move",
  "context": {
    "sensor_data": {
      "battery_level": 85,
      "temperature": 42.5,
      "location": {"x": 10.5, "y": 20.3}
    }
  }
}
```

### task.assigned.technical_support (COO → Technical Support)
```json
{
  "task_id": "ALERT-XR25-001-1733012345",
  "assigned_to": "tech_support_001",
  "task_data": { /* same as task.new */ },
  "assignment_reason": "Robot alert requires technical support"
}
```

### task.completed (Technical Support → COO)
```json
{
  "task_id": "ALERT-XR25-001-1733012345",
  "status": "completed",
  "result": {
    "actions": ["clean_wheels", "recalibrate_motors"],
    "error_code": "E01",
    "ticket_id": "ROB-123",
    "requires_hitl": false,
    "is_temporary_solution": false
  }
}
```

### solution.for_robot (COO → Alert Receiver)
```json
{
  "robot_id": "XR25-001",
  "task_id": "ALERT-XR25-001-1733012345",
  "solution": {
    "actions": ["clean_wheels", "recalibrate_motors"],
    "error_code": "E01",
    "requires_hitl": false
  }
}
```

## Lancement du Système

**Un seul point d'entrée:**
```bash
# Terminal 1 - Système complet (Message Bus + tous les agents)
python agents/main.py

# Terminal 2 - Robot embarqué
python start_robot.py

# Terminal 3 - Console de simulation
python start_simulator.py
```

## Agents et Leurs Rôles

| Agent | Type | Responsabilités | Topics Subscribed | Topics Published |
|-------|------|----------------|-------------------|------------------|
| **Alert Receiver** | LlmAgent + A2A | - Reçoit alertes robot via A2A<br/>- Analyse avec RAG<br/>- Route vers COO | `solution.for_robot` | `task.new` |
| **COO Agent** | Orchestrator | - Routing intelligent<br/>- Délégation de tâches<br/>- Forward solutions | `task.new`<br/>`task.completed` | `task.assigned.*`<br/>`solution.for_robot` |
| **Technical Support** | Resolver | - Résolution problèmes<br/>- Consultation RAG<br/>- Création Jira/Gmail | `task.assigned.technical_support` | `task.completed` |

## Notes Importantes

1. **Message Bus Unique**: Tous les agents partagent la MÊME instance de Message Bus créée dans `agents/main.py`
2. **A2A Exposition**: Alert Receiver est exposé en A2A sur port 8000 pour communication avec le robot
3. **Async Communication**: Flux asynchrone complet via Message Bus
4. **HITL Support**: Technical Support peut escalader vers humains via Gmail + Jira
