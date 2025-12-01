# 🤖 RoboNest - Intelligent Multi-Agent Robot Support System

Production-grade autonomous robot fleet management system using **Google ADK** and **A2A Protocol**.

[![Google ADK](https://img.shields.io/badge/Google%20ADK-0.1.0-blue)](https://ai.google.dev/adk)
[![Python](https://img.shields.io/badge/Python-3.12+-green)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20%7C%202.5-orange)](https://ai.google.dev/)

---

## 📋 Overview

RoboNest is an intelligent multi-agent system designed to autonomously manage and resolve incidents for autonomous robot fleets. Built on Google's Agent Development Kit (ADK) and leveraging the standardized Agent-to-Agent (A2A) protocol, RoboNest demonstrates advanced agentic AI capabilities.

### Key Features

- ✅ **Autonomous Error Detection & Resolution** - Real-time monitoring and automated remediation
- ✅ **Intelligent Conditional Routing** - E01 local (2s), E02-E09 remote A2A (7s)  
- ✅ **Multi-Agent Orchestration** - 4 specialized agents coordinated via Message Bus
- ✅ **RAG-Powered Knowledge Base** - ChromaDB with technical documentation
- ✅ **HITL Integration** - Seamless escalation with Jira tickets and email notifications
- ✅ **Solution Verification & Re-escalation** - Automatic retry with failure context

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDED ROBOT (Port 8001)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  main_agent (Orchestrator)                                │  │
│  │    - Conditional Routing: E01→local, E02-E09→remote      │  │
│  │                                                            │  │
│  │  Sub-agents:                                              │  │
│  │    ├─ sensor_agent (SequentialAgent)                     │  │
│  │    ├─ diagnostic_agent (LoopAgent)                       │  │
│  │    ├─ action_agent (LlmAgent) - E01 only                │  │
│  │    └─ support_workflow_agent (LoopAgent)                │  │
│  │         ├─ formatter_agent - Structures alert            │  │
│  │         ├─ RemoteA2aAgent - A2A communication           │  │
│  │         ├─ solution_executor - Parses & executes         │  │
│  │         └─ status_checker - Verification                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ A2A Protocol (HTTP)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SUPPORT SYSTEM (Port 8000)                     │
│                                                                 │
│  ┌────────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │ Alert Receiver │──▶│  Message Bus │──▶│   COO Agent     │  │
│  │  (A2A Server)  │   │  (Pub/Sub)   │   │ (Coordinator)   │  │
│  │  - LlmAgent    │   │              │   │                 │  │
│  │  - RAG Tool    │   │  Topics:     │   │  Routes to:     │  │
│  │  - Classifier  │   │  • task.new  │   │  • Tech Support │  │
│  └────────────────┘   │  • assigned  │   │  • FAQ          │  │
│                       │  • completed │   │  • Complaints   │  │
│                       │  • solution  │   └─────────────────┘  │
│                       └──────────────┘                         │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────┐      │
│  │        Technical Support Agent                      │      │
│  │  - ERROR_SOLUTIONS mapping (deterministic)         │      │
│  │  - Jira ticket creation                            │      │
│  │  - Gmail HITL notifications                        │      │
│  │  - Solution generation                             │      │
│  └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.12+
python --version

# Clone repository
git clone <your-repo-url>
cd robonest-system
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
```

### Launch System

```bash
# Terminal 1: Main Support System (Alert Receiver, COO, Tech Support)
python agents/main.py

# Terminal 2: Embedded Robot
python start_robot.py

# Terminal 3 (Optional): Error Simulator
python start_simulator.py
```

### Health Checks

```bash
# Alert Receiver A2A card
curl http://localhost:8000/.well-known/agent-card.json

# Robot status
curl http://localhost:8001/status

# Expected: Robot operational, A2A connected
```

---

## 🧪 Demo Scenarios

### Scenario 1: E03 (Low Battery) - Automated Resolution

**Trigger:**
```bash
# In simulator console
Option 2: Simulate E03 (Low battery)
```

**Expected Workflow (~7 seconds):**
1. Robot detects battery at 15%
2. Formats alert with robot_id
3. Sends via A2A to Alert Receiver
4. Alert Receiver queries RAG, classifies as "high"
5. Routes to Technical Support via Message Bus
6. Tech Support generates solution: `["charge_battery", "return_to_dock"]`
7. Creates Jira ticket (e.g., ROB-36)
8. Robot fetches and executes actions
9. Verification confirms success ✅

**Logs:**
```
[Robot] 📤 Formatted: XR25-001 - E03
[Robot] HTTP Request: POST http://localhost:8000
[Main] 📋 Solution for E03: ['charge_battery', 'return_to_dock']
[Main] 🎫 Jira ticket created: ROB-36
[Robot] ⚙️ Executing action 1/2: charge_battery
[Robot] ⚙️ Executing action 2/2: return_to_dock
[Robot] ✅ Error E03 resolved
```

### Scenario 2: E07 (Battery Critical) - HITL Escalation

**Trigger:**
```bash
Option 3: Simulate E07 (Battery swollen)
```

**Expected Workflow (~12 seconds):**
1. Same workflow as E03
2. Tech Support detects `requires_hitl=True`
3. Creates CRITICAL Jira ticket
4. Sends escalation email to support team
5. Robot executes temporary safe actions: `["emergency_shutdown", "wait_for_hitl"]`
6. Robot enters `waiting_for_hitl=True` state
7. Waits for human intervention (no re-escalation loop) ⏳

### Scenario 3: E01 (Wheels Blocked) - Local Resolution

**Trigger:**
```bash
Option 1: Simulate E01 (Wheels blocked)
```

**Expected Workflow (~2 seconds):**
1. Robot detects wheels blocked
2. Routes to `action_agent` (local)
3. Executes `clean_wheels`
4. No remote call - handled entirely on robot ✅

**Benefit:** 5x faster than remote resolution

---

## 📊 Technology Stack

### AI & Agents
- **Google ADK 0.1.0** - Multi-agent orchestration framework
- **Gemini 2.0 Flash Lite** - Primary LLM (fast, cost-effective)
- **Gemini 2.5 Flash** - Enhanced LLM for complex reasoning
- **A2A Protocol** - Standardized agent-to-agent communication

### Backend
- **FastAPI** - Async web framework for A2A server
- **Python 3.12** - Modern async/await support
- **ChromaDB** - Vector database for RAG embeddings
- **Pydantic** - Data validation and JSON schemas

### Integrations
- **Jira Cloud API** - Ticket creation and tracking
- **Gmail API** - HITL email notifications
- **Custom Message Bus** - Internal pub/sub architecture

---

## 📁 Project Structure

```
robonest-system/
├── agents/
│   ├── main.py                          # System entry point
│   ├── alert_receiver/
│   │   └── alert_receiver_a2a.py       # A2A server + routing
│   ├── coordinator/
│   │   └── coo_agent.py                 # Message Bus coordinator
│   └── support/
│       ├── technical_support_agent.py   # Solution generator
│       └── error_solutions.py           # ERROR_SOLUTIONS mapping
│
├── embedded_robot/
│   ├── main_a2a.py                      # Robot main orchestrator
│   ├── start_robot.py                   # Robot launcher
│   └── adk_agents/
│       ├── sensor_agents.py             # Sequential agent
│       ├── diagnostic_agent.py          # Loop agent
│       ├── action_agent.py              # Local actions (E01)
│       ├── support_workflow_agent.py    # A2A workflow
│       └── hardware_simulator.py        # Hardware simulation
│
├── rag/
│   ├── chroma_db/                       # Vector database (included)
│   └── knowledge_base/                  # Technical documentation
│
├── start_simulator.py                   # Error simulator
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🐛 Troubleshooting

### Robot Cannot Reach Alert Receiver

```bash
# Verify A2A agent card is accessible
curl http://localhost:8000/.well-known/agent-card.json
```

**Solution:** Ensure Alert Receiver is running and port 8000 is open.

### Empty Solutions (0 actions)

**Symptom:** `📦 Structured solution: 0 actions`

**Solution:** Verify solutions come from backend via Message Bus only.

### JSON Parsing Errors

**Symptom:** `❌ Error parsing/executing solution`

**Solution:** See `execute_solution_structured` with robust regex extraction.

---

## 📈 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **E01 Latency** | ~2s | Local resolution |
| **E03 Latency** | ~7s | Full A2A workflow |
| **E07 Latency** | ~12s | Includes email |

---

## 🎓 Google ADK Patterns

- ✅ **LlmAgent, SequentialAgent, LoopAgent, RemoteA2aAgent**
- ✅ **A2A Protocol** - Agent discovery and messaging
- ✅ **FunctionTool** - Custom Python functions
- ✅ **RAG Integration** - ChromaDB knowledge retrieval
- ✅ **JSON Schema Validation** - Structured LLM outputs

---

## 📝 License

MIT License

---

**Ready to test?**

```bash
python agents/main.py    # Terminal 1
python start_robot.py     # Terminal 2
python start_simulator.py # Terminal 3
```

Then simulate E03 or E07! 🚀
