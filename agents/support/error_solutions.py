# Error Code to Solution Mapping
# This provides deterministic mapping instead of LLM heuristics

ERROR_SOLUTIONS = {
    "E01": {
        "actions": ["clean_wheels", "recalibrate_motors"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Wheels blocked - cleaning procedure"
    },
    "E02": {
        "actions": ["reset_navigation", "reboot_sensors"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Navigation error - reset required"
    },
    "E03": {
        "actions": ["charge_battery", "return_to_dock"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Low battery - return to dock"
    },
    "E04": {
        "actions": ["restart_service", "reboot"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Software error - restart needed"
    },
    "E05": {
        "actions": ["clear_cache", "optimize_memory"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Performance degraded - optimization"
    },
    "E06": {
        "actions": ["reconnect_wifi", "reset_network"],
        "requires_hitl": False,
        "is_temporary": False,
        "description": "Communication lost - network reset"
    },
    "E07": {
        "actions": ["emergency_shutdown", "wait_for_hitl"],
        "requires_hitl": True,
        "is_temporary": True,
        "description": "Battery critical/swollen - HITL required"
    },
    "E08": {
        "actions": ["safe_mode", "wait_for_hitl"],
        "requires_hitl": True,
        "is_temporary": True,
        "description": "Firmware corruption - HITL required"
    },
    "E09": {
        "actions": ["emergency_stop", "wait_for_hitl"],
        "requires_hitl": True,
        "is_temporary": True,
        "description": "Safety sensor failure - HITL required"
    }
}


def get_solution_for_error(error_code: str) -> dict:
    """
    Get predefined solution for error code
    
    Args:
        error_code: Error code (E01-E09)
        
    Returns:
        Solution dict with actions, requires_hitl, etc.
    """
    solution_template = ERROR_SOLUTIONS.get(error_code)
    
    if solution_template:
        return {
            "actions": solution_template["actions"].copy(),
            "requires_hitl": solution_template["requires_hitl"],
            "is_temporary_solution": solution_template["is_temporary"],
            "description": solution_template["description"]
        }
    else:
        # Unknown error - escalate to HITL
        return {
            "actions": ["wait_for_hitl"],
            "requires_hitl": True,
            "is_temporary_solution": False,
            "description": f"Unknown error {error_code} - manual intervention required"
        }
