# 📋 PLAN DE FINALISATION - Système RoboNest A2A

## ✅ État Actuel

### Fonctionnel
- ✅ Communication A2A complète (robot ↔ alert_receiver)
- ✅ Exécution automatique solutions (Sequential Agent)
- ✅ Ré-escalation jusqu'à 3 tentatives (Loop Agent)
- ✅ HITL immédiat pour erreurs critiques (E07)
- ✅ HITL après échecs multiples
- ✅ Console interactive de test

### Manquant
- ❌ Notifications Gmail/Jira pour HITL
- ❌ Actions validées dans hardware_simulator
- ❌ Documentation utilisateur complète
- ❌ Script de démarrage automatique

---

## 📝 PLAN D'ACTION DÉTAILLÉ

### ÉTAPE 1: Actions Valides (30 min)

#### Option A: Liste d'actions dans RAG (RECOMMANDÉ)
**Avantages:**
- Flexible et évolutif
- Peut inclure contexte d'usage
- Permet de documenter chaque action
- L'agent apprend du contexte

**Implémentation:**
1. Créer fichier `knowledge_base/robot_actions.md`
2. Documenter toutes les actions possibles avec descriptions
3. L'agent Alert Receiver query le RAG pour connaître les actions

**Contenu:**
```markdown
# Actions Robot Disponibles

## E01 - Wheels Blocked
- clean_wheels: Nettoie les roues (résout obstruction légère)
- lubricate_wheels: Lubrifie mécanisme (résout friction)
- reverse_motors: Inverse moteurs pour dégager (résout blocage mécanique)
- manual_check: Inspection visuelle requise (HITL)

## E03 - Battery
- charge_battery: Lance recharge complète
- optimize_power: Réduit consommation

## E07 - Critical
- cooldown: Refroidissement d'urgence
- power_down: Arrêt sécurisé
- emergency_shutdown: Arrêt immédiat
```

#### Option B: Liste dans instructions agent
**Pour:** Simple et rapide
**Contre:** Moins flexible, instructions trop longues

**Verdict:** ✅ **Option A (RAG)** pour production réelle, mais pour la démo on peut garder l'approche actuelle (qui simule des actions pas toujours valides - c'est parfait pour tester la ré-escalation!)

---

### ÉTAPE 2: Scénarios de Démo Finaux (1h)

#### Scénario 1: HITL Immédiat ✅ (Déjà fonctionnel)
```
Console: 3 (E07 - Batterie critique)
→ Alert Receiver détecte E07
→ requires_hitl=true immédiatement
→ Robot exécute pré-solutions (cooldown)
→ waiting_for_hitl=True
→ Pas de ré-escalation
Console: b (HITL - refroidir)
→ E07 résolu
```

#### Scénario 2: HITL après 3 Échecs ✅ (Déjà fonctionnel)
```
Console: 1 (E01)
→ Tentative 1: Actions proposées mais échouent
→ Tentative 2: Nouvelles actions, échouent aussi
→ Tentative 3: HITL forcé (requires_hitl=true)
→ Robot waiting_for_hitl=True
Console: h (HITL - débloquer)
→ E01 résolu
```

**Ce qu'il faut :** 
- [x] HITL immédiat (E07) → Fonctionne déjà
- [x] HITL après échecs → Fonctionne déjà
- [ ] **Ajuster alert_receiver instructions** pour garantir que tentatives 1 et 2 proposent vraiment des actions DIFFÉRENTES

---

### ÉTAPE 3: Notifications Gmail + Jira pour HITL (2h)

**Statut:** ❌ Pas encore implémenté

**Localisation:** `agents/alert_receiver/alert_receiver_a2a.py`

**Implémentation:**

