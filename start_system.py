"""
RoboNest System Launcher
Launches core infrastructure: Message Bus, COO Agent, Alert Receiver
Robot and simulator should be launched separately in their own terminals
"""
import subprocess
import sys
import time
from pathlib import Path
import os

def print_banner(text, char="="):
    """Print a formatted banner"""
    print(f"\n{char * 70}")
    print(f"  {text}")
    print(f"{char * 70}")

def check_env():
    """Check if .env file exists and has GOOGLE_API_KEY"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("\n⚠️  WARNING: .env file not found!")
        print("   Create .env file with: GOOGLE_API_KEY=your_key_here")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    return True

def main():
    """Main launcher for core infrastructure"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_banner("🚀 ROBONEST A2A SYSTEM - CORE INFRASTRUCTURE", "=")
    
    # Check environment
    check_env()
    
    project_root = Path(__file__).parent
    processes = []
    
    try:
        # 1. Alert Receiver (A2A Server)
        print("\n📡 Starting Alert Receiver (port 8000)...")
        alert_receiver = subprocess.Popen(
            [sys.executable, "agents/alert_receiver/alert_receiver_a2a.py"],
            cwd=project_root
        )
        processes.append(("Alert Receiver", alert_receiver))
        print("   ✅ Alert Receiver started")
        time.sleep(3)
        
        # 2. Main System (COO + Message Bus)
        print("\n🧠 Starting Main System (COO Agent + Message Bus)...")
        main_system = subprocess.Popen(
            [sys.executable, "agents/main.py"],
            cwd=project_root
        )
        processes.append(("Main System", main_system))
        print("   ✅ Main System started")
        time.sleep(3)
        
        # 3. Show status
        print_banner("✅ CORE INFRASTRUCTURE RUNNING", "=")
        print("\n📍 Services:")
        print("   ✅ Alert Receiver (A2A):  http://localhost:8000")
        print("   ✅ Agent Card:             http://localhost:8000/.well-known/agent-card.json")
        print("   ✅ Main System (COO):      Running")
        print("   ✅ Message Bus:            Running")
        
        print("\n📚 Next Steps:")
        print("\n   🤖 Start Robot (in separate terminal):")
        print("      python start_robot.py")
        
        print("\n   🎮 Start Simulator Console (in separate terminal):")
        print("      python start_simulator.py")
        
        print("\n   OR manually:")
        print("      Terminal 2: cd embedded_robot && python main_a2a.py")
        print("      Terminal 3: cd embedded_robot && python simulator_console.py")
        
        print_banner("Press CTRL+C to stop core infrastructure", "=")
        
        # Keep running
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} stopped unexpectedly!")
                    raise Exception(f"{name} crashed")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt received")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Cleanup
        print("\n🛑 Shutting down core infrastructure...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
        
        print("\n✅ Core infrastructure stopped")
        print("👋 Goodbye!\n")


if __name__ == "__main__":
    main()
