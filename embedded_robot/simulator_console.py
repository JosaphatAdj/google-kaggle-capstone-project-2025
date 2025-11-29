"""
Robot Simulator Console - Interactive CLI for testing robot scenarios
"""

import asyncio
import httpx
from typing import Optional
import sys
from pathlib import Path

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class RobotSimulator:
    """Interactive robot simulator"""
    
    def __init__(self, robot_url: str = "http://localhost:8001"):
        self.robot_url = robot_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def simulate_error(self, error_code: str):
        """Simulate an error on the robot"""
        try:
            response = await self.client.post(f"{self.robot_url}/simulate/error/{error_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"{Colors.OKGREEN}✅ {result['message']}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}   Robot will auto-detect and handle via A2A protocol{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Failed: {response.status_code}{Colors.ENDC}")
        
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    async def human_intervention(self, action: str):
        """Simulate human intervention (HITL)"""
        try:
            response = await self.client.post(f"{self.robot_url}/fix/{action}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"{Colors.OKGREEN}✅ HITL Action completed: {result.get('message', 'Success')}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Failed: {response.status_code}{Colors.ENDC}")
        
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    async def get_status(self):
        """Get robot status"""
        try:
            response = await self.client.get(f"{self.robot_url}/status")
            
            if response.status_code == 200:
                status = response.json()
                
                print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
                print(f"{Colors.BOLD}🤖 Robot Status: {status['robot_id']}{Colors.ENDC}")
                print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
                
                state_color = Colors.OKGREEN if status['state'] == 'operational' else Colors.FAIL
                print(f"\n  State: {state_color}{status['state'].upper()}{Colors.ENDC}")
                
                if status['current_error']:
                    print(f"  {Colors.WARNING}⚠️  Current Error: {status['current_error']}{Colors.ENDC}")
                
                print(f"\n  📊 Sensors:")
                print(f"     Battery: {status['battery_level']}%")
                print(f"     Temperature: {status['temperature']}°C")
                print(f"     Wheels: {'❌ BLOCKED' if status['wheels_blocked'] else '✅ OK'}")
                
                print(f"\n  📈 Metrics:")
                metrics = status['adk_metrics']
                print(f"     Self-resolutions: {metrics['self_resolutions']}")
                print(f"     Escalations: {metrics['escalations']}")
                print(f"     Failed solutions: {metrics['failed_solutions']}")
                print(f"     Success rate: {metrics['self_resolution_rate']}")
                print(f"     Protocol: {metrics.get('protocol', 'HTTP')}")
                
                print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
            else:
                print(f"{Colors.FAIL}❌ Failed to get status: {response.status_code}{Colors.ENDC}")
        
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}⚠️  Make sure robot is running on {self.robot_url}{Colors.ENDC}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def interactive_console():
    """Main interactive console"""
    
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}      🤖 ROBONEST ROBOT SIMULATOR - A2A VERSION{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
    
    simulator = RobotSimulator()
    
    # Check connection
    print(f"{Colors.OKCYAN}Checking robot connection...{Colors.ENDC}")
    await simulator.get_status()
    
    while True:
        print(f"\n{Colors.BOLD}Available Commands:{Colors.ENDC}")
        print(f"  {Colors.OKBLUE}1{Colors.ENDC} - Simulate E01 (Roues bloquées)")
        print(f"  {Colors.OKBLUE}2{Colors.ENDC} - Simulate E03 (Batterie faible)")
        print(f"  {Colors.WARNING}3{Colors.ENDC} - Simulate E07 (Batterie critique - HITL)")
        print(f"  {Colors.OKGREEN}h{Colors.ENDC} - Intervention Humaine (HITL) - débloquer roues")
        print(f"  {Colors.OKGREEN}b{Colors.ENDC} - Intervention Humaine (HITL) - refroidir batterie")
        print(f"  {Colors.OKCYAN}s{Colors.ENDC} - Statut Robot")
        print(f"  {Colors.FAIL}q{Colors.ENDC} - Quit")
        
        try:
            choice = input(f"\n{Colors.BOLD}Votre choix: {Colors.ENDC}").strip().lower()
            
            if choice == '1':
                print(f"\n{Colors.WARNING}🎬 Simulation E01 - Roues bloquées...{Colors.ENDC}")
                await simulator.simulate_error("E01")
                print(f"{Colors.OKCYAN}   → Le robot va détecter l'erreur et escalader via A2A{Colors.ENDC}")
                print(f"{Colors.OKCYAN}   → Le système de support va analyser et proposer une solution{Colors.ENDC}")
                print(f"{Colors.OKCYAN}   → La solution sera renvoyée au robot via A2A{Colors.ENDC}")
            
            elif choice == '2':
                print(f"\n{Colors.WARNING}🎬 Simulation E03 - Batterie faible...{Colors.ENDC}")
                await simulator.simulate_error("E03")
                print(f"{Colors.OKCYAN}   → Escalation automatique via protocole A2A{Colors.ENDC}")
            
            elif choice == '3':
                print(f"\n{Colors.FAIL}🚨 Simulation E07 - BATTERIE CRITIQUE (HITL requis){Colors.ENDC}")
                await simulator.simulate_error("E07")
                print(f"{Colors.WARNING}   → Erreur critique détectée{Colors.ENDC}")
                print(f"{Colors.WARNING}   → Le robot va escalader avec flag HITL=True{Colors.ENDC}")
                print(f"{Colors.WARNING}   → Intervention humaine requise{Colors.ENDC}")
                print(f"{Colors.OKCYAN}   → Utilisez commande 'b' pour simuler intervention{Colors.ENDC}")
            
            elif choice == 'h':
                print(f"\n{Colors.OKGREEN}🔧 Intervention Humaine: Déblocage roues manuel{Colors.ENDC}")
                await simulator.human_intervention("clean_wheels")
                print(f"{Colors.OKGREEN}   → Le robot reprend ses opérations normales{Colors.ENDC}")
            
            elif choice == 'b':
                print(f"\n{Colors.OKGREEN}🔧 Intervention Humaine: Refroidissement batterie{Colors.ENDC}")
                await simulator.human_intervention("cooldown")
                print(f"{Colors.OKGREEN}   → Le robot reprend ses opérations normales{Colors.ENDC}")
            
            elif choice == 's':
                await simulator.get_status()
            
            elif choice == 'q':
                print(f"\n{Colors.OKCYAN}👋 Au revoir!{Colors.ENDC}\n")
                break
            
            else:
                print(f"{Colors.WARNING}⚠️  Commande inconnue{Colors.ENDC}")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.OKCYAN}👋 Au revoir!{Colors.ENDC}\n")
            break
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    await simulator.close()


def main():
    """Main entry point"""
    try:
        asyncio.run(interactive_console())
    except KeyboardInterrupt:
        print(f"\n{Colors.OKCYAN}Au revoir!{Colors.ENDC}")


if __name__ == "__main__":
    main()
