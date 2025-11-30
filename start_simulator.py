"""
Start Simulator Console - Launch interactive test console
"""
import subprocess
import sys
from pathlib import Path
import os

def main():
    """Launch simulator console"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 70)
    print("  🎮 ROBONEST - SIMULATOR CONSOLE")
    print("=" * 70)
    print("\n🚀 Starting interactive test console...")
    print("   Make sure robot is running (start_robot.py)")
    print("\n" + "=" * 70 + "\n")
    
    project_root = Path(__file__).parent
    
    # Run console
    subprocess.run(
        [sys.executable, "embedded_robot/simulator_console.py"],
        cwd=project_root
    )

if __name__ == "__main__":
    main()
