# Error Codes Knowledge Base

## Overview

This directory contains the comprehensive error code database for the RoboNest A2A Multi-Agent System. The database documents all robot error codes with detailed information for automated support and troubleshooting.

## Files

- **`error_codes_database_english.json`** - English version of error codes database
- **`error_codes_database.json`** - French version of error codes database  

## Structure

Each error code entry contains:

```json
{
    "code": "E01",
    "description": "Brief description of the error",
    "causes": ["List", "of", "possible", "causes"],
    "resolution": "General resolution approach",
    "actions": ["automated_action_1", "automated_action_2"],
    "urgency": "low|medium|high|critical",
    "requires_hitl": true|false,
    "safety_warning": "Optional safety warning for critical errors",
    "models": ["XR25", "XR30"]
}
```

## Error Codes

### Standard Errors (E01-E06)
- **E01** - Wheels blocked (High)
- **E02** - Navigation failure (High)
- **E03** - Battery low (Medium)
- **E04** - Software glitch (Medium)
- **E05** - Performance degraded (Low)
- **E06** - Communication error (Medium)

### Critical Errors (E07-E09) - HITL Required
- **E07** - Battery critical/swollen ⚠️ FIRE HAZARD
- **E08** - Firmware corruption ⚠️ UNPREDICTABLE BEHAVIOR
- **E09** - Safety sensor failure ⚠️ UNSAFE OPERATION

## Usage in A2A System

The RAG tool queries this database when:
1. Robot escalates an error via A2A protocol
2. Alert Receiver needs to determine solution actions
3. Classification of error urgency is required
4. HITL decision needs to be made

## Actions Field

The `actions` array lists automated remediation steps that the robot can execute:

**Movement Actions:**
- `clean_wheels`, `recalibrate_motors`, `reverse_motors`
- `lubricate_wheels`, `inspect_wheels`

**Navigation Actions:**
- `reset_navigation`, `reboot_sensors`, `recalibrate_positioning`
- `clear_map_cache`

**Power Actions:**
- `charge_battery`, `clean_charging_port`, `return_to_dock`
- `power_down`, `cooldown`, `emergency_shutdown`

**System Actions:**
- `reboot`, `restart_service`, `clear_cache`
- `reset_to_defaults`, `safe_mode_boot`

**Safety Actions:**
- `emergency_stop`, `disable_movement`, `safety_diagnostic`
- `wait_for_hitl`, `isolate_robot`

## Critical Error Handling

Errors E07, E08, E09 are flagged with `requires_hitl: true` and trigger:
1. Immediate escalation to human operators
2. Gmail notification to support@robonest.com
3. Jira ticket creation with Critical priority
4. Safety actions only (no autonomous resolution attempts)

## Integration with Alert Receiver

The Alert Receiver agent uses this knowledge base to:
- Determine appropriate actions based on error code
- Assess urgency and escalation requirements
- Generate structured JSON responses with action lists
- Trigger HITL notifications for critical errors

Example query:
```python
result = await rag_tool.query_knowledge_base(
    question="What is error code E07? What are the causes and solutions?",
    context="robot_errors",
    department="technical"
)
```

## Metadata

Each JSON file includes metadata:
- `version`: Database version (2.0)
- `last_updated`: Last modification date
- `language`: Language code (en/fr)
- `system`: System identifier
- `total_errors`: Count of documented errors
- `critical_errors`: List of HITL-required error codes

## Maintenance

When adding new error codes:
1. Update both English and French versions
2. Ensure all required fields are present
3. Test actions are valid in hardware_simulator
4. Update `total_errors` count in metadata
5. Add to `critical_errors` if HITL required

## Testing

Verify database integrity:
```python
import json

# Load and validate
with open('error_codes_database_english.json') as f:
    data = json.load(f)
    
# Check all critical errors are documented
assert all(code in data['error_codes'] for code in data['metadata']['critical_errors'])
```

---

**Last Updated:** 2025-11-29  
**Version:** 2.0  
**System:** RoboNest A2A Multi-Agent System
