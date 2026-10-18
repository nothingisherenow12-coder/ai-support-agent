# AI Support & Operations Agent

An AI-powered support and operations system. A support user asks natural-language
questions; the system routes them to a grounded knowledge base (RAG), structured
customer/ticket tools, or a controlled action workflow — where a write operation
requires explicit human approval before the database changes.

Core principle:

```text
AI proposes. Human approves. Backend executes.
```

The LLM never gets unrestricted database access. It works through explicitly
defined application tools, and write tools run only after approval.

---

## Architecture

```text
  React UI (Vite + TypeScript)
  │  REST (CORS: http://localhost:5173)
  ▼
FastAPI
  ├── POST /api/v1/chat ──► AI Orchestrator ──┬── Knowledge → RAG answer + sources
  │                                            ├── Data → allow-listed business tool
  │                                            └── Action → plan + persist proposal
  ├── POST /api/v1/documents/upload (PDF → chunks → embeddings)
  ├── POST /api/v1/knowledge/query (direct RAG query)
  ├── GET  /api/v1/customers/{id}[ /tickets]
  └── /api/v1/actions ──► propose / list / approve / reject / execute
                            │
                     PostgreSQL + pgvector
```

Mermaid version of the request flow:

```mermaid
flowchart TD
    U[User message] --> C[POST /api/v1/chat]
    C --> I{Intent classifier}
    I -->|knowledge| R[pgvector similarity search]
    R --> G[Grounded Groq answer + sources]
    I -->|data| T[Tool selector → allow-listed tool → PostgreSQL]
    I -->|action| P[Action planner → saved proposal: proposed]
    P --> H{Human approval}
    H -->|approve| E[Executor: locked, approved-only, exactly-once ticket create]
    H -->|reject| X[Rejected: no DB change]
```

---

## Request routing

The AI classifies each message as `knowledge`, `data`, or `action`:

* **Knowledge** — e.g. `"What is our refund policy?"` → query embedding →
  pgvector cosine search → distance threshold (`RAG_MAX_DISTANCE=0.35`) →
  grounded Groq response with `{answer, sources, answerable}`.
  Insufficient evidence returns `answerable=false` and a fixed fallback sentence.
* **Data** — e.g. `"Show me the tickets for customer 1."` → tool selector picks
  one of `get_customer | get_customer_tickets | get_ticket | list_open_tickets` →
  validated backend execution → structured result. No SQL from the LLM.
* **Action** — e.g. `"Create a support ticket for customer 1 …"` → planner builds
  an `ActionProposal` (currently only `create_ticket`) → persisted with
  `status=proposed` → returned with `action_id` and `requires_approval=true`.

## RAG pipeline

```text
PDF upload → suffix check → pypdf extraction → cleaning → chunking (1000/200)
→ Gemini embeddings (RETRIEVAL_DOCUMENT, 768-d) → PostgreSQL + pgvector
```

Query time: `RETRIEVAL_QUERY` embedding → cosine-distance top-k →
threshold filter → strict grounded prompt (context-only, no outside knowledge)
→ JSON-schema-validated answer + per-chunk sources
`{document_id, filename, chunk_id, chunk_index, distance}`.

## Action safety model

```text
PROPOSED → APPROVED → EXECUTED   (execute allowed only from APPROVED)
PROPOSED → REJECTED               (terminal; never executes)
```

Enforced in backend code, not in prompts:

* `save_action_proposal` rejects unknown `customer_id` values at propose time (400).
* `approve_action` re-validates the customer exists (409 on violation).
* `execute_action(action_id)` locks the row (`SELECT … FOR UPDATE`), requires
  status `approved` (else 409), creates the ticket and flips to `executed` in
  **one transaction** — a ticket-creation failure rolls everything back and the
  action stays `approved` (retryable, never falsely `executed`).
* Re-execution and execution of proposed/rejected actions return 409.
* `create_ticket` (write tool) flushes without committing; the caller owns commit,
  so execution is atomic.

---

## API routes

