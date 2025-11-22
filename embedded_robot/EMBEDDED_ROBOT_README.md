# 🤖 Robot Embarqué - Google ADK (Version Finale)

> **Projet Capstone Kaggle - 5 Days of AI Agents**  
> Architecture complète avec tous les patterns ADK enseignés

---

## 🎯 Objectif

Démontrer la maîtrise de **Google ADK** à travers un robot intelligent qui :
- ✅ **Auto-diagnostique** ses problèmes (Loop Agent)
- ✅ **Apprend** des pannes passées (Memory)
- ✅ **Se répare** automatiquement si possible (Self-healing)
- ✅ **Escalade** intelligemment vers le support (A2A)
- ✅ **Re-escalade** si une solution échoue

---

## 🏗️ Architecture Complète

```
embedded_robot/
├── main.py                          # ✅ FastAPI + ADK (PORT 8001)
│
├── adk_agents/                      # Agents ADK purs
│   ├── sensor_agents.py            # Sequential: Lecture capteurs
│   ├── diagnostic_agent.py         # Loop: Diagnostics itératifs
│   ├── action_agent.py             # Exécution solutions
│   └── hardware_simulator.py       # Simulation hardware
│
└── README.md                        # Ce fichier
```

**🔥 TOUT est refait en ADK pur ! Pas de mélange avec l'ancien code.**

---

## 🚀 Démarrage Rapide

### 1. Installation

```bash
pip install google-adk google-generativeai fastapi uvicorn httpx
```

### 2. Configuration

Créer `.env` :
```bash
GOOGLE_API_KEY=votre_clé_gemini
```

### 3. Lancement

```bash
# Terminal 1 : Support System (PORT 8000)
cd agents
python main.py

# Terminal 2 : Robot Embarqué (PORT 8001)  
cd embedded_robot
python main.py
```

### 4. Accéder

- **API Docs** : http://localhost:8001/docs
- **Status** : http://localhost:8001/status

---

## 🎮 Scénarios de Démo

### Scénario 1 : Bug Simple (Auto-résolution)

```bash
# 1. Déclencher E01 (Roues bloquées)
curl -X POST http://localhost:8001/simulate/error/E01

# Résultat attendu :
# - 🔍 Capteurs détectent → Diagnostics identifient
# - 📤 Escalade vers support (pas de mémoire)
# - 📥 Reçoit solution "clean_wheels"
# - ⚙️ Applique → Succès
# - 💾 Stocke en mémoire
```

### Scénario 2 : Même Bug (Memory + Self-Healing)

```bash
# 2. Re-déclencher E01
curl -X POST http://localhost:8001/simulate/error/E01

# Résultat attendu :
# - 🧠 Memory trouve solution
# - 🤖 Auto-résolution (SANS escalade)
# - ✅ Problème résolu seul
```

### Scénario 3 : Solution Échoue (Re-escalation)

Ce scénario nécessite un test Python :

```python
import requests

# 1. Simuler E01 persistant
hardware = robot_state.hardware
hardware.simulate_wheels_blocked(persistent=True)

# 2. Envoyer solution
response = requests.post("http://localhost:8001/solution/execute", json={
    "action": "clean_wheels",
    "error_code": "E01",
    "ticket_id": "ROBO-0001",
    "agent_id": "tech_support"
})

# Résultat :
# - ⚙️ Solution s'exécute
# - ❌ MAIS erreur persiste
# - 🔄 Re-escalation automatique vers support
# - 📨 Notification : "Solution clean_wheels a échoué"
```

### Scénario 4 : Erreur Critique (HITL)

```bash
# Déclencher E07 (Batterie critique)
curl -X POST http://localhost:8001/simulate/error/E07

# Résultat :
# - 🚨 Détection erreur critique
# - 📤 Escalade immédiate (pas d'auto-résolution)
# - ⏳ Indication "HITL requis"
# - 🛑 Robot en mode safe
```

---

## 📊 Flow Complet avec Re-escalation

