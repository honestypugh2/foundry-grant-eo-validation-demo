#!/bin/bash
# Start script for Grant Compliance Backend and Frontend
# This script starts both services in separate terminal windows

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Grant Compliance Application Launcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at $PROJECT_ROOT/.venv${NC}"
    echo -e "${YELLOW}Please create it first: python -m venv .venv${NC}"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not installed. Installing now...${NC}"
    cd "$PROJECT_ROOT/frontend"
    npm install
    cd "$PROJECT_ROOT"
fi

# Check if backend dependencies are installed
if ! "$PROJECT_ROOT/.venv/bin/python" -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Backend dependencies not installed. Installing now...${NC}"
    "$PROJECT_ROOT/.venv/bin/pip" install -r "$PROJECT_ROOT/backend/requirements.txt"
fi

echo -e "${GREEN}✓ All dependencies ready${NC}"
echo ""

# Function to start backend
start_backend() {
    echo -e "${BLUE}Starting Backend API...${NC}"
    cd "$PROJECT_ROOT/backend"
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}Backend starting at http://localhost:8000${NC}"
    echo -e "${GREEN}API Docs at http://localhost:8000/docs${NC}"
    uvicorn main:app --reload --port 8000
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}Starting Frontend App...${NC}"
    cd "$PROJECT_ROOT/frontend"
    echo -e "${GREEN}Frontend starting at http://localhost:3000${NC}"
    npm run dev
}

# Check if we're using tmux or screen
if command -v tmux &> /dev/null; then
    echo -e "${GREEN}Using tmux for process management${NC}"
    echo ""
    
    # Create a new tmux session
    SESSION_NAME="grant-compliance"
    
    # Kill existing session if it exists
    tmux kill-session -t $SESSION_NAME 2>/dev/null || true
    
    # Create new session with backend
    tmux new-session -d -s $SESSION_NAME -n backend
    tmux send-keys -t $SESSION_NAME:backend "cd $PROJECT_ROOT/backend && source $PROJECT_ROOT/.venv/bin/activate && uvicorn main:app --reload --port 8000" C-m
    
    # Create new window for frontend
    tmux new-window -t $SESSION_NAME -n frontend
    tmux send-keys -t $SESSION_NAME:frontend "cd $PROJECT_ROOT/frontend && npm run dev" C-m
    
    # Create a new window for logs
    tmux new-window -t $SESSION_NAME -n status
    tmux send-keys -t $SESSION_NAME:status "echo 'Grant Compliance Application Status' && echo '' && echo 'Backend: http://localhost:8000' && echo 'API Docs: http://localhost:8000/docs' && echo 'Frontend: http://localhost:3000' && echo '' && echo 'Switch windows: Ctrl+b then 0,1,2' && echo 'Detach: Ctrl+b then d' && echo 'Kill session: tmux kill-session -t $SESSION_NAME'" C-m
    
    # Attach to the session
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Services started in tmux session!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Backend:${NC}  http://localhost:8000"
    echo -e "${YELLOW}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${YELLOW}Frontend:${NC} http://localhost:3000"
    echo ""
    echo -e "${BLUE}Tmux Commands:${NC}"
    echo -e "  Switch windows: ${YELLOW}Ctrl+b then 0,1,2${NC}"
    echo -e "  Detach session: ${YELLOW}Ctrl+b then d${NC}"
    echo -e "  Reattach:       ${YELLOW}tmux attach -t $SESSION_NAME${NC}"
    echo -e "  Stop all:       ${YELLOW}tmux kill-session -t $SESSION_NAME${NC}"
    echo ""
    echo -e "${GREEN}Attaching to tmux session...${NC}"
    sleep 2
    tmux attach -t $SESSION_NAME
    
elif command -v gnome-terminal &> /dev/null; then
    echo -e "${GREEN}Using gnome-terminal for process management${NC}"
    echo ""
    
    # Start backend in new terminal
    gnome-terminal --title="Backend API" -- bash -c "cd $PROJECT_ROOT/backend && source $PROJECT_ROOT/.venv/bin/activate && echo -e '${GREEN}Backend API - http://localhost:8000${NC}' && echo -e '${GREEN}API Docs - http://localhost:8000/docs${NC}' && echo '' && uvicorn main:app --reload --port 8000; exec bash"
    
    sleep 2
    
    # Start frontend in new terminal
    gnome-terminal --title="Frontend App" -- bash -c "cd $PROJECT_ROOT/frontend && echo -e '${GREEN}Frontend App - http://localhost:3000${NC}' && echo '' && npm run dev; exec bash"
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Services started in separate terminals!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Backend:${NC}  http://localhost:8000"
    echo -e "${YELLOW}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${YELLOW}Frontend:${NC} http://localhost:3000"
    echo ""
    echo -e "${BLUE}Close the terminal windows to stop the services${NC}"
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}Using macOS Terminal for process management${NC}"
    echo ""
    
    # Start backend in new terminal
    osascript -e "tell application \"Terminal\" to do script \"cd $PROJECT_ROOT/backend && source $PROJECT_ROOT/.venv/bin/activate && echo 'Backend API - http://localhost:8000' && echo 'API Docs - http://localhost:8000/docs' && echo '' && uvicorn main:app --reload --port 8000\""
    
    sleep 2
    
    # Start frontend in new terminal
    osascript -e "tell application \"Terminal\" to do script \"cd $PROJECT_ROOT/frontend && echo 'Frontend App - http://localhost:3000' && echo '' && npm run dev\""
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Services started in separate terminals!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Backend:${NC}  http://localhost:8000"
    echo -e "${YELLOW}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${YELLOW}Frontend:${NC} http://localhost:3000"
    echo ""
    echo -e "${BLUE}Close the terminal windows to stop the services${NC}"
    
else
    # Fallback: Run in background with trap to cleanup
    echo -e "${YELLOW}Starting services in background mode${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Cleanup function
    cleanup() {
        echo ""
        echo -e "${YELLOW}Stopping services...${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}Services stopped${NC}"
        exit 0
    }
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Start backend in background
    (start_backend) &
    BACKEND_PID=$!
    
    sleep 3
    
    # Start frontend in background
    (start_frontend) &
    FRONTEND_PID=$!
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Services started!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Backend:${NC}  http://localhost:8000 (PID: $BACKEND_PID)"
    echo -e "${YELLOW}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${YELLOW}Frontend:${NC} http://localhost:3000 (PID: $FRONTEND_PID)"
    echo ""
    echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
    
    # Wait for processes
    wait
fi
