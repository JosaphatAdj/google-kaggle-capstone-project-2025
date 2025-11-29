# 🚀 Guide de Démarrage - RoboNest A2A

## 📋 Architecture A2A

Le système utilise maintenant le **protocole A2A natif de Google ADK** pour la communication entre le robot et le système de support.

```
┌──────────────────────────────────────┐
│   Système Principal (Port 8000)      │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Alert Receiver A2A Server      │ │
│  │ (alert_receiver_a2a.py)        │ │
│  │                                │ │
│  │ • LlmAgent + to_a2a()          │ │
│  │ • /.well-known/agent-card.json │ │
│  │ • Tools: process_alert, etc.   │ │
│  └────────────────────────────────┘ │
│            ▲                         │
│            │ A2A Protocol             │
└────────────┼─────────────────────────┘
             │
             │ RemoteA2aAgent
             │
┌────────────▼─────────────────────────┐
│   Robot Embarqué (Port 8001)         │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Robot Main Agent               │ │
│  │ (main_a2a.py)                  │ │
│  │                                │ │
│  │ Sub-agents:                    │ │
│  │  • sensor_agent (Sequential)   │ │
│  │  • diagnostic_agent (Loop)     │ │
│  │  • action_agent                │ │
│  │  • remote_support (A2A)  ✅    │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

---

## 🆕 Nouveaux Fichiers

### 1. `agents/alert_receiver/alert_receiver_a2a.py`
- **Serveur A2A** pour recevoir alertes robots
- Utilise `to_a2a()` pour exposer l'agent via A2A
- Tools: `process_robot_alert`, `provide_solution`, `get_pending_solution`

### 2. `embedded_robot/main_a2a.py`
- **Client A2A** pour le robot
- Utilise `RemoteA2aAgent` pour se connecter au support
- Communication automatique via sub-agent

### 3. `embedded_robot/simulator_console.py`
- **Console interactive** pour simuler erreurs et HITL
- Interface colorée dans le terminal

---

## ⚙️Démarrage Step-by-Step

### Prérequis
```bash
pip install google-adk google-generativeai fastapi uvicorn httpx
```

### Étape 1: Lancer le Système Principal (Alert Receiver A2A)

**Terminal 1:**
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\agents\alert_receiver"
python alert_receiver_a2a.py
```

**Vérification:**
- Server démarre sur port 8000
- Agent card disponible sur: http://localhost:8000/.well-known/agent-card.json

### Étape 2: Lancer le Robot (Client A2A)

**Terminal 2:**
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python main_a2a.py
```

**Vérification:**
- Robot démarre sur port 8001
- Se connecte automatiquement à Alert Receiver via A2A
- API Docs: http://localhost:8001/docs

### Étape 3: Lancer la Console Interactive

**Terminal 3:**
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python simulator_console.py
```

---

## 🎮 Utilisation Console Interactive

```
🤖 ROBONEST ROBOT SIMULATOR - A2A VERSION
==========================================================

Available Commands:
  1 - Simulate E01 (Roues bloquées)
  2 - Simulate E03 (Batterie faible)
  3 - Simulate E07 (Batterie critique - HITL)
  h - Intervention Humaine (HITL) - débloquer roues
  b - Intervention Humaine (HITL) - refroidir batterie
  s - Statut Robot
  q - Quit
```

### Scénarios de Test

#### ✅ Scénario 1: Escalation Normale (E01)
1. Tapez `1` pour simuler E01 (roues bloquées)
2. Le robot détecte l'erreur
3. Escalade automatiquement via A2A vers Alert Receiver
4. Alert Receiver traite et propose solution
5. Solution renvoyée au robot via A2A
6. Robot exécute la solution

#### ✅ Scénario 2: HITL Requis (E07)
1. Tapez `3` pour simuler E07 (batterie critique)
2. Robot détecte erreur critique
3. Escalade avec flag `requires_hitl=True`
4. Robot entre en mode attente HITL
5. Tapez `b` pour intervention humaine (refroidissement)
6. Robot reprend opérations normales

