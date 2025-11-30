# QUICKSTART - RoboNest System

Guide de démarrage rapide pour lancer le système RoboNest avec architecture Message Bus.

## 🚀 Lancement Rapide (3 Terminaux)

### Terminal 1 - Système Principal
```bash
cd d:\PROGRAMME PYTHON\robonest-system
python agents/main.py
```

**Ce qui démarre:**
- ✅ Message Bus (instance unique partagée)
- ✅ Alert Receiver (A2A Server sur port 8000)
- ✅ COO Agent (Orchestrateur)
- ✅ Technical Support Agent (Résolveur)

**Logs attendus:**
```
🚀 ROBONEST - UNIFIED SYSTEM STARTUP
📦 Initializing shared infrastructure...
✅ Shared Message Bus created
🧠 Starting COO Agent...
✅ COO Agent operational
🔧 Starting Technical Support Agent...
✅ Technical Support Agent operational
📡 Creating Alert Receiver Agent...
✅ Alert Receiver Agent created
🌐 Exposing Alert Receiver via A2A...
✅ A2A Server configured on port 8000
✅ UNIFIED SYSTEM OPERATIONAL
```

---

### Terminal 2 - Robot Embarqué
```bash
python start_robot.py
```

**Ce qui démarre:**
- ✅ Robot embarqué avec A2A Client
- ✅ Connexion à Alert Receiver (localhost:8000)
- ✅ Simulation de capteurs et états

---

### Terminal 3 - Console Simulateur
```bash
python start_simulator.py
```

**Ce qui démarre:**
- ✅ Console interactive pour déclencher erreurs
- ✅ Options: E01-E09, escalations, HITL

---

## 🧪 Test Complet E01 (Roues Bloquées)

1. **Dans Terminal 3 (Simulateur):**
   ```
   Entrez le numéro du scénario: 1
   ```

2. **Logs attendus dans Terminal 1 (Système):**
   ```
   [Alert Receiver] 🚨 Processing alert from XR25-001: E01
   [Alert Receiver] 📤 Forwarding alert to COO
   [COO Agent] 📋 Nouvelle tâche: ALERT-XR25-001-xxx (robot_alert)
   [COO Agent] ✅ Agent assigné: technical_support
   [COO Agent] ✅ Tâche déléguée à tech_support_001
   [Technical Support] 📥 Received task
   [Technical Support] 🔧 Processing technical task
   [Technical Support] ✅ Task completed and published
   [COO Agent] 📤 Solution forwarded to Alert Receiver
   [Alert Receiver] 📥 Received solution from COO
   [Alert Receiver] ✅ Solution queued for XR25-001
   ```

3. **Logs attendus dans Terminal 2 (Robot):**
   ```
   🤖 Polling for solution...
   ✅ Solution received: {"actions": ["clean_wheels", "recalibrate_motors"], ...}
   🔄 Executing action: clean_wheels
   ✅ clean_wheels completed
   🔄 Executing action: recalibrate_motors
   ✅ recalibrate_motors completed
   ✅ All actions completed successfully
   ```

**Résultat:** ✅ Problème résolu automatiquement

---

## 🔥 Test HITL E07 (Batterie Critique)

1. **Dans Terminal 3 (Simulateur):**
   ```
   Entrez le numéro du scénario: 3
   ```

2. **Comportement attendu:**
   - Technical Support détecte `requires_hitl=true`
   - 📧 Email envoyé via Gmail (si configuré)
   - 🎫 Ticket Jira créé (si configuré)
   - Actions de sécurité retournées: `["cooldown", "power_down"]`

3. **Logs système:**
   ```
   [Technical Support] ⚠️ HITL required for E07
   [Technical Support] 📧 HITL email sent to support@...
   [Technical Support] 🎫 Jira ticket created: ROB-XXX
   ```

---

## ⚙️ Configuration

### Variables d'environnement (`.env`)

**Obligatoire:**
```env
GOOGLE_API_KEY=votre_clé_api_gemini
```

**Optionnel (pour HITL):**
```env
# Gmail
GMAIL_SENDER_EMAIL=robot-system@company.com
GMAIL_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx

# Jira
JIRA_SERVER=https://company.atlassian.net
JIRA_EMAIL=user@company.com
JIRA_API_TOKEN=votre_token_jira
JIRA_PROJECT_KEY=ROB

# Ports (optionnel)
ALERT_RECEIVER_PORT=8000
ROBOT_PORT=8001
```

**Copier exemple:**
```bash
cp .env.example .env
# Puis éditer .env avec vos clés
```

---

## 📊 Architecture

```
Robot (A2A Client)
    ↓ HTTP/A2A
Alert Receiver (A2A Server + LlmAgent)
    ↓ Message Bus: task.new
COO Agent (Orchestrateur)
    ↓ Message Bus: task.assigned.technical_support
Technical Support Agent (Résolveur)
    ├─ RAG (Knowledge Base)
    ├─ Gmail (HITL Notifications)
    └─ Jira (Ticket Creation)
    ↓ Message Bus: task.completed
COO Agent
    ↓ Message Bus: solution.for_robot
Alert Receiver
    ↓ A2A Response
Robot (Exécute actions)
```

**Détails:** Voir [docs/diagrams/message_bus_architecture.md](docs/diagrams/message_bus_architecture.md)

---

## 🐛 Troubleshooting

### Problème: "Connection refused" (Robot)
**Cause:** Alert Receiver n'est pas démarré  
**Solution:** Vérifier Terminal 1, s'assurer que "A2A Server configured on port 8000" est affiché

### Problème: "No solution received"
**Cause:** Message Bus ne connecte pas les agents  
**Solution:** Vérifier que tous les agents sont dans le MÊME processus (agents/main.py)

### Problème: "HITL notifications not sent"
**Cause:** Variables d'environnement Gmail/Jira manquantes  
**Solution:** Configurer `.env` avec credentials ou ignorer (système fonctionne sans)

### Problème: "Import error google.adk"
**Cause:** Dépendances manquantes  
**Solution:**
```bash
pip install google-adk google-generativeai
```

---

## 📚 Documentation Complète

- **Architecture:** [docs/architecture.md](docs/architecture.md)
- **Diagrammes:** [docs/diagrams/](docs/diagrams/)
- **RAG Knowledge Base:** [rag/knowledge_base/products/error_codes/README.md](rag/knowledge_base/products/error_codes/README.md)
- **API Documentation:** [docs/api_documentation.md](docs/api_documentation.md)

---

## ✅ Checklist Première Utilisation

- [ ] Cloner le projet
- [ ] Installer dépendances: `pip install -r requirements.txt`
- [ ] Créer `.env` avec `GOOGLE_API_KEY`
- [ ] Lancer Terminal 1: `python agents/main.py`
- [ ] Attendre "✅ UNIFIED SYSTEM OPERATIONAL"
- [ ] Lancer Terminal 2: `python start_robot.py`
- [ ] Lancer Terminal 3: `python start_simulator.py`
- [ ] Tester E01 (option 1 dans simulateur)
- [ ] Vérifier logs et exécution actions

---

**Système opérationnel ? Testez les autres scénarios E02-E09 !** 🎉
