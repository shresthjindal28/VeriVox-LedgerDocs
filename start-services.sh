#!/bin/bash
# Start all Study With Me backend services

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Starting Study With Me Backend Services            ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any existing processes on required ports
echo "→ Stopping any existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
sleep 1

# Start PDF Service (port 8000)
echo "→ Starting PDF Service on port 8000..."
cd "$SCRIPT_DIR/ai-pdf-server"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null
python run.py &
PDF_PID=$!

# Start User Service (port 8001)
echo "→ Starting User Service on port 8001..."
cd "$SCRIPT_DIR/User-Service"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null
python run.py &
USER_PID=$!

# Start Gateway (port 8080)
echo "→ Starting API Gateway on port 8080..."
cd "$SCRIPT_DIR/gateway"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null
python run.py &
GATEWAY_PID=$!

# Wait for services to start
sleep 3

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Services Started                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  PDF Service:  http://localhost:8000  (PID: $PDF_PID)               ║"
echo "║  User Service: http://localhost:8001  (PID: $USER_PID)               ║"
echo "║  API Gateway:  http://localhost:8080  (PID: $GATEWAY_PID)               ║"
echo "║                                                              ║"
echo "║  API Docs:     http://localhost:8080/docs                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait
