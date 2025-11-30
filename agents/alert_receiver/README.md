# 📡 Alert Receiver - A2A Server

Serveur A2A (Agent-to-Agent) qui reçoit les alertes des robots et retourne des solutions structurées en JSON.

## 📋 Vue d'Ensemble

L'Alert Receiver est un agent ADK exposé via protocole A2A. Il :
- Reçoit des alertes de robots via A2A
- Analyse avec RAG (base de connaissances)
- Classifie la priorité
- Retourne des solutions structurées JSON
- Gère la logique HITL (Human-in-the-Loop)

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│ LlmAgent (alert_receiver)            │
│  - Gemini 2.0 Flash Lite             │
│  - Response mode: JSON forcé         │
└──────────┬───────────────────────────┘
           │
           ├─ Tools:
           │   ├─ query_error_code (RAG)
           │   ├─ classify_error
           │   ├─ process_robot_alert
           │   ├─ provide_solution
           │   └─ get_alert_stats
           │
           └─ Exposed via: to_a2a(agent, port=8000)
```

## 🚀 Démarrage

### Prérequis
```bash
pip install google-adk python-dotenv
```

### Configuration
```bash
# Fichier .env à la racine
GOOGLE_API_KEY=your_api_key_here
```

### Lancement
```bash
# Méthode 1: Direct
python alert_receiver_a2a.py

# Méthode 2: Via launcher système
cd ../..
python start_system.py
```

Serveur démarre sur **http://localhost:8000**

## 🌐 Endpoints A2A

### Agent Card (Auto-exposé)
```bash
curl http://localhost:8000/.well-known/agent-card.json
```

Retourne la carte d'identité de l'agent avec capabilities.

### A2A Endpoint (POST /)
```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"message": "Robot XR25-001 has error E01: wheels blocked"}'
```

## 📤 Format de Réponse

### Structure JSON
```json
{
  "actions": ["action1", "action2", "..."],
  "requires_hitl": true/false,
  "is_temporary_solution": true/false,
  "ticket_id": "ALERT-ROBOTID-TIMESTAMP",
  "error_code": "E01"
}
```

### Exemples

#### E01 - Normal
```json
{
  "actions": ["clean_wheels", "recalibrate_motors"],
  "requires_hitl": false,
  "is_temporary_solution": false,
  "ticket_id": "ALERT-XR25-001-1701234567",
  "error_code": "E01"
}
```

#### E07 - Critique (HITL)
```json
{
  "actions": ["cooldown", "power_down"],
  "requires_hitl": true,
  "is_temporary_solution": true,
  "ticket_id": "ALERT-XR25-001-1701234568",
  "error_code": "E07"
}
```

#### 2ème Échec → HITL Forcé
```json
{
  "actions": ["manual_inspection"],
  "requires_hitl": true,
  "is_temporary_solution": true,
  "ticket_id": "ALERT-XR25-001-1701234569",
  "error_code": "E01"
}
```

## 🧠 Logique de Décision

### Classification Erreurs

| Code | Description | Priorité | HITL Immédiat |
|------|-------------|----------|---------------|
| E01 | Roues bloquées | Haute | Non |
| E02 | Navigation échec | Haute | Non |
| E03 | Batterie faible | Moyenne | Non |
| E04 | Bug logiciel | Moyenne | Non |
| E05 | Performance | Basse | Non |
| E07 | Batterie critique | **Critique** | **Oui** |
| E08 | Firmware corrompu | **Critique** | **Oui** |
| E09 | Capteur sécurité | **Critique** | **Oui** |

### Logique Ré-escalation

```
Message → Détection type

Si "ESCALATION ALERT" (1er échec):
  → Proposer actions DIFFÉRENTES
  → requires_hitl = false (sauf si critique)

Si "CRITICAL ESCALATION" (2ème échec):
  → requires_hitl = true (FORCÉ)
  → is_temporary_solution = true
  → Actions de sécurité uniquement
```

## 🔧 Outils (Tools)

### query_error_code
```python
query_error_code(error_code: str, robot_model: str) -> str
```
Recherche dans RAG pour obtenir contexte erreur.

### classify_error
```python
classify_error(error_code: str, description: str) -> dict
```
Classifie priorité et détermine si HITL requis.

### process_robot_alert
```python
process_robot_alert(
    robot_id: str,
    error_code: str,
    severity: str,
    description: str,
    location: Optional[Dict]
) -> dict
```
Traite l'alerte, crée ticket, forward COO si HITL.

### provide_solution
```python
provide_solution(
    ticket_id: str,
    solution_type: str,
    actions: List[str],
    details: Optional[Dict]
) -> dict
```
Retourne solution structurée avec métadonnées.

## 📊 Patterns Google ADK Utilisés

- **LlmAgent** avec Gemini 2.0  Flash
- **to_a2a()** pour exposition serveur
- **FunctionTool** pour outils RAG
- **GenerateContentConfig** avec `response_mime_type="application/json"`
- **HttpRetryOptions** pour résilience
- **Agent Card** auto-généré

## 📁 Structure

```
agents/alert_receiver/
├── alert_receiver_a2a.py    # Serveur A2A principal
├── rag_tool.py               # Outil RAG (base connaissances)
├── knowledge_base/           # Docs erreurs/solutions
│   ├── error_codes.md
│   └── troubleshooting.md
└── README.md                 # Ce fichier
```

## 🐛 Troubleshooting

### Serveur ne démarre pas
- Vérifier port 8000 libre: `netstat -ano | findstr :8000`
- Vérifier `GOOGLE_API_KEY` configuré
- Vérifier dépendances: `pip install google-adk`

### Agent Card non accessible
- Vérifier URL: `http://localhost:8000/.well-known/agent-card.json`
- Vérifier que `to_a2a()` a bien exposé l'agent
- Logs doivent afficher: `✅ Alert Receiver A2A Server created on port 8000`

### JSON invalide retourné
- Vérifier que `response_mime_type="application/json"` est activé
- Vérifier instruction agent contient format JSON exact
- Tester manuellement avec curl

### RAG ne fonctionne pas
- Vérifier que `knowledge_base/` contient des fichiers .md
- Logs doivent afficher: `📚 Loading knowledge base`
- Tester query directe: `rag_tool.query_knowledge_base("E01")`

## 🔐 Sécurité & Production

### Pour Production
1. Ajouter authentification A2A
2. Rate limiting sur endpoints
3. Validation stricte des inputs
4. Logging centralisé
5. Monitoring métriques

### Variables d'Environnement
```bash
GOOGLE_API_KEY=xxx         # Required
ALERT_RECEIVER_PORT=8000   # Optional (default: 8000)
LOG_LEVEL=INFO             # Optional (default: INFO)
```

## 📚 Documentation Complémentaire

- [Embedded Robot README](../../embedded_robot/README.md)
- [Guide Lancement A2A](../../GUIDE_LANCEMENT_A2A.md)
- [Succès A2A](../../SUCCES_A2A_FINAL.md)

## 🎯 Test Rapide

```bash
# Terminal 1: Lancer serveur
python alert_receiver_a2a.py

# Terminal 2: Tester agent card
curl http://localhost:8000/.well-known/agent-card.json

# Terminal 3: Envoyer alerte test
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Robot XR25-001 error E01: wheels blocked. Battery: 85%, Temp: 35°C"
  }'
```

Réponse attendue : JSON avec `actions`, `requires_hitl`, etc.

---

**Développé avec Google ADK - Serveur A2A Production-Ready**
