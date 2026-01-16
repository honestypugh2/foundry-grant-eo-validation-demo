#!/bin/bash
# Start script for Grant Compliance Backend and Frontend

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

echo "========================================"
echo "Grant Compliance Application Launcher"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Create it with: python -m venv .venv"
    exit 1
fi

# Stop any existing services first
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
sleep 1

# Start backend
echo "Starting Backend API..."
cd "$PROJECT_ROOT/src/backend"
"$PROJECT_ROOT/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/backend.log" 2>&1 &
echo "Backend started (PID: $!)"

sleep 3

# Start frontend
echo "Starting Frontend App..."
cd "$PROJECT_ROOT/src/frontend"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
echo "Frontend started (PID: $!)"

sleep 3

echo ""
echo "========================================"
echo "Services started!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "View logs:"
echo "  tail -f $LOG_DIR/backend.log"
echo "  tail -f $LOG_DIR/frontend.log"
echo ""
echo "Stop: ./stop.sh"
