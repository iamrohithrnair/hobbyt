@echo off
echo.
echo ========================================
echo   Hobbyt - Gemini Repository Analyzer
echo ========================================
echo.

echo [1/3] Setting up Backend...
cd backend
if not exist .venv (
    uv venv .venv
)
call .venv\Scripts\activate
uv pip install -r requirements.txt
start "Hobbyt Backend" cmd /k "python main.py"
cd ..

echo.
echo [2/3] Setting up Frontend...
cd frontend
call npm install
start "Hobbyt Frontend" cmd /k "npm run dev"
cd ..

echo.
echo [3/3] Launching...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo All components are starting. Please wait a few seconds for the dev servers to initialize.
echo.
pause
