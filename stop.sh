#!/bin/bash
# Stop script for Grant Compliance Application

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping Grant Compliance Application...${NC}"

# Kill tmux session if it exists
tmux kill-session -t grant-compliance 2>/dev/null && echo -e "${GREEN}✓ Tmux session stopped${NC}"

# Kill backend (uvicorn) processes
pkill -9 -f "uvicorn" 2>/dev/null && echo -e "${GREEN}✓ Backend stopped${NC}" || echo -e "${GREEN}✓ Backend not running${NC}"

# Kill frontend (Vite/Node) processes  
pkill -9 -f "node.*vite" 2>/dev/null && echo -e "${GREEN}✓ Vite stopped${NC}" || echo -e "${GREEN}✓ Frontend not running${NC}"

echo -e "${GREEN}All services stopped!${NC}"
exit 0
