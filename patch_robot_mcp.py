"""
Script pour patcher robot_agent.py avec les modifications MCP HTTP
"""
import sys
import re

def patch_robot_agent():
    """Apply MCP HTTP patches to robot_agent.py"""
    
    filepath = r"d:\PROGRAMME PYTHON\robonest-system\embedded_robot\robot_agent.py"
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch 1: Add import after line with "import random"
    if "from embedded_robot.mcp_http_client import" not in content:
        content = content.replace(
            "import random\n\nlogger = logging.getLogger(__name__)",
            "import random\n\n# MCP HTTP Client helpers\nfrom embedded_robot.mcp_http_client import send_alert_http, poll_solution_http\n\nlogger = logging.getLogger(__name__)"
        )
        print("[OK] Patch 1: Import ajouté")
    else:
        print("[SKIP] Patch 1: Import déjà présent")
    
    # Patch 2: Replace _send_alert HTTP call with MCP HTTP call
    # Find the section with httpx.AsyncClient in _send_alert
    old_send_pattern = r'(logger\.info\(f"📤 Sending alert:.*?\n\s+# Send to Alert Receiver\s+async with httpx\.AsyncClient.*?logger\.error\(f"❌ Alert failed:.*?\n)'
    new_send_code = '''logger.info(f"📤 Sending alert: {error.name} ({severity})")
            
            # Send to Alert Receiver MCP endpoint
            content = await send_alert_http(
                robot_id=self.robot_id,
                error_code=error.name,
                severity=severity,
                description=error.value,
                sensors=sensors
            )
            
            logger.info(f"✅ Alert sent successfully: {content}")
            self.last_alert_sent = alert_data
            self.alert_acknowledged = True
'''
    
    # Simplified: just replace the httpx.AsyncClient block
    if 'await send_alert_http(' not in content:
        # Find and replace the async with httpx section
        lines = content.split('\n')
        new_lines = []
        in_httpx_block = False
        skip_until_except = False
        
        for i, line in enumerate(lines):
            if '# Send to Alert Receiver' in line and 'async with httpx' in lines[i+1] if i+1 < len(lines) else False:
                # Start of block to replace
                in_httpx_block = True
                new_lines.append('            # Send to Alert Receiver MCP endpoint')
                new_lines.append('            content = await send_alert_http(')
                new_lines.append('                robot_id=self.robot_id,')
                new_lines.append('                error_code=error.name,')
                new_lines.append('                severity=severity,')
                new_lines.append('                description=error.value,')
                new_lines.append('                sensors=sensors')
                new_lines.append('            )')
                new_lines.append('')
                new_lines.append('            logger.info(f"✅ Alert sent successfully: {content}")')
                new_lines.append('            self.last_alert_sent = alert_data')
                new_lines.append('            self.alert_acknowledged = True')
                skip_until_except = True
                continue
            
            if skip_until_except:
                # Skip lines until we hit the except
                if line.strip().startswith('except Exception'):
                    skip_until_except = False
                    new_lines.append('')  # Add blank line
                    new_lines.append(line)
                continue
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        print("[OK] Patch 2: Méthode _send_alert modifiée")
    else:
        print("[SKIP] Patch 2: _send_alert déjà patché")
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n[OK] Patching terminé!")
    print(f"Fichier modifié: {filepath}")

if __name__ == "__main__":
    try:
        patch_robot_agent()
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        sys.exit(1)
