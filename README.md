#  Candidate Review Dashboard

This is a small internal recruiting dashboard built for the  take-home assignment. It gives reviewers a place to browse candidates, submit category scores, and generate a mock AI summary. Admins get the extra operational view: all reviewers' scores plus internal notes.

The app is split into a FastAPI backend and a React/Vite frontend.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, SQLite, JWT auth
- Frontend: React, Vite, plain CSS
- Tests: Pytest + FastAPI TestClient
- Local orchestration: Docker Compose

## Demo Accounts

These users are seeded automatically when the backend starts:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@.dev` | `Password123!` |
| Reviewer | `reviewer@.dev` | `Password123!` |

Registration is intentionally locked to the `reviewer` role. The API never accepts a role from the client during registration.

## Setup And Run

Copy the example environment file if you want to run with local env values:

```bash
cp .env.example .env
```

### Option 1: Docker Compose

```bash
docker compose up --build
```

Services:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`
- API docs: `http://127.0.0.1:8000/docs`

### Option 2: Run Locally

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://127.0.0.1:8000` by default. To point it somewhere else:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

## Tests

Run backend tests from the project root:

```bash
backend/.venv/bin/pytest
```

Current coverage includes:

- Admin can create a candidate and receive the expected response.
- Registration always creates a reviewer, even if the client sends a role.
- Reviewers only see their own scores and do not receive `internal_notes`.

The frontend build can be checked with:

```bash
cd frontend
npm run build
```

## API Examples

Login as admin:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@.dev","password":"Password123!"}'
```

Save the returned token:

```bash
TOKEN="paste-access-token-here"
```

List candidates with pagination:

```bash
curl "http://127.0.0.1:8000/candidates?offset=0&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

Filter candidates:

```bash
curl "http://127.0.0.1:8000/candidates?status=reviewed&role_applied=Backend&skill=Python&keyword=engineer&offset=0&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

Get candidate detail:

```bash
curl "http://127.0.0.1:8000/candidates/CANDIDATE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Submit a score:

```bash
curl -X POST "http://127.0.0.1:8000/candidates/CANDIDATE_ID/scores" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category":"Technical","score":5,"note":"Strong backend fundamentals and clear API thinking."}'
```

Generate the mock AI summary:

```bash
curl -X POST "http://127.0.0.1:8000/candidates/CANDIDATE_ID/summary" \
  -H "Authorization: Bearer $TOKEN"
```

Stream score updates with SSE:

```bash
curl -N "http://127.0.0.1:8000/candidates/CANDIDATE_ID/stream" \
  -H "Authorization: Bearer $TOKEN"
```

## Debugging Note

The assignment included this query pattern:

```python
def search_candidates(status: str, keyword: str, page: int, page_size: int):
    all_candidates = db.execute("SELECT * FROM candidates").fetchall()
    filtered = [c for c in all_candidates if c["status"] == status]
    # ... also filter by keyword in Python ...
    offset = (page - 1) * page_size
    return filtered[offset : offset + page_size]
```

The bug is that it loads every candidate into application memory before filtering and pagination. That may seem fine with a few rows, but it breaks down quickly: the database cannot use indexes effectively, every request gets slower as the table grows, and pagination becomes expensive because the app is paginating after doing unnecessary work.

The correct approach is to push filtering, sorting, counting, and pagination into the database query. In this project, `/candidates` builds SQLAlchemy filters and applies `offset` and `limit` in SQL. The models also define indexes on fields used by common access patterns, such as candidate status, role, and score ownership.

## Architecture Decision Record

### 1. FastAPI For The Backend

Context: The API needs JWT auth, request validation, async behavior for the mock AI call, and clean OpenAPI docs for testing.

Decision: I used FastAPI with Pydantic schemas and dependency-based auth.

Trade-off: FastAPI is very productive for this size of project, but the built-in startup hook used here is simple. In a larger production service I would move database migrations and seeding into explicit commands.

### 2. SQLite With SQLAlchemy Models

Context: The assignment allowed SQLite or DynamoDB-style storage. For a take-home project, the API should be easy to run locally without cloud setup.

Decision: I used SQLite with SQLAlchemy models for users, candidates, and scores. Candidate skills are stored as JSON text to keep the schema lightweight while still supporting list-like data in responses.

Trade-off: SQLite keeps the project simple and portable, but filtering list fields with `LIKE` is not as strong as a normalized candidate-skills table or a database with JSON indexes. For a production version, I would likely normalize skills or use Postgres JSONB.

### 3. Role-Based Visibility In The API

Context: Reviewers and admins see different data. Reviewers can score candidates but should only see their own scores and should not see internal notes.

Decision: The backend enforces role checks from the JWT-authenticated user. The frontend also hides admin-only UI, but it does not rely on hiding alone for security.

Trade-off: The current JWT setup is intentionally small and local-friendly. A production version would add refresh tokens, password reset flow, stronger secret management, and probably centralized identity.

## Learning Reflection

One thing I paid closer attention to here was making the seeded data useful for actually testing filters and pagination, instead of adding only one or two happy-path records. Given more time, I would add a small migration layer and broaden frontend tests around the AI summary loading state and role-specific UI.

I also kept the mock AI summary intentionally boring and predictable. In a real system, I would wrap the LLM call behind a service boundary with retries, timeouts, and audit logging so reviewers can trust how the summary was produced.
