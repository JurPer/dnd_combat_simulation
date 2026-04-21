# D&D Combat Simulator

This project now runs with:

- a React frontend in `frontend/`
- a FastAPI backend in `backend/`
- JSON-backed storage in `data/`

## Local setup

### Backend

1. Create and activate a Python virtual environment.

```bash
.\.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```bash
pip install -r reqs.txt
```

3. Start the API:

```bash
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

2. Start the frontend:

```bash
npm start
```

The frontend runs on `http://localhost:3000` and talks to the API on `http://localhost:8000`.

## Data

Combatants, actions, effects, and saved battles are stored in JSON:

- `data/combatants`
- `data/actions`
- `data/effects`
- `data/battles`

## Notes

- Docker is no longer required.
- Django and SQLite are no longer required for runtime.
