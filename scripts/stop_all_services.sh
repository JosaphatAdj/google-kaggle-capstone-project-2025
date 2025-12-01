#!/bin/bash

# ============================================================
# RoboNest - Stop All Services
# Gracefully stops Support System, Robot, and Simulator
# ============================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PIDS_DIR="$PROJECT_ROOT/.pids"

print_step() {
    echo -e "${BLUE}[▶]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Stopping RoboNest Services...                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop Support System
if [ -f "$PIDS_DIR/support.pid" ]; then
    PID=$(cat "$PIDS_DIR/support.pid")
    if ps -p $PID > /dev/null 2>&1; then
        print_step "Stopping Support System (PID: $PID)..."
        kill $PID
        sleep 2
        if ! ps -p $PID > /dev/null 2>&1; then
            print_success "Support System stopped"
        else
            kill -9 $PID
            print_warning "Support System force killed"
        fi
    fi
    rm "$PIDS_DIR/support.pid"
fi

# Stop Robot
if [ -f "$PIDS_DIR/robot.pid" ]; then
    PID=$(cat "$PIDS_DIR/robot.pid")
    if ps -p $PID > /dev/null 2>&1; then
        print_step "Stopping Robot (PID: $PID)..."
        kill $PID
        sleep 2
        if ! ps -p $PID > /dev/null 2>&1; then
            print_success "Robot stopped"
        else
            kill -9 $PID
            print_warning "Robot force killed"
        fi
    fi
    rm "$PIDS_DIR/robot.pid"
fi

# Stop Simulator
if [ -f "$PIDS_DIR/simulator.pid" ]; then
    PID=$(cat "$PIDS_DIR/simulator.pid")
    if ps -p $PID > /dev/null 2>&1; then
        print_step "Stopping Simulator (PID: $PID)..."
        kill $PID
        sleep 1
        if ! ps -p $PID > /dev/null 2>&1; then
            print_success "Simulator stopped"
        else
            kill -9 $PID
            print_warning "Simulator force killed"
        fi
    fi
    rm "$PIDS_DIR/simulator.pid"
fi

echo ""
echo -e "${GREEN}All services stopped successfully${NC}"
echo ""
