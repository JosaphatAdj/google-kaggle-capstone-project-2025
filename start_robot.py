"""
Start Robot - Launch embedded robot in standalone terminal
"""
import subprocess
import sys
from pathlib import Path
import os

def main():
    """Launch robot"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 70)
    print("  🤖 ROBONEST - EMBEDDED ROBOT")
    print("=" * 70)
    print("\n🚀 Starting robot on port 8001...")
    print("   Make sure core infrastructure is running (start_system.py)")
    print("\n" + "=" * 70 + "\n")
    
    project_root = Path(__file__).parent
    
    # Run robot
    subprocess.run(
        [sys.executable, "embedded_robot/main_a2a.py"],
        cwd=project_root
    )

if __name__ == "__main__":
    main()