| Method & path | Purpose |
|---|---|
| `GET /api/v1/health` | Liveness + DB readiness (`database: ok/unreachable`) |
| `POST /api/v1/auth/login` | Sign in and receive an HttpOnly session cookie |
| `GET /api/v1/auth/session` | Check the current session |
| `POST /api/v1/auth/password` | Change password; revokes other sessions |
| `POST /api/v1/auth/logout` | Clear the session cookie |
| `POST /api/v1/chat` `{message, context?}` | Unified orchestrator (knowledge / data / action); recent user prompts provide conversational context for knowledge queries |
| `POST /api/v1/documents/upload` | PDF upload (multipart `file`), returns `{id, filename, chunks_created}` |
| `GET /api/v1/documents` | List indexed documents (supports `limit`, maximum 500) |
| `DELETE /api/v1/documents/{id}` | Delete an indexed document and its chunks |
| `POST /api/v1/knowledge/query` `{question, top_k}` | Direct RAG query |
| `GET /api/v1/customers/{id}` | Customer record (404 if missing) |
| `POST /api/v1/customers` | Create a customer (name, unique email, optional company) |
| `GET /api/v1/customers?limit=&offset=&q=` | Paginated customer directory; response includes `items`, `total`, `limit`, `offset` |
| `GET /api/v1/customers/{id}/tickets?limit=&offset=` | Paginated customer tickets (404 if customer missing) |
| `GET /api/v1/tickets?limit=&offset=&status=&priority=&q=` | Paginated, filterable tickets |
| `POST /api/v1/imports/customers` | Preview/import customer CSV (`dry_run=false` to commit) |
| `POST /api/v1/imports/tickets` | Preview/import ticket CSV; stable `external_id` makes retries safe |
| `GET /api/v1/users` / `POST /api/v1/users` | Admin-only team directory and account creation |
| `GET /api/v1/audit` | Admin-only recent workspace audit events |
| `POST /api/v1/actions` | Save proposal → 201 `{…, status: proposed}` |
| `GET /api/v1/actions[?status=]` | List proposals, optional status filter |
| `GET /api/v1/actions/{id}` | Single proposal (404 if missing) |
| `POST /api/v1/actions/{id}/approve` | proposed → approved (409 on bad transition) |
| `POST /api/v1/actions/{id}/reject` | proposed → rejected (409 on bad transition) |
| `POST /api/v1/actions/{id}/execute` | approved → executed + ticket (409 otherwise) |

AI-provider failures are mapped: quota/429 → `503` (+ `Retry-After`), other
provider errors → `502`. No stack traces leak to clients.

Interactive docs: `http://localhost:8000/docs`.

---

## Technology stack

Backend: Python, FastAPI, Pydantic (Groq structured chat output), SQLAlchemy,
Alembic, PostgreSQL + pgvector, Groq chat, Gemini (`gemini-embedding-2`),
pypdf, pytest, httpx. Protected endpoints require a signed HttpOnly session cookie.
Frontend: React 19, TypeScript (strict), Vite 6, React Router 7, Tailwind CSS v4,
Axios, lucide-react. No Redux; local state + API modules under `src/api/`.

## Project structure

```text
backend/
  app/
    main.py                 # FastAPI app + CORS (localhost:5173) + router wiring
    core/config.py          # database, AI, session, upload and CORS settings
    db/                     # Base, engine, SessionLocal, get_db
    models/                 # Customer, Ticket, Document, DocumentChunk, Action
    schemas/                # customer, ticket, knowledge, document, action,
                            # intent, tool_call, orchestrator, chat
    services/               # parser, chunker, embedding, ingestion,
                            # document_service, retrieval, rag,
                            # intent_classifier, tool_selector, tool_executor,
                            # orchestrator, action_planner, action_service,
                            # action_executor, tools/{customer,ticket,write}_tools
    routers/                # health, auth, document, knowledge, customers, chat, actions
  alembic/versions/         # 6 migrations (customers, tickets, documents,
                            # embeddings, actions) — single head, check-clean
  scripts/seed_data.py      # 2 customers + 3 tickets (customer 1 = John Smith)
  tests/                    # backend regression and integration tests (see Testing)
frontend/
  src/
    api/                    # client, chat, knowledge, customers, actions
    components/             # layout, chat, knowledge, customers, actions, common
    pages/                  # Dashboard, Assistant, KnowledgeBase, Customers, Actions
    types/                  # action, chat, customer, knowledge
```

## Configuration

Backend `backend/.env` (see `backend/.env.example`; never committed):

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_support
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
RAG_MAX_DISTANCE=0.35
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
AUTH_USERNAME=operator
AUTH_PASSWORD=use_a_long_unique_password
AUTH_SECRET_KEY=use_at_least_32_random_bytes
AUTH_TOKEN_TTL_MINUTES=480
  AUTH_COOKIE_SECURE=false
```

Copy the root `.env.example` to `.env`. Set `POSTGRES_PASSWORD` there to the same password
used by `DATABASE_URL`. The database port binds to loopback only. Generate a
unique auth secret for each deployment; protected routes fail closed until all
three `AUTH_*` credentials are configured. The current sign-in supports one
operator account; use an identity provider for multi-user production deployments.

Frontend requests use same-origin `/api` paths by default. Vite proxies them to
`http://localhost:8000` during development. Set `VITE_API_BASE_URL` only when
the deployed API has a separate origin, and configure CORS to match.

For a separate API origin, `frontend/.env` may contain:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Local development

Requirements: Python 3.12+, Node.js + npm, Docker.