#### 3.1 Fonction `send_hitl_notification`
```python
def send_hitl_notification(
    ticket_id: str,
    error_code: str,
    robot_id: str,
    severity: str,
    description: str
) -> dict:
    """
    Send HITL notification via Gmail + Create Jira ticket
    
    Returns:
        {
            "email_sent": bool,
            "jira_ticket": str,
            "notifications": []
        }
    """
    notifications = []
    
    # 1. Gmail notification
    if alert_state.gmail_enabled:
        email_result = alert_state.gmail_notifier.send_critical_alert(
            to="support@robonest.com",
            subject=f"🚨 HITL Required: {robot_id} - {error_code}",
            body=f"""
            Robot: {robot_id}
            Error: {error_code}
            Severity: {severity}
            
            {description}
            
            Ticket: {ticket_id}
            Action: Human intervention required immediately
            """
        )
        notifications.append({"type": "email", "status": email_result})
    
    # 2. Jira ticket
    if alert_state.jira_enabled:
        jira_ticket = alert_state.jira_client.create_ticket(
            project="ROBOT",
            summary=f"HITL: {robot_id} - {error_code}",
            description=description,
            priority="Critical" if severity == "critical" else "High",
            labels=["HITL", "robot", error_code]
        )
        notifications.append({"type": "jira", "ticket": jira_ticket})
    
    return {
        "email_sent": any(n["type"] == "email" for n in notifications),
        "jira_ticket": next((n["ticket"] for n in notifications if n["type"] == "jira"), None),
        "notifications": notifications
    }
```

#### 3.2 Appeler dans `process_robot_alert`
```python
# Si HITL détecté
if requires_hitl:
    notification_result = send_hitl_notification(
        ticket_id=ticket_id,
        error_code=error_code,
        robot_id=robot_id,
        severity=priority,
        description=description
    )
    logger.info(f"📧 HITL notifications sent: {notification_result}")
```

**Note:** Pour la démo, on peut **simuler** les notifications (pas besoin de vraie config Gmail/Jira):
```python
def send_hitl_notification_demo(ticket_id, error_code, robot_id):
    """Demo version - just logs"""
    logger.warning(f"📧 [DEMO] Email sent to: support@robonest.com")
    logger.warning(f"🎫 [DEMO] Jira ticket created: ROBOT-{ticket_id}")
    return {"demo": True, "email_sent": True, "jira_ticket": f"ROBOT-{ticket_id}"}
```

---

### ÉTAPE 4: Documentation (1h30)

#### 4.1 `embedded_robot/README.md`
```markdown
# 🤖 Embedded Robot - A2A Version

Robot embarqué avec support Google ADK A2A pour communication avec système de support distant.

## Architecture
- **Main Agent**: Orchestrateur principal
- **Support Workflow**: Sequential + Loop pour escalation automatique
- **Hardware Simulator**: Simulation capteurs et actionneurs
- **A2A Client**: Communication avec Alert Receiver

## Démarrage
```bash
python main_a2a.py
```

## Test
```bash
python simulator_console.py
```

## Patterns ADK Utilisés
- LlmAgent
- RemoteA2aAgent
- SequentialAgent
- LoopAgent
- FunctionTool
```

#### 4.2 `agents/alert_receiver/README.md`
```markdown
# 📡 Alert Receiver - A2A Server

Serveur A2A qui reçoit alertes robots et retourne solutions structurées.

## Architecture
- **LlmAgent**: Agent principal avec RAG
- **A2A Server**: Exposé via `to_a2a()`
- **RAG Tool**: Base de connaissances erreurs

## Démarrage
```bash
python alert_receiver_a2a.py
```

## Endpoints
- Agent Card: `http://localhost:8000/.well-known/agent-card.json`
- A2A: `POST http://localhost:8000`

## Response Format
```json
{
  "actions": ["action1", "action2"],
  "requires_hitl": false,
  "is_temporary_solution": false,
  "ticket_id": "ALERT-XXX",
  "error_code": "E01"
}
```
```

#### 4.3 `start_system.py` (Script de démarrage)
```python
"""
RoboNest System Launcher
Lance Alert Receiver + Robot + Console dans des processus séparés
"""
import subprocess
import sys
import time
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 ROBONEST A2A SYSTEM - LAUNCHER")
    print("=" * 60)
    
    # 1. Alert Receiver
    print("\n📡 Starting Alert Receiver (port 8000)...")
    alert_receiver = subprocess.Popen(
        [sys.executable, "agents/alert_receiver/alert_receiver_a2a.py"],
        cwd=Path(__file__).parent
    )
    time.sleep(3)
    
    # 2. Robot
    print("\n🤖 Starting Robot (port 8001)...")
    robot = subprocess.Popen(
        [sys.executable, "embedded_robot/main_a2a.py"],
        cwd=Path(__file__).parent
    )
    time.sleep(3)
    
    # 3. Console
    print("\n🎮 Starting Test Console...")
    print("\n" + "=" * 60)
    print("✅ ALL SYSTEMS RUNNING")
    print("=" * 60)
    print("\nAlert Receiver: http://localhost:8000")
    print("Robot API: http://localhost:8001")
    print("\nPress CTRL+C to stop all services")
    print("=" * 60 + "\n")
    
    try:
        subprocess.run(
            [sys.executable, "embedded_robot/simulator_console.py"],
            cwd=Path(__file__).parent
        )
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 Shutting down...")
        alert_receiver.terminate()
        robot.terminate()
        print("✅ All services stopped\n")

