# System Context
Project: Sentinel Agentic SOC

## Tech Stack
- Backend: Python 3.10+, FastAPI
- Frontend: React + Vite
- Core Architecture: 24 multi-agent consensus system operating over an encrypted EventBus.

## Architectural Boundaries & Rules
1. Do not modify the SQLite WAL logic in `InvestigationManager` without explicit instruction.
2. All API endpoints must use standard FastAPI paradigms and adhere to existing role-based authentication checks (e.g., `Depends(check_role(["admin"]))`).
3. Inter-agent communication must not bypass the established EventBus.
4. When handling exceptions, adhere to FastAPI best practices by utilizing proper logging mechanisms (`logger.error` or `logger.exception`) before raising an `HTTPException`.