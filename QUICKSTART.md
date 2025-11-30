# 🚀 RoboNest - Quick Start Guide

## Architecture

Le système RoboNest est composé de 3 parties distinctes:

```
┌─────────────────────────────────────────┐
│  INFRASTRUCTURE PRINCIPALE              │
│  - Alert Receiver (A2A Server)          │
│  - COO Agent (Coordinateur)             │
│  - Message Bus                          │
└─────────────────────────────────────────┘
              ↕ A2A Protocol
┌─────────────────────────────────────────┐
│  ROBOT EMBARQUÉ                         │
│  - Agents capteurs                      │
│  - Agent diagnostic                     │
│  - Support workflow (A2A client)        │
└─────────────────────────────────────────┘
              ↕ Simulation
┌─────────────────────────────────────────┐
│  CONSOLE SIMULATEUR                     │
│  - CLI interactive                      │
│  - Simulation erreurs                   │
│  - Intervention HITL                    │
└─────────────────────────────────────────┘
```

## Lancement du Système

### Option 1: Lancement Séparé (Recommandé pour Debug)

**Terminal 1 - Infrastructure Principale:**
```bash
python start_system.py
```
Ceci lance:
- Alert Receiver (port 8000)
- COO Agent
- Message Bus

**Terminal 2 - Robot:**
```bash
python start_robot.py
```
Lance le robot embarqué (port 8001)

**Terminal 3 - Simulateur:**
```bash
python start_simulator.py
```
Lance la console interactive de test

**Avantages:**
- ✅ Logs séparés et lisibles
- ✅ Debug facile par composant
- ✅ Peut redémarrer un composant sans affecter les autres

### Option 2: Lancement Manuel

```bash
# Terminal 1
cd agents/alert_receiver
python alert_receiver_a2a.py

# Terminal 2
cd agents
python main.py

# Terminal 3
cd embedded_robot
python main_a2a.py

# Terminal 4
cd embedded_robot
python simulator_console.py
```

## Vérification

Une fois lancé, vérifier:

```bash
# Agent Card disponible
curl http://localhost:8000/.well-known/agent-card.json

# Status robot
curl http://localhost:8001/status
```

## Tests Rapides

Dans le simulateur (Terminal 3):

```
1  # Simule E01 (roues bloquées) - ré-escalation
3  # Simule E07 (batterie critique) - HITL immédiat
s  # Affiche statut complet
h  # HITL: débloquer roues
b  # HITL: refroidir batterie
```

## Arrêt du Système

1. CTRL+C dans le simulateur (Terminal 3)
2. CTRL+C dans le robot (Terminal 2)
3. CTRL+C dans l'infrastructure (Terminal 1)

## Troubleshooting

**"Connection refused" sur port 8000:**
- L'infrastructure principale n'est pas lancée
- Lancer `start_system.py` d'abord

**"Robot not responding":**
- Le robot n'est pas lancé
- Lancer `start_robot.py`

**Logs mélangés:**
- Assurez-vous d'utiliser des terminaux séparés
- Ne pas lancer tout depuis `start_system.py`

---

Pour documentation complète, voir:
- `README.md` - Documentation système complète
- `embedded_robot/README.md` - Documentation robot
- `agents/alert_receiver/README.md` - Documentation Alert Receiver
