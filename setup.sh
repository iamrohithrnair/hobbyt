#!/bin/bash
echo ""
echo "========================================"
echo "  Hobbyt – Gemini Repository Analyzer"
echo "========================================"
echo ""

echo "[1/3] Setting up Backend..."
cd backend
if [ ! -d .venv ]; then
    uv venv .venv
fi
uv pip install -r requirements.txt
.venv/bin/python main.py &
BACKEND_PID=$!
cd ..

echo ""
echo "[2/3] Setting up Frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "[3/3] Launching..."
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "All components are starting. Press Ctrl+C to stop."
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