```bash
# 1. Copy .env.example to .env and set a strong POSTGRES_PASSWORD.
#    Use the same password in backend/.env DATABASE_URL.
# 2. Database (PostgreSQL 16 + pgvector)
docker compose up -d db

# 3. Backend (configure backend/.env from backend/.env.example)
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_data       # idempotent small demo dataset
python -m scripts.seed_demo_scale # optional: 100 synthetic customers + 300 tickets
uvicorn app.main:app --reload      # http://localhost:8000, docs at /docs

# 4. Frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

## Containerized workspace

Copy the root `.env.example` to `.env`, set a strong alphanumeric
`POSTGRES_PASSWORD`, and configure `backend/.env` with the same database
password plus fresh AI and authentication credentials. Then run:

```bash
docker compose up --build -d
```

Open `http://localhost:8080`. Nginx serves the built frontend, proxies API
requests to FastAPI, and rate-limits login attempts. The web and database ports
bind to loopback; the API is internal to the Compose network. This local stack
does not provision TLS. For a public deployment, terminate HTTPS at a trusted
edge proxy and enable `AUTH_COOKIE_SECURE=true`. Apply a login rate limit at the
public edge as well; if Nginx sits behind another proxy, configure trusted real
IP handling before relying on per-client Nginx limits.

## Testing

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q            # full suite (needs DB; live-AI tests need quota)
.venv\Scripts\python.exe -m pytest -q tests/test_actions_api.py tests/test_chat.py tests/test_rag.py
cd ../frontend
npm run typecheck && npm run build
```

Test strategy: Gemini is mocked in unit tests (deterministic, no quota burn).
A small set of tests exercises the live provider; they fail with `429` when the
free-tier quota is exhausted — an environment limit, not a code defect.
`test_rag.py` was converted from a live script into mocked tests for this reason.
Real-DB integration tests (actions lifecycle incl. concurrent-execution and
rollback cases) run against PostgreSQL. CI uses an ephemeral database; for local
runs, configure `DATABASE_URL` to a dedicated test database before running pytest.

## Recruiter demo flow

1. Dashboard → backend reachable.
2. Knowledge Base → upload a company PDF.
3. Assistant → `"What is our refund policy?"` → grounded answer + sources.
4. Assistant → `"Show me the tickets for customer 1."` → structured ticket cards.
5. Assistant → `"Create a support ticket for customer 1 about a billing problem."`
   → amber approval card (action persisted as `proposed`).
6. Approve the proposal, then choose **Execute approved action**; re-execution is refused (409).
7. Actions page → full queue with approve / reject / execute + history.

## Security & limitations (honest)

* Sign-in protects business API routes with expiring signed sessions. Configure
  strong deployment secrets, set `AUTH_COOKIE_SECURE=true`, and terminate TLS at
  the public edge. The container Nginx rate-limits login attempts; there is no
  multi-user identity provider or application-level rate limiter.
* CORS defaults to `http://localhost:5173` / `127.0.0.1:5173`; set explicit
  production origins.
* PDF uploads are limited to 20 MB, checked for a PDF signature, then parsed
  with pypdf. Malware scanning is not included; production deployments handling
  untrusted uploads should add scanning at the storage or edge layer.
* Secrets live in untracked `.env` files; `.env.example` files carry placeholders only.
* Gemini embedding calls have no explicit client timeout.
  (Axios uses 60s; backend relies on SDK defaults).
* Admin, agent, and viewer roles are enforced by the API. Admins can manage
  accounts, reset passwords, and review the audit log; agents can work tickets
  and chat; viewers have read-only access. Users can change their own password.
* Workspace chat history is stored per user. Audit events cover authentication,
  customer/ticket/document/action/user changes and bulk imports, but do not
  capture every read or retain chat message contents.
* Ticket CSV imports require a stable `external_id` to make retries idempotent.
  Customer emails are unique and existing rows are skipped.
* The project seed scripts create synthetic demo data. Do not treat it as real
  customer information or load it into a production workspace.

## Known pending work

* Login throttling is enforced by the bundled Nginx proxy. Directly exposing
  the API bypasses that limit; public deployments need an edge limit too.
* Ticket and customer lists use offset pagination. For very large or highly
  active workspaces, keyset pagination and measured database query tuning may
  be needed.
* Audit retention, off-host backup storage, and scheduled restore drills must
  be configured by the operator for the chosen hosting platform.
* Datetime columns are stored as naive UTC for compatibility; clients should
  treat them as UTC until a timezone-aware migration is introduced.
* There is no frontend unit-test suite yet; CI checks TypeScript and builds the
  production bundle.

## Backups and recovery

With the Docker Compose database running, create a custom-format backup:

```bash
python backend/scripts/backup_database.py
```

Restore only after stopping application writes and verifying the selected
backup. The restore script requires typing `RESTORE` because it replaces data:

```bash
python backend/scripts/restore_database.py backups/ai-support-YYYYMMDDTHHMMSSZ.dump
```

Backups contain customer and workspace data. Keep them encrypted and outside
GitHub, define a retention schedule, and periodically test restores on a
separate database before relying on them.

## Production launch checklist

Before opening the service to real users, rotate any credentials previously
shared in chat, provision fresh database and AI-provider credentials, set an
explicit production `CORS_ORIGINS`, and set `AUTH_COOKIE_SECURE=true`. Put the
loopback-bound Compose web service behind a TLS-enabled public edge proxy and
configure login throttling there. The repository does not include a domain,
certificate, cloud account, or hosting provider configuration. Apply migrations,
run CI, confirm backups and restore drills, and keep synthetic seed data out of
the production database.
