# Migration Summary

This project has been migrated away from Django, SQLite, and Docker.

New runtime architecture:

- `frontend/`: existing React application
- `backend/`: new FastAPI application
- `data/`: JSON-backed storage for combatants, actions, effects, and saved battles

Key design choices:

- The battle engine now runs on plain Python classes in `backend/domain` and `backend/services`.
- Persistent data is stored in JSON files under `data/`.
- The frontend keeps the same route structure and payload shapes wherever practical.
- Legacy Django code remains only as historical reference until it is removed or ignored by callers.

Local development:

- Backend: `uvicorn backend.api.main:app --reload --port 8000`
- Frontend: `npm start` from `frontend/`
