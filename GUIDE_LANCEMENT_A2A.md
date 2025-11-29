# 🚀 GUIDE DE LANCEMENT - Système RoboNest A2A

## ✅ Vérifications Pré-Lancement

### 1. Fichiers Vérifiés
- ✅ `embedded_robot/adk_agents/` existe avec tous les sub-agents :
  - `sensor_agents.py`
  - `diagnostic_agent.py`  
  - `action_agent.py`
  - `hardware_simulator.py`
- ✅ `alert_receiver_a2a.py` - Serveur A2A
- ✅ `main_a2a.py` - Robot client A2A
- ✅ `simulator_console.py` - Console interactive

### 2. Imports Google ADK
- ✅ `google.adk.agents.LlmAgent`
- ✅ `google.adk.agents.remote_a2a_agent.RemoteA2aAgent`
- ✅ `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- ✅ `google.adk.models.google_llm.Gemini`
- ✅ Tous les imports présents et corrects

---

## 📦 Installation des Dépendances

```bash
pip install google-adk google-generativeai fastapi uvicorn httpx pydantic
```

**Vérifier installation :**
```bash
python -c "import google.adk; print('✅ Google ADK installed')"
python -c "from google.adk.agents.remote_a2a_agent import RemoteA2aAgent; print('✅ RemoteA2aAgent available')"
python -c "from google.adk.a2a.utils.agent_to_a2a import to_a2a; print('✅ to_a2a available')"
```

---

## 🎯 Lancement du Système Complet

### 📌 Prérequis
Assurez-vous que le fichier `.env` contient :
```bash
GOOGLE_API_KEY=votre_clé_gemini
```

---

### 🔴 Option 1: Test A2A Simple (Sans COO/Tech Support)

Cette option teste uniquement la communication A2A entre Robot et Alert Receiver.

#### Terminal 1 : Alert Receiver A2A (Port 8000)
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\agents\alert_receiver"
python alert_receiver_a2a.py
```

**Résultat attendu :**
```
==============================================================
🤖 ALERT RECEIVER AGENT - A2A SERVER
==============================================================

Starting server on port 8000...
Agent card: http://localhost:8000/.well-known/agent-card.json
==============================================================

INFO:     Started server process
INFO:     Waiting for application startup.
✅ Alert Receiver State initialized
✅ Alert Receiver Agent created
✅ Alert Receiver A2A Server created on port 8000
   Agent card will be available at: /.well-known/agent-card.json
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Vérifier Agent Card:**
```bash
curl http://localhost:8000/.well-known/agent-card.json
```

#### Terminal 2 : Robot A2A (Port 8001)
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python main_a2a.py
```

**Résultat attendu :**
```
==============================================================
🤖 EMBEDDED ROBOT API - A2A PROTOCOL
==============================================================

Robot: http://localhost:8001
API Docs: http://localhost:8001/docs
Support System: http://localhost:8000

==============================================================

INFO:     Started server process
✅ Robot State initialized with A2A: XR25-001
   Support system: http://localhost:8000
🔍 ADK Diagnostics started with A2A support
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### Terminal 3 : Console Interactive
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python simulator_console.py
```

**Résultat attendu :**
```
==============================================================
      🤖 ROBONEST ROBOT SIMULATOR - A2A VERSION
==============================================================

Checking robot connection...

==============================================================
🤖 Robot Status: XR25-001
==============================================================

  State: OPERATIONAL

  📊 Sensors:
     Battery: 85%
     Temperature: 35.0°C
     Wheels: ✅ OK

  📈 Metrics:
     Self-resolutions: 0
     Escalations: 0
     Failed solutions: 0
    Success rate: 0.0%
     Protocol: A2A

==============================================================

Available Commands:
  1 - Simulate E01 (Roues bloquées)
  2 - Simulate E03 (Batterie faible) 
  3 - Simulate E07 (Batterie critique - HITL)
  h - Intervention Humaine (HITL) - débloquer roues
  b - Intervention Humaine (HITL) - refroidir batterie
  s - Statut Robot
  q - Quit

Votre choix:
```

---

### 🟢 Option 2: Système Complet (Avec COO + Tech Support)

Pour tester le flow end-to-end avec tout le système :

#### Terminal 1 : Système Principal Complet
```bash
cd "d:\PROGRAMME PYTHON\robonest-system"
python start_system.py
```

Ceci démarre :
- MessageBus
- COO Agent (coordinateur)
- Alert Receiver Agent (ancien, via HTTP)
- Technical Support Agent

