# ⚠️ ÉTAT ACTUEL DU SYSTÈME - Session 28/11/2025

## 🔴 PROBLÈME ACTUEL

Le fichier `main_a2a.py` a été **corrompu** lors des dernières modifications. La méthode `_create_main_agent()` est incomplète (manque le début avec instruction, model, name, etc.).

## ✅ CE QUI FONCTIONNE

1. **`alert_receiver_a2a.py`** ✅ COMPLET
   - Serveur A2A avec `to_a2a()`
   - Forçage JSON avec `response_mime_type="application/json"`
   - Instructions claires pour retourner JSON structuré
   - Format: `{"actions": [...], "requires_hitl": bool, ...}`

2. **Logique ré-escalation** ✅ IMPLÉMENTÉE (mais fichier corrompu)
   - Tracking échecs par erreur
   - Ré-escalation 1er échec → nouvelles actions
   - Ré-escalation 2ème échec → HITL mandatory
   - Mode HITL sans ré-escalation

3. **Console Simulator** ✅ FONCTIONNE
   - `simulator_console.py` opérationnel

## ❌ PROBLÈME IDENTIFIÉ

**Symptôme:** Robot ne contacte pas Alert Receiver via A2A

**Cause:** L'instruction de l'agent principal n'est pas assez directive. L'agent "planifie" mais n'utilise pas le sub-agent `alert_receiver`.

**Exemple de log:**
```
📊 ADK A2A Result: Okay, I will handle the wheel blockage error (E01). 
First, I need to get the current sensor readings...
```
→ L'agent **planifie** au lieu d'**exécuter**

## 🛠️ SOLUTION À APPLIQUER

### Fichier: `main_a2a.py`

Le fichier est actuellement cor rompu. Il faut **restaurer** puis appliquer cette instruction **SIMPLE et DIRECTIVE** :

```python
def _create_main_agent(self) -> LlmAgent:
    """Create main orchestrator agent with A2A support"""
    return LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_options=self.retry_config),
        name="robot_orchestrator",
        description="Robot orchestrator with A2A support",
        instruction=f"""
You are robot {self.robot_id}.

When you receive an error message:
1. IMMEDIATELY use the alert_receiver sub-agent
2. Send error details to alert_receiver
3. Get JSON response from alert_receiver
4. Call execute_solution_structured with that response

DO NOT plan, just DO IT NOW.

Example:
Error: E01
→ Contact alert_receiver immediately
→ Get: {{"actions": ["clean_wheels"], "requires_hitl": false, ...}}
→ Call: execute_solution_structured(response)
        """,
        tools=[
            FunctionTool(self.execute_solution_structured),
            FunctionTool(self.get_robot_status)
        ],
        sub_agents=[
            self.remote_support_agent  # Only this one for now
        ]
    )
```

**Points clés:**
- Instruction TRÈS courte et directive
- "IMMEDIATELY", "DO IT NOW" pour forcer l'action
- Exemple concret dans l'instruction
- **Un seul sub-agent** (remote_support) pour éviter confusion
- **Moins de tools** pour forcer l'utilisation du sub-agent

## 📋 ÉTAPES DE RÉPARATION (Pour Demain)

### 1. Restaurer `main_a2a.py`

```powershell
# Option A: Git restore (si dans un repo)
git checkout -- "d:\PROGRAMME PYTHON\robonest-system\embedded_robot\main_a2a.py"

# Option B: Copie de sauvegarde
# Si vous avez une sauvegarde de main.py (version HTTP), adapter depuis là

# Option C: Réutiliser main.py et ajouter juste A2A
cp main.py main_a2a.py
# Puis ajouter RemoteA2aAgent
```

### 2. Appliquer Instruction Simple

Remplacer UNIQUEMENT la méthode `_create_main_agent()` avec la version ultra-simplifiée ci-dessus.

### 3. Tester

```powershell
# Terminal 1
cd "agents/alert_receiver"
python alert_receiver_a2a.py

# Terminal 2
cd "embedded_robot"
python main_a2a.py

# Terminal 3
cd "embedded_robot"
python simulator_console.py
# Tapez: 1 (E01)
```

**Résultat attendu:**
```
Robot logs:
- httpx - INFO - HTTP Request: GET http://localhost:8000/.well-known/agent-card.json
- Successfully resolved remote A2A agent: alert_receiver
- httpx - INFO - HTTP Request: POST http://localhost:8000 "HTTP/1.1 200 OK"
```

Alert Receiver logs:
```
- 🚨 Processing alert from XR25-001: E01
- Retourne JSON avec actions
```

## 🔑 ASTUCE PRINCIPALE

**Le problème n'est PAS le code A2A** (qui fonctionne).  
**Le problème est que Gemini ne suit pas l'instruction** quand elle est trop longue/complexe.

**Solution:** Instruction ≤ 10 lignes, TRÈS directive, avec ordres impératifs.

---

## 📝 FICHIERS DE RÉFÉRENCE

- ✅ `alert_receiver_a2a.py` - **BON ÉTAT**
- ⚠️ `main_a2a.py` - **CORROMPU - À RESTAURER**
- ✅ ` simulator_console.py` - **BON ÉTAT**
- ✅ `TEST_FINAL_A2A.md` - **Guide complet**

---

## 💡 ALTERNATIVE RAPIDE (Si restauration difficile)

Plutôt que réparer main_a2a.py, créer **`simple_robot_a2a.py`** minimal:

```python
# Version MINIMALISTE juste pour tester A2A
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner

# Créer remote agent
support = RemoteA2aAgent(
    name="alert_receiver",
    agent_card="http://localhost:8000/.well-known/agent-card.json"
)

# Créer agent simple
robot = LlmAgent(
    model=Gemini(model="gemini-2.0-flash-lite"),
    name="robot",
    instruction="Contact alert_receiver sub-agent for error E01",
    sub_agents=[support]
)

# Run
runner = Runner(robot)
async for event in runner.run_async("XR25-001", "test", "Error E01 detected"):
    print(event)
```

Ceci permettrait de **valider que A2A fonctionne** avant de tout réintégrer.

---

**Session à reprendre avec fichier `main_a2a.py` restauré** 🔧
