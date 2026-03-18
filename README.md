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
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

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