#### ✅ Scénario 3: Statut
1. Tapez `s` à tout moment pour voir:
   - État du robot
   - Capteurs actuels
   - Métriques (escalations, auto-résolutions, etc.)
   - Protocole utilisé (A2A)

---

## 🔍 Flow Détaillé A2A

### 1. Détection Erreur
```
Hardware Simulator détecte E01
→ run_diagnostics() capture
→ handle_error_with_adk(E01)
```

### 2. Analyse par Agent Principal
```
Runner démarre avec query:
"Error detected: E01 (Wheels blocked)
Sensor data: Battery 85%, Temperature 40°C
Please handle this error. Escalate to support if needed."
```

### 3. Agent Principal Décide
```
main_agent:
- Consulte search_memory → Aucune solution
- Décide d'escalader
- Utilise remote_support_agent (sous-agent A2A)
```

### 4. Communication A2A
```python
remote_support_agent (RemoteA2aAgent):
- Se connecte à http://localhost:8000/.well-known/agent-card.json
- Envoie requête A2A: process_robot_alert(robot_id, error_code, ...)
- Reçoit réponse contenant la solution
```

### 5. Exécution Solution
```
main_agent:
- Reçoit solution de remote_support
- Appelle execute_solution tool
- Action agent exécute l'action
- Vérifie résultat
```

---

## 📊 Différences HTTP vs A2A

| Aspect | Ancien (HTTP) | Nouveau (A2A) |
|--------|---------------|---------------|
| **Communication** | `httpx.post()` manuel | `RemoteA2aAgent` automatique |
| **Protocole** | HTTP/REST custom | A2A standard Google |
| **Découverte** | URL hardcodée | Agent card `.well-known/` |
| **Intégration** | Code custom | Native ADK Runner |
| **Bidirectionnel** | Polling manuel | Automatique via Runner |
| **Type Safety** | JSON manual | Tools typés |

---

## 🐛 Troubleshooting

### Erreur: "RemoteA2aAgent cannot connect"
**Solution:** Vérifier que Alert Receiver A2A est démarré sur port 8000
```bash
curl http://localhost:8000/.well-known/agent-card.json
```

### Erreur: "Robot not responding"
**Solution:** Vérifier robot API
```bash
curl http://localhost:8001/health
```

### Logs utiles
```python
# Dans les deux serveurs, activer logging détaillé
logging.basicConfig(level=logging.DEBUG)
```

---

## 🔄 Migration depuis l'Ancienne Version

### Fichiers Obsolètes
- ❌ `embedded_robot/robot_agent.py` - SUPPRIMÉ (n'utilisait pas ADK)
- ❌ `embedded_robot/main.py` - Remplacé par `main_a2a.py`

### Nouveaux Fichiers
- ✅ `agents/alert_receiver/alert_receiver_a2a.py` - Serveur A2A
- ✅ `embedded_robot/main_a2a.py` - Robot client A2A
- ✅ `embedded_robot/simulator_console.py` - Console interactive

---

## 📝 Notes Importantes

1. **MessageBus Integration**: Pour l'instant, `alert_receiver_a2a.py` a une référence au MessageBus mais ne l'utilise pas encore pleinement. Il faudra intégrer:
   - Publication vers COO via MessageBus
   - Réception de solutions depuis Tech Support

2. **Testing**: Les fichiers sont créés mais nécessitent tests avec le système complet (COO + Tech Support)

3. **Hardware Simulator**: Les sub-agents ADK (`sensor_agents.py`, `diagnostic_agent.py`, `action_agent.py`) doivent exister dans `embedded_robot/adk_agents/`

---

## 🎯 Prochaines Étapes

- [ ] Tester le flow complet end-to-end
- [ ] Intégrer MessageBus dans alert_receiver_a2a
- [ ] Adapter COO Agent pour recevoir alertes A2A
- [ ] Tests automatisés

---

**Développé avec Google ADK A2A Protocol** 🚀
