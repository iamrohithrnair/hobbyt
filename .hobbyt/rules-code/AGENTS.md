# Code Mode Rules (Non-Obvious Only)

## Critical Patterns

- **GeminiStorage is stateless**: [`GeminiStorage._latest_insights`](../../backend/gemini_service.py) is class-level in-memory only - no persistence
- **ADK Agent service**: [`gemini_service.py`](../../backend/gemini_service.py) runs as ADK agent when executed directly, imported as module in FastAPI
- **Paths in MCP config**: [`.hobbyt/mcp.json`](../.hobbyt/mcp.json) configures local paths

## Backend Conventions

- FastAPI endpoints use `async def` even without await (for consistency)
- ADK tool parameters must match exact names in [`submit_repository_insights()`](../../backend/gemini_service.py)
- No database - all state in [`GeminiStorage`](../../backend/gemini_service.py) class variable

## Frontend Conventions

- Polling interval hardcoded at 2000ms in [`App.jsx`](../../frontend/src/App.jsx)
- Backend URL hardcoded as `http://localhost:8000` (no env vars)
- State management via React hooks only (no Redux/Context)

## No Access To

- MCP tools
- Browser tools