#### Terminal 2 : Robot A2A
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python main_a2a.py
```

#### Terminal 3 : Console Interactive
```bash
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python simulator_console.py
```

⚠️ **NOTE:** Pour le système complet, il faudra adapter `start_system.py` pour utiliser `alert_receiver_a2a.py` au lieu de l'ancien alert_receiver.

---

## 🎮 Scénarios de Test

### Scénario 1 : Escalation A2A Simple (E01)

1. **Dans Console** : Tapez `1` (Simuler E01 - Roues bloquées)

2. **Ce qui se passe :**
   ```
   Robot → Détecte E01 via diagnostics
        → main_agent analyse avec sub-agents
        → Recherche memory (vide)
        → Décide d'escalader
        → Utilise remote_support_agent (A2A!)
        → RemoteA2aAgent se connecte à /.well-known/agent-card.json
        → Appelle tool process_robot_alert via A2A
   
   Alert Receiver → Reçoit via A2A
                 → Log "🚨 Processing alert from XR25-001: E01"
                 → (Sans COO, solution manuelle pour l'instant)
   ```

3. **Vérifier logs Terminal 2 (Robot) :**
   ```
   ❌ Error detected: E01 - Wheels blocked
   🧠 ADK handling with A2A: E01
   ```

4. **Vérifier logs Terminal 1 (Alert Receiver) :**
   ```
   🚨 Processing alert from XR25-001: E01
   📤 Forwarding alert to COO: ALERT-XR25-001-xxxxx
   ```

### Scénario 2 : HITL Requis (E07)

1. **Dans Console** : Tapez `3` (Simuler E07 - Batterie critique)

2. **Robot détecte erreur critique** → Escalade avec HITL

3. **Dans Console** : Tapez `b` (Intervention humaine - refroidir)

4. **Vérifier que robot reprend** :
   ```
   ✅ HITL intervention completed, robot resuming normal operation
   ```

### Scénario 3 : Vérifier Statut

**Dans Console** : Tapez `s`

Affiche :
- État du robot
- Capteurs actuels
- Métriques (escalations, protocole A2A, etc.)

---

## 🔍 Endpoints de Test

### Alert Receiver (Port 8000)
```bash
# Agent Card A2A
curl http://localhost:8000/.well-known/agent-card.json

# Health (si implémenté)
curl http://localhost:8000/health
```

### Robot (Port 8001)
```bash
# Health Check
curl http://localhost:8001/health

# Status
curl http://localhost:8001/status

# Simuler E01 via API (alternative à console)
curl -X POST http://localhost:8001/simulate/error/E01

# HITL via API
curl -X POST http://localhost:8001/fix/clean_wheels
```

---

## ⚡ Démarrage Rapide (Copy-Paste)

Ouvrez 3 terminaux PowerShell et exécutez dans l'ordre :

**Terminal 1 :**
```powershell
cd "d:\PROGRAMME PYTHON\robonest-system\agents\alert_receiver"
python alert_receiver_a2a.py
```

**Terminal 2 :**
```powershell
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python main_a2a.py
```

**Terminal 3 :**
```powershell
cd "d:\PROGRAMME PYTHON\robonest-system\embedded_robot"
python simulator_console.py
```

---

## 🐛 Problèmes Connus et Solutions

### Erreur : "Module 'google.adk' not found"
**Solution :**
```bash
pip install --upgrade google-adk
```

### Erreur : "RemoteA2aAgent cannot connect to agent card"
**Solution :**
1. Vérifier Terminal 1 que Alert Receiver est démarré
2. Tester : `curl http://localhost:8000/.well-known/agent-card.json`
3. Vérifier qu'aucun firewall ne bloque le port 8000

### Erreur : "Address already in use (Port 8000 ou 8001)"
**Solution :**
```powershell
# Trouver process sur port
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# Tuer process
taskkill /PID <PID> /F
```

### Robot ne reçoit pas de solutions
**Cause :** Alert Receiver A2A seul ne génère pas de solutions automatiquement.

**Solution temporaire :** Pour test A2A simple, il faudra soit :
- Appeler manuellement `provide_solution` via API
- Ou lancer système complet avec COO + Tech Support

---

## 📊 Vérification du Succès

### ✅ Checklist Post-Lancement

- [ ] Terminal 1 : Alert Receiver démarré sur port 8000
- [ ] Agent card accessible : `http://localhost:8000/.well-known/agent-card.json`
- [ ] Terminal 2 : Robot démarré sur port 8001
- [ ] Robot log affiche : "Robot State initialized with A2A"
- [ ] Terminal 3 : Console affiche menu interactif
- [ ] Console peut récupérer statut robot (commande `s`)
- [ ] Simulation E01 (commande `1`) déclenche logs dans les 2 terminaux
- [ ] Logs Robot montrent "🧠 ADK handling with A2A"
- [ ] Logs Alert Receiver montrent "🚨 Processing alert"

---

## 🎯 Prochaines Étapes

Pour système production-ready :

1. **Adapter start_system.py** pour utiliser `alert_receiver_a2a.py`
2. **Intégrer MessageBus** dans alert_receiver_a2a pour publier vers COO
3. **COO reçoit alertes** et délègue à Tech Support
4. **Tech Support génère solutions** et renvoie via MessageBus
5. **Alert Receiver renvoie solution au robot via A2A response**
6. **Tests end-to-end** avec flow complet

---

**Système A2A prêt à tester ! 🚀**