```
┌─────────────────────────────────────────────────┐
│  1. BUG DÉTECTÉ (E01 - Roues bloquées)          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  2. DIAGNOSTICS (Loop Agent)                    │
│     - Analyse symptômes                         │
│     - Corrèle à E01                             │
│     - Identifie cause : obstruction             │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  3. MEMORY SEARCH                               │
│     - Cherche solution pour E01                 │
│     - Résultat : Aucune (premier incident)      │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  4. ESCALATION A2A → Support                    │
│     POST /alerts/robot-issue                    │
│     {                                           │
│       "error_code": "E01",                      │
│       "diagnostics": {...}                      │
│     }                                           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  5. SOLUTION REÇUE du Support                   │
│     POST /solution/execute                      │
│     {                                           │
│       "action": "clean_wheels",                 │
│       "error_code": "E01",                      │
│       "ticket_id": "ROBO-0001"                  │
│     }                                           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  6. EXÉCUTION (Action Agent)                    │
│     - Applique clean_wheels                     │
│     - Status: "success"                         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  7. VÉRIFICATION POST-SOLUTION                  │
│     - Wait 2 seconds                            │
│     - Check error still present?                │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    ✅ Résolu        ❌ Erreur persiste
         │                 │
         │                 ▼
         │    ┌─────────────────────────────┐
         │    │  8. RE-ESCALATION AUTO       │
         │    │     POST /alerts/solution-   │
         │    │          failed              │
         │    │     {                        │
         │    │       "ticket_id": "0001",   │
         │    │       "attempted_solution":  │
         │    │          "clean_wheels",     │
         │    │       "failure_reason": "...",│
         │    │       "requires_escalation": │
         │    │          true                │
         │    │     }                        │
         │    └──────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  9. MEMORY UPDATE                               │
│     - Store "E01 → clean_wheels" (success/fail) │
│     - Update confidence score                   │
└─────────────────────────────────────────────────┘
```

---

## 🧠 Concepts ADK Démontrés

### ✅ 1. Sequential Agent (Day 1b)
**Fichier** : `sensor_agents.py`
```python
# Lecture ordonnée des capteurs
sensor_sequential = SequentialAgent(
    sub_agents=[sensor_reader]
)
```

### ✅ 2. Loop Agent (Day 1b)
**Fichier** : `diagnostic_agent.py`
```python
# Diagnostics itératifs jusqu'à trouver cause
diagnostic_loop = LoopAgent(
    sub_agents=[analyzer, refiner],
    max_iterations=3
)
```

### ✅ 3. Sessions (Day 3a)
**Fichier** : `main.py`
```python
# Historique des incidents
await session_service.create_session(...)
```

### ✅ 4. Memory (Day 3b)
**Fichier** : `main.py`
```python
# Apprentissage des solutions
def search_memory(error_code):
    # Cherche solutions passées
    ...
```

### ✅ 5. Runner ADK
**Fichier** : `main.py`
```python
# Orchestration via Runner
runner = Runner(
    agent=main_agent,
    session_service=session_service,
    memory_service=memory_service
)
```

### ✅ 6. MCP Tools (Capteurs)
**Fichier** : `sensor_agents.py`
```python
# Outils réutilisables
def read_all_sensors():
    return hardware.get_sensor_readings()
```

### ✅ 7. A2A Communication (Day 5a)
**Fichier** : `main.py`
```python
# Escalade vers support
def escalate_to_support(...):
    # POST A2A request
    ...
```

---

## 🔥 Points Forts

### 1. Re-escalation Automatique

```python
# Si solution échoue, re-escalation automatique
if error_persists_after_solution:
    await re_escalate_failed_solution(
        error_code=error_code,
        failed_solution=solution.action,
        ticket_id=solution.ticket_id
    )
```

### 2. Gestion HITL

```python
# Détection automatique des cas HITL
if solution.requires_hitl or error_code in ["E07", "E08", "E09"]:
    robot_state.waiting_for_hitl = True
    return {"status": "pending_hitl"}
```

### 3. Memory qui Apprend

```python
# Confiance évolue selon succès/échecs
if solution_worked:
    memory.success_count += 1
else:
    memory.failure_count += 1

confidence = success / total
```

---

## 📊 Métriques Trackées

```json
{
  "adk_metrics": {
    "self_resolutions": 5,
    "escalations": 3,
    "failed_solutions": 1,
    "self_resolution_rate": "62.5%"
  }
}
```

---

## 🧪 Tests

### Test 1 : Hardware Simulator

```bash
cd embedded_robot/adk_agents
python hardware_simulator.py

# Teste tous les scénarios hardware
```

### Test 2 : API Complète

```bash
# Lancer le serveur
python main.py

# Tester via FastAPI docs
# http://localhost:8001/docs
```

---

## 📚 Références

- **Google ADK** : https://google.github.io/adk-docs/
- **Kaggle Course** : https://www.kaggle.com/learn-guide/5-day-genai
- **Sequential Agents** : Day 1b
- **Loop Agents** : Day 1b
- **Sessions** : Day 3a
- **Memory** : Day 3b
- **A2A** : Day 5a

---

## ✅ Checklist Démo Kaggle

- [x] Tous les patterns ADK intégrés
- [x] Code 100% ADK (pas d'ancien code mélangé)
- [x] Re-escalation si solution échoue
- [x] HITL pour cas critiques
- [x] Memory + Self-healing
- [x] Métriques mesurables
- [x] API production-ready
- [x] Documentation complète

---

**🚀 Prêt à impressionner Kaggle !**