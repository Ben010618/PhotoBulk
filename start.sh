#!/usr/bin/env bash
# ==============================================================================
# KameraPh Studio Suite: Unix / macOS / Linux Boot Orchestrator
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==================================================="
echo "  Launching KameraPh Studio Suite (macOS / Linux)"
echo "==================================================="

# 1. Determine Python interpreter
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# 2. Check virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# 3. Verify .env file existence
if [ ! -f ".env" ]; then
    echo "Notice: .env not found. Creating from .env.example..."
    cp .env.example .env
fi

# 4. Database Schema Instantiation
echo "Instantiating database schema..."
$PYTHON_CMD init_db.py

# 5. Check frontend build
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend assets..."
    if command -v npm &>/dev/null; then
        (cd frontend && npm install && npm run build)
    else
        echo "Warning: npm not found. Serving without prebuilt frontend dist."
    fi
fi

# 6. Launch Browser if in desktop environment
HOST="127.0.0.1"
PORT="8000"
URL="http://$HOST:$PORT"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$URL" &>/dev/null || true
elif command -v xdg-open &>/dev/null; then
    xdg-open "$URL" &>/dev/null || true
fi

echo "Starting KameraPh Uvicorn API Server on $URL..."
exec $PYTHON_CMD -m uvicorn api_server:app --host "$HOST" --port "$PORT" --reload
