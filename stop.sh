#!/bin/bash
# Stop script for Grant Compliance Application
# This script stops all running backend and frontend processes

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Grant Compliance Application...${NC}"
echo ""

# Kill tmux session if it exists
if tmux has-session -t grant-compliance 2>/dev/null; then
    echo -e "${YELLOW}Killing tmux session...${NC}"
    tmux kill-session -t grant-compliance
    echo -e "${GREEN}✓ Tmux session stopped${NC}"
fi

# Kill backend processes
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}Stopping backend (port 8000)...${NC}"
    kill -9 $BACKEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo -e "${GREEN}✓ Backend not running${NC}"
fi

# Kill frontend processes
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}Stopping frontend (port 3000)...${NC}"
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Frontend stopped${NC}"
else
    echo -e "${GREEN}✓ Frontend not running${NC}"
fi

# Also check for Vite's alternative port
FRONTEND_ALT_PIDS=$(lsof -ti:5173 2>/dev/null || true)
if [ ! -z "$FRONTEND_ALT_PIDS" ]; then
    echo -e "${YELLOW}Stopping frontend (port 5173)...${NC}"
    kill -9 $FRONTEND_ALT_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Frontend (alt port) stopped${NC}"
fi

echo ""
echo -e "${GREEN}All services stopped successfully!${NC}"
