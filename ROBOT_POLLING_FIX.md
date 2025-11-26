# Instructions pour ajouter le polling de solutions dans robot_agent.py

## Problème
Le robot envoie des alertes et elles sont traitées, mais il ne récupère jamais les solutions car il n'y a pas de boucle de polling.

## Solution : Ajouter une tâche de polling dans le simulateur

### Étape 1 : Trouver la méthode `InteractiveSimulator.run()` (ligne ~379)

### Étape 2 : Après la ligne 386 qui crée `diagnostics_task`, ajouter :

```python
# Start solution polling in background
async def poll_for_solutions():
    """Poll for solutions every 3 seconds"""
    while True:
        try:
            from embedded_robot.mcp_http_client import poll_solution_http
            solution = await poll_solution_http(self.robot.robot_id)
            
            if solution:
                print(f"\n💡 Solution received: {solution.get('action')}")
                await self.robot.execute_solution(solution)
        except Exception as e:
            # Silently continue on errors
            pass
        
        await asyncio.sleep(3)  # Poll every 3 seconds

polling_task = asyncio.create_task(poll_for_solutions())
```

### Étape 3 : Modifier la section `finally` (ligne ~452) pour arrêter polling_task

Remplacer :
```python
finally:
    self.robot.diagnostics_running = False
    diagnostics_task.cancel()
    try:
        await diagnostics_task
    except asyncio.CancelledError:
        pass
```

Par :
```python
finally:
    self.robot.diagnostics_running = False
    diagnostics_task.cancel()
    polling_task.cancel()
    try:
        await diagnostics_task
    except asyncio.CancelledError:
        pass
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
```

## Résultat Attendu

Après cette modification, le robot va automatiquement :
1. ✅ Envoyer des alertes quand vous tapez `1` ou `2`
2. ✅ Poller pour des solutions toutes les 3 secondes
3. ✅ Exécuter automatiquement les solutions reçues
4. ✅ Afficher "💡 Solution received: clean_wheels" dans la console