if __name__ == "__main__":
    main()
```

---

### ÉTAPE 5: README Principal (30 min)

#### `README.md` (racine projet)
```markdown
# 🤖 RoboNest - Multi-Agent Robot Support System

Système de support multi-agents pour robots utilisant Google ADK et protocole A2A.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "GOOGLE_API_KEY=your_key" > .env

# Start system
python start_system.py
```

## Architecture

```
┌─────────────────┐         A2A          ┌──────────────────┐
│ Embedded Robot  │ ◄──────────────────► │ Alert Receiver   │
│  (port 8001)    │   Solutions JSON     │  (port 8000)     │
└─────────────────┘                      └──────────────────┘
        │                                         │
        │                                    ┌────┴────┐
        ▼                                    │   RAG   │
┌─────────────────┐                         │  Tool   │
│ Test Console    │                         └─────────┘
└─────────────────┘
```

## Demos

### Test 1: HITL Immédiat (E07)
1. `Console: 3` → Batterie critique
2. System sends HITL alert
3. `Console: b` → Human fixes

### Test 2: HITL après Échecs
1. `Console: 1` → E01
2. System tries 3 times
3. After 3 failures → HITL
4. `Console: h` → Human fixes

## Documentation
- [Embedded Robot](embedded_robot/README.md)
- [Alert Receiver](agents/alert_receiver/README.md)
- [System Success Report](SUCCES_A2A_FINAL.md)
```

---

## 📊 RÉSUMÉ PLAN

### Priorités

| Tâche | Temps | Priorité | Statut |
|-------|-------|----------|--------|
| 1. Actions dans RAG | 30 min | Moyenne | 📝 À faire |
| 2. Scénarios démo finaux | 1h | Haute | ✅ Déjà OK (ajuster instructions) |
| 3. Notifications HITL | 2h | Moyenne | 📝 À faire (version démo simple) |
| 4. Documentation complète | 1h30 | **Haute** | 📝 À faire |
| 5. `start_system.py` | 30 min | **Haute** | 📝 À faire |

**Total estimé: 5h30**

### Ordre Recommandé

1. **start_system.py** (30 min) → Permet de tester facilement
2. **READMEs** (1h30) → Documentation essentielle
3. **Notifications HITL démo** (1h) → Version simple qui log
4. **Ajuster instructions alert_receiver** (30 min) → Garantir 3 actions différentes
5. **Actions RAG** (optionnel, post-démo)

---

## 🎯 POUR DÉMO FINALE

### Ce qui fonctionne PARFAITEMENT
- ✅ A2A end-to-end
- ✅ Exécution automatique
- ✅ Ré-escalation intelligente
- ✅ 2 scénarios HITL

### Ce qu'on ajoute (minimal viable)
1. ✅ `start_system.py` → Lancement une commande
2. ✅ READMEs → Documentation claire
3. ✅ Logs HITL notifications → `logger.warning("📧 Email sent to support")`

### Démo Script
```
1. python start_system.py
2. Test E07 (HITL immédiat)
3. Test E01 (3 échecs → HITL)
4. Montrer les logs A2A
5. Montrer architecture avec diagrammes
```

---

**Voulez-vous que je commence par quelle étape ?**

Recommandation : **Commençons par `start_system.py` + READMEs** car ça rendra le système immédiatement démontrable et professionnel. 🚀
