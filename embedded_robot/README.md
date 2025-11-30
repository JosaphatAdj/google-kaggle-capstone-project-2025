# 🤖 Embedded Robot - A2A Version

Robot embarqué autonome avec support Google ADK et protocole A2A pour communication avec système de support distant.

## 📋 Vue d'Ensemble

Le robot embarqué utilise Google ADK (Agent Development Kit) pour :
- Détecter automatiquement les erreurs hardware
- Escalader vers le système de support via A2A (Agent-to-Agent)
- Recevoir et exécuter des solutions structurées
- Gérer les interventions humaines (HITL)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│ Main Agent (robot_orchestrator)            │
│  - Détection erreurs                       │
│  - Délégation au workflow                  │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Support Workflow Agent (LoopAgent)         │
│  - Boucle jusqu'à résolution ou HITL       │
│  - Max 3 itérations                        │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Escalation Sequence (SequentialAgent)      │
│  1. RemoteA2aAgent → Alert Receiver        │
│  2. Solution Executor → Execute JSON       │
└─────────────────────────────────────────────┘
```

## 🚀 Démarrage

### Prérequis
```bash
pip install google-adk python-dotenv fastapi uvicorn
```

### Configuration
```bash
# Créer fichier .env à la racine
echo "GOOGLE_API_KEY=your_api_key_here" > ../.env
```

### Lancement
```bash
# Méthode 1: Direct
python main_a2a.py

# Méthode 2: Via launcher système
cd ..
python start_system.py
```

Le robot démarre sur **http://localhost:8001**

## 🧪 Test

### Console Interactive
```bash
python simulator_console.py
```

Commandes disponibles :
- `1` - Simuler E01 (Roues bloquées)
- `2` - Simuler E03 (Batterie faible)
- `3` - Simuler E07 (Critique - HITL)
- `h` - Intervention HITL (débloquer roues)
- `b` - Intervention HITL (refroidir batterie)
- `s` - Statut robot
- `q` - Quitter

### API Endpoints

#### Simuler une erreur
```bash
curl -X POST http://localhost:8001/simulate/error/E01
```

#### Vérifier statut
```bash
curl http://localhost:8001/status
```

#### Intervention HITL
```bash
curl -X POST http://localhost:8001/fix/clean_wheels
```

## 📊 Patterns Google ADK Utilisés

### Agents
- **LlmAgent** : Agent principal orchestrateur
- **RemoteA2aAgent** : Client A2A vers Alert Receiver
- **SequentialAgent** : Orchestration A2A → Execution
- **LoopAgent** : Ré-escalation automatique

### Outils
- **FunctionTool** : `execute_solution_structured`, `get_robot_status`
- **Runner** : Exécution asynchrone
- **Sessions & Memory** : Gestion contexte

### Communication
- **A2A Protocol** : Communication inter-agents native
- **Agent Card** : Découverte automatique du serveur

## 🔄 Flow d'Escalation

### Scénario 1: Résolution Automatique
```
1. Erreur E01 détectée
2. Main Agent → Support Workflow
3. RemoteA2A → Alert Receiver
4. JSON reçu: {"actions": ["clean_wheels"], "requires_hitl": false}
5. Exécution automatique
6. Vérification après 5s
7. ✅ Erreur résolue
```

### Scénario 2: HITL Immédiat (E07)
```
1. Erreur E07 (critique) détectée
2. Escalation A2A
3. JSON reçu: {"actions": ["cooldown"], "requires_hitl": true, "is_temporary_solution": true}
4. Exécution pré-solutions
5. waiting_for_hitl = True
6. ❌ Pas de ré-escalation (attend humain)
7. HITL via console: 'b'
8. ✅ Erreur résolue
```

### Scénario 3: Échecs Multiples → HITL
```
1. Erreur E01 détectée
2. Tentative #1 → Échec
3. Ré-escalation avec contexte échec
4. Tentative #2 → Échec
5. Ré-escalation critique
6. Tentative #3 → HITL forcé (requires_hitl=true)
7. waiting_for_hitl = True
8. HITL via console: 'h'
9. ✅ Erreur résolue
```

## 📁 Structure

```
embedded_robot/
├── main_a2a.py              # Point d'entrée principal
├── simulator_console.py      # Console de test interactive
├── adk_agents/
│   ├── sensor_agents.py      # SequentialAgent capteurs
│   ├── diagnostic_agent.py   # LoopAgent diagnostic
│   ├── action_agent.py       # Agent d'actions
│   ├── support_workflow_agent.py  # Sequential + Loop pour A2A
│   └── hardware_simulator.py # Simulation hardware
└── README.md                 # Ce fichier
```

## 🐛 Troubleshooting

### Robot ne démarre pas
- Vérifier que port 8001 est libre
- Vérifier `GOOGLE_API_KEY` dans `.env`
- Vérifier qu'Alert Receiver tourne (port 8000)

### A2A ne fonctionne pas
- Vérifier URL Alert Receiver: `http://localhost:8000`
- Tester agent card: `curl http://localhost:8000/.well-known/agent-card.json`
- Vérifier logs: `RemoteA2A` doit apparaître

### Solutions pas exécutées
- Vérifier que Sequential Agent reçoit bien le JSON
- Vérifier logs: `execute_solution_structured` doit être appelé
- Format JSON doit contenir: `actions`, `requires_hitl`, `error_code`

## 📚 Documentation Complémentaire

- [Alert Receiver README](../agents/alert_receiver/README.md)
- [Plan de Finalisation](../PLAN_FINALISATION.md)
- [Succès A2A](../SUCCES_A2A_FINAL.md)

## 🎯 Démo Rapide

```bash
# Terminal 1: Lancer tout le système
python start_system.py

# La console s'ouvre automatiquement
# Tapez: 3 (E07 - HITL immédiat)
# Puis: b (HITL refroidir)

# Ou tapez: 1 (E01 - test ré-escalation)
# Attendre 3 échecs automatiques
# Puis: h (HITL débloquer)
```

---

**Développé avec Google ADK - Démonstration Protocole A2A**
