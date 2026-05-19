# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Critical Architecture

- Backend runs in **dual mode**: FastAPI server (port 8000) AND ADK agent service
- [`gemini_service.py`](backend/gemini_service.py) defines the Google ADK agent with tools; can be run directly for interactive CLI mode
- [`main.py`](backend/main.py) runs FastAPI server: `python backend/main.py`
- MCP config at [`.hobbyt/mcp.json`](.hobbyt/mcp.json) — update paths for different machines

## Non-Standard Patterns

- **In-memory state**: [`GeminiStorage`](backend/gemini_service.py) class stores insights without persistence (resets on restart)
- **Polling architecture**: Frontend polls `/live-updates` every 2 seconds instead of WebSockets
- **ADK tools**: [`submit_repository_insights()`](backend/gemini_service.py) is the ADK tool for pushing data to UI
- **Platform-specific deps**: `python-magic` vs `python-magic-bin` based on OS in [`requirements.txt`](backend/requirements.txt)

## Environment Variables

- `GEMINI_API_KEY` — Google AI Studio API key (required)
- `GEMINI_MODEL_ID` — Model to use (default: `gemini-3.1-flash-lite`)

## Setup

- Run `setup.sh` (macOS/Linux) or `setup.bat` (Windows) to start both services
- Uses `uv` for Python package management
- Backend venv: `backend/.venv` (created automatically)
- Frontend: Standard Vite + React (port 5173)

## Commands

```bash
# Backend setup (from project root)
cd backend && uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt && python main.py

# Frontend (from project root)
cd frontend && npm run dev

# ADK Agent interactive mode (from project root)
cd backend && source .venv/bin/activate && python gemini_service.py
```