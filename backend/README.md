# Backend — AI Support & Operations Agent

FastAPI + PostgreSQL + pgvector + Groq chat + Gemini embeddings. See root `README.md` for the
full picture (architecture, API table, demo flow, security notes).

## Setup

```bash
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure `backend/.env` (template: `.env.example`):

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_support
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
RAG_MAX_DISTANCE=0.35
AUTH_USERNAME=operator
AUTH_PASSWORD=use_a_long_unique_password
AUTH_SECRET_KEY=use_at_least_32_random_bytes
AUTH_COOKIE_SECURE=false  # local HTTP only; set true behind HTTPS
```

```bash
docker compose up -d db         # set POSTGRES_PASSWORD in the root .env first
alembic upgrade head
python -m scripts.seed_data     # adds the small demo dataset idempotently
python -m scripts.seed_demo_scale # optional: 100 synthetic customers + 300 tickets
uvicorn app.main:app --reload
```

## Tests

```bash
.venv\Scripts\python.exe -m pytest -q
```

Notes:

* Requires the database up and migrated; several tests use real PostgreSQL
  sessions. For local runs, use a dedicated test database in `DATABASE_URL`.
* Unit tests mock Gemini. A few tests call the live API and return `429`
  while the free-tier quota is exhausted — that is an environment limit.
* Set unique auth credentials in `backend/.env`; protected business routes fail
  closed until configured. The frontend signs in at `/api/v1/auth/login`.
  `AUTH_COOKIE_SECURE=false` is for local HTTP only; deployments must set it to
  `true` and serve the app over HTTPS.
* `alembic check` must report "No new upgrade operations detected".
