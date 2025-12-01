#!/bin/bash

# ============================================================
# RoboNest - Start All Services
# Launches Support System, Robot, and optionally Simulator
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_ROOT/logs"

# PID files
PIDS_DIR="$PROJECT_ROOT/.pids"
SUPPORT_PID="$PIDS_DIR/support.pid"
ROBOT_PID="$PIDS_DIR/robot.pid"
SIMULATOR_PID="$PIDS_DIR/simulator.pid"

# ============================================================
# Helper Functions
# ============================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║               RoboNest System Launcher                 ║"
    echo "║          Multi-Agent Robot Support Platform            ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[▶]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# ============================================================
# Prerequisites Check
# ============================================================

check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        print_error "Python not found. Please install Python 3.12+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    
    # Check .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error ".env file not found"
        echo -e "${YELLOW}Creating from .env.example...${NC}"
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_warning "Please edit .env with your GOOGLE_API_KEY before continuing"
        exit 1
    fi
    print_success ".env file found"
    
    # Check GOOGLE_API_KEY
    if ! grep -q "GOOGLE_API_KEY=.*[A-Za-z0-9]" "$PROJECT_ROOT/.env"; then
        print_error "GOOGLE_API_KEY not configured in .env"
        print_warning "Please add your API key to .env file"
        exit 1
    fi
    print_success "GOOGLE_API_KEY configured"
    
    # Check dependencies
    if ! python -c "import google.adk" 2>/dev/null; then
        print_warning "Dependencies not installed. Installing..."
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    print_success "Dependencies installed"
}

# ============================================================
# Directory Setup
# ============================================================

setup_directories() {
    print_step "Setting up directories..."
    mkdir -p "$LOGS_DIR"
    mkdir -p "$PIDS_DIR"
    print_success "Directories ready"
}

# ============================================================
# Service Management
# ============================================================

start_support_system() {
    print_step "Starting Support System (Port 8000)..."
    
    cd "$PROJECT_ROOT"
    nohup python agents/main.py > "$LOGS_DIR/support.log" 2>&1 &
    echo $! > "$SUPPORT_PID"
    
    # Wait for startup
    sleep 3
    
    # Check if running
    if ps -p $(cat "$SUPPORT_PID") > /dev/null 2>&1; then
        # Verify A2A endpoint
        if curl -s -f http://localhost:8000/.well-known/agent-card.json > /dev/null 2>&1; then
            print_success "Support System running (PID: $(cat "$SUPPORT_PID"))"
        else
            print_warning "Support System started but A2A endpoint not responding"
        fi
    else
        print_error "Support System failed to start"
        cat "$LOGS_DIR/support.log" | tail -20
        exit 1
    fi
}

start_robot() {
    print_step "Starting Embedded Robot (Port 8001)..."
    
    cd "$PROJECT_ROOT"
    nohup python embedded_robot/main_a2a.py > "$LOGS_DIR/robot.log" 2>&1 &
    echo $! > "$ROBOT_PID"
    
    # Wait for startup
    sleep 3
    
    # Check if running
    if ps -p $(cat "$ROBOT_PID") > /dev/null 2>&1; then
        # Verify status endpoint
        if curl -s -f http://localhost:8001/status > /dev/null 2>&1; then
            print_success "Robot running (PID: $(cat "$ROBOT_PID"))"
        else
            print_warning "Robot started but status endpoint not responding"
        fi
    else
        print_error "Robot failed to start"
        cat "$LOGS_DIR/robot.log" | tail -20
        exit 1
    fi
}

start_simulator() {
    print_step "Starting Error Simulator (Port 8002)..."
    
    cd "$PROJECT_ROOT"
    nohup python start_simulator.py > "$LOGS_DIR/simulator.log" 2>&1 &
    echo $! > "$SIMULATOR_PID"
    
    sleep 2
    
    if ps -p $(cat "$SIMULATOR_PID") > /dev/null 2>&1; then
        print_success "Simulator running (PID: $(cat "$SIMULATOR_PID"))"
    else
        print_warning "Simulator failed to start (this is optional)"
    fi
}

# ============================================================
# Status Display
# ============================================================

display_status() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║               System Started Successfully              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo "  • Support System : http://localhost:8000"
    echo "  • Embedded Robot : http://localhost:8001"
    if [ -f "$SIMULATOR_PID" ] && ps -p $(cat "$SIMULATOR_PID") > /dev/null 2>&1; then
        echo "  • Simulator      : http://localhost:8002"
    fi
    echo ""
    echo -e "${BLUE}Health Checks:${NC}"
    echo "  curl http://localhost:8000/.well-known/agent-card.json"
    echo "  curl http://localhost:8001/status"
    echo ""
    echo -e "${BLUE}Logs:${NC}"
    echo "  tail -f $LOGS_DIR/support.log"
    echo "  tail -f $LOGS_DIR/robot.log"
    echo ""
    echo -e "${BLUE}Stop Services:${NC}"
    echo "  ./scripts/stop_all_services.sh"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to exit, or run:${NC}"
    echo "  tail -f $LOGS_DIR/*.log"
    echo ""
}

# ============================================================
# Cleanup on Exit
# ============================================================

cleanup() {
    echo ""
    print_warning "Interrupt received. Services are running in background."
    print_step "Use './scripts/stop_all_services.sh' to stop all services"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================
# Main Execution
# ============================================================

main() {
    print_banner
    
    check_prerequisites
    setup_directories
    
    # Start services
    start_support_system
    sleep 2
    start_robot
    
    # Optionally start simulator
    if [ "$1" == "--with-simulator" ]; then
        sleep 2
        start_simulator
    fi
    
    display_status
    
    # Keep script running to show logs
    if [ "$1" == "--follow-logs" ]; then
        print_step "Following logs (Ctrl+C to exit)..."
        tail -f "$LOGS_DIR"/*.log
    fi
}

# Parse arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --with-simulator    Also start the error simulator"
        echo "  --follow-logs       Follow logs after starting services"
        echo "  --help             Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                           # Start support + robot"
        echo "  $0 --with-simulator          # Start all including simulator"
        echo "  $0 --follow-logs             # Start and follow logs"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
