# Industry Value Creation: AI Support Ticket Triage Assistant

A one-day career-fair ready project that demonstrates a simple agentic AI workflow for realistic IT support operations.

## Problem
Support teams waste time manually reading, classifying, routing, and drafting responses for incoming tickets.

## Solution
This app runs a 4-agent pipeline:
- Classifier Agent: category, urgency, sentiment
- Router Agent: assigns team
- Reply Agent: drafts response
- QA Agent: validates reply quality (with one retry)

## Tech Stack
- Backend: FastAPI, Pydantic
- Frontend: React + Vite + TypeScript
- Storage: SQLite (auto-created local DB)
- Testing: Pytest

## Folder Structure

```text
AI Project/
  backend/
    app/
      agents/
      models/
      services/
      main.py
    tests/
    requirements.txt
  frontend/
    src/
      App.tsx
      main.tsx
      styles.css
    package.json
  data/
    sample_tickets.csv
  README.md
```

## Run Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

> If the database already exists and an Alembic version table is missing, run:
> ```bash
> alembic stamp head
> ```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## API Example
POST `/analyze`

```json
{
  "tickets": [
    {"ticket_id": "T1", "text": "I cannot login and this is urgent"}
  ]
}
```

## Testing

Comprehensive test suite with **60+ tests** covering authentication, user management, ticket processing, and all API endpoints.

### Run All Tests
```bash
cd backend
pytest
```

### Run by Category
```bash
pytest -m unit           # Fast unit tests (~5 seconds)
pytest -m integration    # API integration tests (~15 seconds)
pytest -m "not slow"     # Skip slow tests
```

### View Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
# Open: backend/htmlcov/index.html
```

### Test Files
- `test_auth.py` - Authentication & token handling (4 tests)
- `test_user_service.py` - User CRUD operations (7 tests)
- `test_agents.py` - AI agent pipeline (8 tests)
- `test_pipeline.py` - Complete ticket processing pipeline (7 tests)
- `test_api_endpoints.py` - All API endpoints (15 tests)
- `test_middleware.py` - Rate limiting & CORS (9 tests)
- `test_schemas.py` - Data validation (12 tests)

**Coverage**: 85%+ code coverage, 100% API endpoint coverage.

See [TEST_COVERAGE_REPORT.md](TEST_COVERAGE_REPORT.md) for detailed coverage breakdown.

## History and Persistence
- Each analysis run is saved automatically into a local SQLite file: `backend/support_assistant.db`
- Run history endpoint: `GET /history?limit=20`
- Run detail endpoint: `GET /history/{run_id}`

## 60-Second Demo Flow
1. Start backend and frontend.
2. Paste 4 to 5 sample tickets in UI.
3. Click Analyze Tickets.
4. Show category, urgency, team, and draft reply.
5. Open Agent Trace and explain the 4-agent workflow.

## Resume Bullet
Built an agentic AI support-ticket triage assistant using FastAPI and React that classifies issue urgency, routes ownership, generates response drafts, and validates quality through a multi-agent pipeline.
