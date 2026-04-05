
✅ Features
Backend
POST /auth/register — Create account
POST /auth/login — Sign in and receive JWT
GET /auth/me — Retrieve current user
POST /analyze — Analyze support tickets
GET /history — Get analysis history
GET /history/{run_id} — Fetch run details
DELETE /history/{run_id} — Remove saved run
GET /health — Health check
GET /system-mode — Mode metadata
Rate limiting: 120 requests / 60 seconds
Full schema validation with Pydantic
Frontend
Friendly onboarding / welcome screen
Create account / sign in flow
Paste messages, analyze, review results
History view with saved analysis runs
Clear UI with progressive feedback
Testing & Reliability
60+ tests across unit and integration coverage
Shared fixtures and isolated DB tests
pytest + pytest-cov
Documentation in TESTING.md
🛠️ Backend Setup
Run Database Migrations
If the DB already exists but the Alembic version table is missing:

Start Backend
Backend URL: http://127.0.0.1:8000

🌐 Frontend Setup
Frontend URL: http://127.0.0.1:5173

🔧 Required Environment
Create a .env file in backend with:

🧪 Testing
Run all tests:

Run unit tests only:

Run integration tests:

Generate coverage report:

Open HTML report at backend/htmlcov/index.html

📌 API Summary
Authentication
POST /auth/register
POST /auth/login
GET /auth/me
Ticket Analysis
POST /analyze
History
GET /history
GET /history/{run_id}
DELETE /history/{run_id}
Monitoring
GET /health
GET /system-mode
🧠 Notes
The system uses a safe hybrid AI mode: OpenAI agents when configured, otherwise deterministic fallback logic.
User identity is preserved through JWT authentication.
Local data is persisted in SQLite by default for easy dev/test usage.
