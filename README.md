# Quiz Platform

A full-stack, multi-tenant online quiz platform built with **FastAPI** and **React**. Organizations host admins who create question banks, build quizzes, and monitor student attempts in real time, while students take timed, proctored quizzes and review their results and analytics.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [Setup Instructions](#4-setup-instructions)
5. [Seed Data](#5-seed-data)
6. [Bulk Question Import](#6-bulk-question-import)
7. [User Roles](#7-user-roles)
8. [Major Features](#8-major-features)
9. [Testing](#9-testing)
10. [Deployment](#10-deployment)
11. [API Overview](#11-api-overview)
12. [Known Limitations](#12-known-limitations)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Project Overview

The Quiz Platform is a multi-tenant web application where multiple independent organizations each manage their own admins, question banks, quizzes, and student attempts in complete isolation.

### Key Features

- **Multi-tenant organization isolation** — data from one organization is never accessible to another
- **Question Banks** — reusable pools of multiple-choice questions with marks and negative marking
- **Bulk Question Import** — CSV and JSON file upload with partial-success reporting and row-level errors
- **Quiz Builder** — assign questions from banks to quizzes with optional per-question marks overrides
- **Quiz Publishing** — quizzes are hidden from students until explicitly published; optional time windows
- **Timed Quiz Attempts** — server-enforced countdown with automatic timeout handling
- **Anti-Cheat / Proctoring** — tab switch counting, window blur, copy-paste, and fullscreen exit events
- **Attempt auto-abandon** — configurable max tab switch threshold auto-abandons the attempt
- **Analytics** — per-quiz aggregate stats, per-question difficulty ranking, and student personal history
- **Admin Dashboard** — platform snapshot with attempt counts, anti-cheat totals, and recent activity
- **JWT Authentication** — short-lived access tokens with rotating refresh tokens
- **Interactive Swagger docs** — available at `/docs` in development mode

---

## 2. Tech Stack

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 19 with TypeScript 6 |
| Build tool | Vite 8 |
| UI library | Material UI (MUI) v9 with Emotion |
| Data grid | MUI X DataGrid v9 |
| State / data fetching | TanStack React Query v5 |
| HTTP client | Axios v1 |
| Routing | React Router v7 |

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 |
| Runtime | Python 3.11 (Dockerized) |
| ORM | SQLAlchemy 2.0 (async) |
| DB driver | asyncpg 0.29 |
| Migrations | Alembic 1.13 |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT), bcrypt |
| Server | Uvicorn with standard extras |

### Database

| Component | Technology |
|---|---|
| Engine | PostgreSQL 15 |
| Local container | Docker (`postgres:15-alpine`) |
| Production | Neon (serverless PostgreSQL) |

### Infrastructure / Deployment

| Component | Technology |
|---|---|
| Container orchestration | Docker Compose |
| Frontend hosting | Vercel |
| Backend hosting | Render |
| Database hosting | Neon |

---

## 3. Architecture Overview

```
Quiz Platform
├── frontend/          React SPA (Vite)
│   ├── src/api/       Axios client, typed endpoints, API functions
│   ├── src/hooks/     React Query hooks (one file per domain)
│   ├── src/pages/     admin/ and student/ page components
│   ├── src/components/
│   │   ├── admin/     Admin-specific dialogs and forms
│   │   └── common/    Shared UI primitives
│   └── src/context/   AuthContext (JWT storage + refresh)
│
└── backend/           FastAPI application
    ├── app/api/v1/    Route handlers (one file per resource group)
    ├── app/services/  Business logic (QuizService, AttemptService, etc.)
    ├── app/models/    SQLAlchemy ORM models
    ├── app/schemas/   Pydantic request/response schemas
    ├── app/repositories/ Async data-access layer
    └── alembic/       Database migration scripts
```

### Frontend Structure

- **Pages** are split into `admin/` (question banks, quiz builder, attempts oversight, analytics) and `student/` (available quizzes, attempt flow, results, personal analytics).
- **React Query hooks** (`useQuestions.ts`, `useQuizzes.ts`, `useAttempts.ts`, etc.) own all server state. Components never call `axios` directly.
- **AuthContext** holds the current user, persists tokens to `localStorage`, and handles transparent token refresh.

### Backend Structure

- **Routes** in `app/api/v1/` are thin — they validate inputs via Pydantic, call a service method, and map exceptions to HTTP status codes.
- **Services** contain all business logic. `QuizService` owns question banks, questions, and quizzes. `AttemptService` owns the full attempt lifecycle including proctoring. `AnalyticsService` owns all reporting queries.
- **Repository pattern** — every service receives an `AsyncSession` and uses a typed repository class for all DB access. This keeps SQL out of services and makes unit testing straightforward.

### Multi-Tenant Organization Model

- Every **admin** belongs to exactly one organization (`organization_id` on the `users` table).
- Every **question bank**, **question**, and **quiz** belongs to an organization and can only be accessed by an admin from that same organization.
- **Students** are not scoped to an organization — they can attempt any published quiz.
- Cross-tenant access attempts return `404` (indistinguishable from "not found") rather than `403`, per the platform's tenant boundary rules. This prevents information leakage about other organizations' resources.
- The `require_admin_with_org` FastAPI dependency enforces both admin role and non-null `organization_id` on every write route.

---

## 4. Setup Instructions

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- [Node.js 20+](https://nodejs.org/) — for local frontend development only
- [Python 3.11+](https://www.python.org/) — for running backend tests locally only

### Environment Variables

Copy `.env.example` to `.env` in the project root and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | `quiz_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | *(set this)* |
| `POSTGRES_DB` | Database name | `quiz_db` |
| `POSTGRES_HOST` | DB hostname (use `db` inside Docker) | `db` |
| `POSTGRES_PORT` | DB port | `5432` |
| `DATABASE_URL` | Full asyncpg connection string | *(derived from above)* |
| `BACKEND_PORT` | Port the backend container exposes | `8000` |
| `APP_ENV` | `development` enables Swagger UI | `development` |
| `SECRET_KEY` | JWT signing secret — **change in production** | *(set this)* |

Example `.env`:
```env
POSTGRES_USER=quiz_user
POSTGRES_PASSWORD=quiz_password
POSTGRES_DB=quiz_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://quiz_user:quiz_password@db:5432/quiz_db
BACKEND_PORT=8000
APP_ENV=development
SECRET_KEY=change-this-to-a-long-random-string-in-production
```

### Running the Full Stack (Docker)

```bash
# From the project root
docker compose up --build
```

This starts:
- `db` — PostgreSQL 15 on port `5432`
- `backend` — FastAPI on port `8000` (with `--reload` for development)

The backend volume-mounts `./backend` into `/app` so code changes hot-reload without rebuilding.

### Applying Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### Running the Frontend (local dev)

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server starts on `http://localhost:5173` by default. The `VITE_API_URL` in `frontend/.env` controls which backend it points to.

```env
# frontend/.env
VITE_API_URL=http://localhost:8000
```

### Running Backend Tests Locally

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

---

## 5. Seed Data

A fully deterministic, idempotent seed script is provided at `backend/seed.py`. Re-running it any number of times produces the same database state with no duplicate rows.

### Run the Seed

```bash
docker compose exec backend python seed.py
```

### Verify Without Inserting

```bash
docker compose exec backend python seed.py --verify
```

### Seed Structure

| Entity | Count | Details |
|---|---|---|
| Organizations | 2 | Alpha Tech Academy, Beta Engineering Institute |
| Admins | 2 | One per organization |
| Students | 20 | `student01` through `student20` |
| Question Banks | 4 | 2 per organization |
| Questions | 24 | 6 per bank, CS/AI interview-style |
| Quizzes | 4 | 2 per organization, all published, 6 questions each |

### Admin Credentials

| Organization | Email | Password |
|---|---|---|
| Alpha Tech Academy | `admin@alpha.dev` | `Alpha@Admin123!` |
| Beta Engineering Institute | `admin@beta.dev` | `Beta@Admin123!` |

### Student Credentials

All 20 students share the same password:

| Email pattern | Password |
|---|---|
| `student01@example.com` … `student20@example.com` | `Student@Pass123!` |

### Question Bank Topics

**Alpha Tech Academy**
- *DSA & Programming* — QuickSort complexity, Python `dict` internals, `__slots__`, merge sort, generators, C++ `new` vs `malloc`
- *AI / Machine Learning* — vanishing gradients, LLM temperature, RAG, ReAct agents, F1/AUROC, vector databases

**Beta Engineering Institute**
- *Data Engineering & Databases* — `EXPLAIN ANALYZE`, 3NF, Kafka consumer groups, OLTP vs OLAP, `HAVING`, surrogate keys
- *System Design & Cloud* — CAP theorem, Docker `ENTRYPOINT`, HTTP 201, message queues, horizontal scaling, Kubernetes Service

---

## 6. Bulk Question Import

Admins can import multiple questions at once from a CSV or JSON file via the **Import** button on the Questions page, or directly via the API.

**Endpoint:** `POST /api/v1/question-banks/{bank_id}/import`
**Auth:** Admin JWT required
**Body:** `multipart/form-data` with fields `file` and `format`
**Max rows:** 500 per request

### Supported Formats

| Format | `format` field value |
|---|---|
| CSV | `csv` |
| JSON | `json` |

### CSV Schema

The CSV must have a header row with these exact columns (order does not matter, case-insensitive):

```
text, explanation, marks, negative_marks, option_a, option_b, option_c, option_d, correct_option
```

| Column | Required | Description |
|---|---|---|
| `text` | Yes | Question text (non-empty string) |
| `explanation` | No | Explanation shown after submission |
| `marks` | Yes | Positive decimal — marks awarded for correct answer |
| `negative_marks` | Yes | Non-negative decimal — marks deducted for wrong answer |
| `option_a` … `option_d` | Yes | Text for each of the four options |
| `correct_option` | Yes | `A`, `B`, `C`, or `D` (case-insensitive) |

### Example CSV

```csv
text,explanation,marks,negative_marks,option_a,option_b,option_c,option_d,correct_option
"What is the time complexity of binary search?","Divides search space in half each step.",1,0.25,"O(n)","O(log n)","O(n²)","O(1)","B"
"Which Python keyword creates a generator?","yield suspends execution and returns a value.",1,0.25,"return","yield","async","lambda","B"
"What does DNS stand for?","Translates domain names to IP addresses.",1,0.25,"Dynamic Name Service","Domain Name System","Distributed Network Service","Data Node Server","B"
```

### Example JSON

The JSON body must be an array of objects. Each object uses the same field names as the `QuestionCreate` schema:

```json
[
  {
    "text": "What is the worst-case time complexity of QuickSort?",
    "explanation": "Occurs when the pivot is always the min or max element.",
    "marks": 2,
    "negative_marks": 0.5,
    "options": [
      { "text": "O(n log n)", "is_correct": false },
      { "text": "O(n²)",      "is_correct": true  },
      { "text": "O(n)",       "is_correct": false },
      { "text": "O(log n)",   "is_correct": false }
    ]
  }
]
```

### Response Format

The endpoint always returns `200 OK` with a partial-success body:

```json
{
  "imported": 2,
  "failed": 1,
  "errors": [
    { "row": 3, "field": "marks", "message": "Input should be greater than 0" }
  ]
}
```

- `imported` — number of rows successfully inserted
- `failed` — number of rows that had at least one validation error
- `errors` — one entry per failing field per row; multiple errors per row are all reported

### Common Validation Errors

| Error | Cause |
|---|---|
| `String should have at least 1 character` | Empty `text` field |
| `Input should be greater than 0` | `marks` is zero or negative |
| `Input should be greater than or equal to 0` | `negative_marks` is negative |
| `List should have at least 4 items` | Fewer than 4 options provided |
| `Exactly one option must be marked correct` | Zero or more than one correct option |
| `correct_option must be A, B, C, or D` | Invalid letter in CSV `correct_option` column |
| `Import exceeds maximum of 500 rows` | File has more than 500 data rows |
| `Uploaded file is empty` | Zero-byte file uploaded |

---

## 7. User Roles

There are two roles: `admin` and `student`. Role is set at registration and cannot be changed through the API.

### Admin Permissions

Admins must belong to an organization. All admin actions are scoped to their organization only.

- Create, read, update, delete **question banks**
- Create, read, update, delete **questions** within owned banks
- **Bulk import** questions from CSV or JSON
- Create, read, update, delete **quizzes**
- Assign and remove questions from quizzes (with optional per-question marks override)
- Reorder questions within a quiz
- **Publish** and **unpublish** quizzes
- View all **student attempts** for their organization's quizzes (filterable by quiz, student, status)
- View the full **audit trail** (tab switch log) for any attempt
- Access per-quiz and per-question **analytics**
- Access the **admin dashboard** (platform snapshot)

### Student Permissions

Students are not scoped to any organization and can see all published quizzes across all organizations.

- Register and log in
- Browse currently available (published, within time window) quizzes
- Start or resume a quiz attempt
- Save answers (auto-save on every selection)
- Submit a quiz attempt
- View the graded result of any completed attempt
- View personal attempt history (paginated, filterable by status)
- View personal analytics summary (total attempts, averages, status breakdown)

---

## 8. Major Features

### Question Banks

Question banks are organizational containers for multiple-choice questions. Each bank belongs to an organization and can only be accessed by that organization's admins. Banks can be created, renamed, described, and deleted. A bank cannot be deleted while questions in it are referenced by a quiz.

### Question Management

Each question has:
- Question text
- Optional explanation (shown to students after submission)
- Marks (positive decimal)
- Negative marks (non-negative decimal)
- Exactly 4 options, exactly 1 of which is marked correct

Questions can be created individually via the form dialog or imported in bulk via CSV/JSON. Questions are listed in a data grid with text preview, marks, and created date.

### Quiz Builder

The Quiz Builder page (`/admin/quizzes/:id/builder`) allows admins to:
- View quiz metadata (title, duration, published status, time window)
- Add questions from any bank in their organization via a picker dialog
- Set a per-question marks override (overrides the question's default marks for this quiz only)
- Reorder questions using up/down arrow buttons
- Remove individual questions
- Publish or unpublish the quiz

A **readiness checklist** is shown before publishing — the quiz must have a title, a duration, and at least one question assigned.

### Quiz Publishing

An unpublished quiz is invisible to students. Publishing requires at least one question to be assigned. A published quiz can be unpublished at any time. If a time window (`start_time`, `end_time`) is set, students can only start attempts within that window.

### Quiz Attempts

The attempt flow:
1. Student starts an attempt (`POST /api/v1/attempts/start`) — server validates published status, time window, and attempt limit.
2. A snapshot of the quiz questions is taken at start time, stored in `attempt_questions`. This means question edits after an attempt starts do not affect in-progress attempts.
3. Student saves answers one at a time; each save is an upsert (safe to call on every keypress / option click).
4. Student submits (`POST /api/v1/attempts/{id}/submit`) — server grades all answers, calculates score (marks for correct, minus negative_marks for incorrect, floored at 0), and returns the full result.
5. If the timer expires before submission, the attempt is automatically marked `timed_out` on the next server interaction.

Attempt statuses: `in_progress` → `submitted` / `timed_out` / `abandoned`.

### Anti-Cheat Monitoring

The platform implements browser-observable proctoring:

- **Tab switches** — tracked via the Visibility API. Each switch increments `tab_switch_count`. If `max_tab_switches` is configured and exceeded, the attempt is automatically abandoned.
- **Window blur** — logged when the browser window loses focus.
- **Copy-paste** — logged when clipboard events fire during an attempt.
- **Fullscreen exit** — logged when the browser exits fullscreen mode.

All proctoring events are stored immutably in the `proctoring_events` audit table and are visible to admins via the attempt audit view.

### Analytics

**Student analytics** (`GET /api/v1/analytics/me`):
- Total attempts, breakdown by status
- Paginated personal attempt history with quiz title, score, and timestamps

**Admin quiz analytics** (`GET /api/v1/analytics/quizzes/{quiz_id}`):
- Total attempts, status breakdown (submitted/timed_out/abandoned rates)
- Average score, total tab switches, total proctoring events

**Admin per-question analytics** (`GET /api/v1/analytics/quizzes/{quiz_id}/questions`):
- Correct/incorrect/unanswered percentages per question
- Difficulty ranking across questions in the quiz

**Admin dashboard** (`GET /api/v1/analytics/admin/dashboard`):
- Organization-wide user counts, quiz counts, attempt status breakdown
- Anti-cheat totals
- 10 most recent attempts with student and quiz names

### Multi-Tenant Organization Isolation

Organization isolation is enforced at every layer:

- **Dependency injection** — `require_admin_with_org` guarantees every admin route has a non-null `organization_id`.
- **Repository layer** — all data lookups are scoped queries (`WHERE organization_id = $1`). There are no unscoped admin queries.
- **Error handling** — a cross-tenant access attempt returns `404`, not `403`, to avoid leaking the existence of resources belonging to other organizations.
- **Attempt scoping** — admin attempt queries filter by the admin's `organization_id`, so admins only see attempts on their own quizzes.

---

## 9. Testing

### Running Backend Tests

```bash
# Inside Docker (recommended)
docker compose exec backend pytest -v

# Locally (requires requirements-dev.txt installed)
cd backend
pytest -v
```

Run only the bulk import tests:
```bash
docker compose exec backend pytest tests/test_bulk_import.py -v
```

### Test Files

| File | Coverage |
|---|---|
| `test_bulk_import.py` | CSV/JSON import, partial failure, row-level errors, tenant isolation, row limit (25 tests) |
| `test_organization_isolation.py` | Cross-tenant access attempts return LookupError |
| `test_quiz_service.py` | `update_quiz`, `publish_quiz`, `update_question_bank` |
| `test_attempt_scoring.py` | Score calculation, marks override, negative marking |
| `test_analytics_service.py` | Dashboard, quiz analytics, per-question analytics, student history |
| `test_auth_service.py` | Registration, login, token refresh, logout |
| `test_proctoring_events.py` | Event logging, tab switch auto-abandon, timeout enforcement |
| `test_quiz_browsing.py` | Available quiz filtering (time window, published status) |
| `test_password.py` | Password strength validation rules |

### Current Test Status

```
tests/test_bulk_import.py          25 passed
tests/test_organization_isolation.py  passed
tests/test_quiz_service.py            passed
tests/test_analytics_service.py       passed
tests/test_proctoring_events.py       passed
tests/test_quiz_browsing.py           passed
tests/test_attempt_scoring.py      4 pre-existing failures (AsyncMock session.add issue)
tests/test_password.py             3 pre-existing failures (any() misuse in assertions)
tests/test_auth_service.py         requires .env (skipped without database)
```

> The 7 pre-existing failures are in unrelated test files and do not affect any feature implemented in the current development phase.

---

## 10. Deployment

### Frontend — Vercel

The frontend is deployed to Vercel. `vercel.json` configures a catch-all rewrite to `index.html` to support client-side routing.

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**Required Vercel environment variable:**

| Variable | Value |
|---|---|
| `VITE_API_URL` | URL of your deployed backend, e.g. `https://your-app.onrender.com` |

### Backend — Render

Deploy the `backend/` directory as a Python web service. The `Dockerfile` is provided.

**Required environment variables on Render:**

| Variable | Description |
|---|---|
| `DATABASE_URL` | Full `postgresql+asyncpg://...` connection string (from Neon) |
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |
| `SECRET_KEY` | Long random string for JWT signing |
| `APP_ENV` | Set to `production` to disable Swagger UI |
| `CORS_ORIGINS` | JSON array of allowed origins, including your Vercel URL |

**Start command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Run migrations on deploy:**
```bash
alembic upgrade head
```

### Database — Neon

Provision a Neon PostgreSQL database and copy the connection string into `DATABASE_URL`. Use the `postgresql+asyncpg://` scheme (not `postgresql://`).

---

## 11. API Overview

All routes are prefixed with `/api/v1`. Interactive docs are at `http://localhost:8000/docs` when `APP_ENV=development`.

### Authentication Flow

```
POST /api/v1/auth/register    Register a new user → returns access + refresh tokens
POST /api/v1/auth/login       Login → returns access + refresh tokens
POST /api/v1/auth/refresh     Rotate refresh token → returns new token pair
POST /api/v1/auth/logout      Revoke refresh token
GET  /api/v1/auth/me          Get current user info
```

Tokens are passed as `Authorization: Bearer <access_token>`. Access tokens are short-lived (15 minutes by default). Use the refresh token to obtain a new pair before expiry.

### Endpoint Groups

| Prefix | Auth | Description |
|---|---|---|
| `/api/v1/auth` | Public / Bearer | Registration, login, token management |
| `/api/v1/question-banks` | Admin | CRUD for question banks and their questions; bulk import |
| `/api/v1/questions` | Admin | Cross-bank question listing |
| `/api/v1/quizzes` | Admin + Student | Quiz CRUD (admin); available quiz listing (student) |
| `/api/v1/attempts` | Student | Start, answer, submit, and review attempts; proctoring events |
| `/api/v1/admin/attempts` | Admin | View and audit all attempts for the organization |
| `/api/v1/analytics` | Admin + Student | Dashboard and quiz analytics (admin); personal history (student) |
| `/api/v1/health` | Public | Liveness check |

### Key Route Reference

```
# Question banks
GET    /api/v1/question-banks
POST   /api/v1/question-banks
GET    /api/v1/question-banks/{bank_id}
PUT    /api/v1/question-banks/{bank_id}
DELETE /api/v1/question-banks/{bank_id}
GET    /api/v1/question-banks/{bank_id}/questions
POST   /api/v1/question-banks/{bank_id}/questions
POST   /api/v1/question-banks/{bank_id}/import

# Quizzes
GET    /api/v1/quizzes
POST   /api/v1/quizzes
GET    /api/v1/quizzes/{quiz_id}
PUT    /api/v1/quizzes/{quiz_id}
POST   /api/v1/quizzes/{quiz_id}/publish
POST   /api/v1/quizzes/{quiz_id}/unpublish
GET    /api/v1/quizzes/{quiz_id}/questions
POST   /api/v1/quizzes/{quiz_id}/questions
DELETE /api/v1/quizzes/{quiz_id}/questions/{question_id}
GET    /api/v1/quizzes/available

# Attempts (student)
POST   /api/v1/attempts/start
POST   /api/v1/attempts/{attempt_id}/answers
POST   /api/v1/attempts/{attempt_id}/submit
GET    /api/v1/attempts/{attempt_id}/result
POST   /api/v1/attempts/{attempt_id}/tab-switch
POST   /api/v1/attempts/{attempt_id}/proctoring-event

# Admin oversight
GET    /api/v1/admin/attempts
GET    /api/v1/admin/attempts/{attempt_id}/audit

# Analytics
GET    /api/v1/analytics/me
GET    /api/v1/analytics/me/history
GET    /api/v1/analytics/quizzes/{quiz_id}
GET    /api/v1/analytics/quizzes/{quiz_id}/questions
GET    /api/v1/analytics/admin/dashboard
```

---

## 12. Known Limitations

- **Results page search is limited to the most recent 100 attempts.** `ResultsPage.tsx` fetches with `limit=100` and filters client-side. Students with more than 100 attempts will not see older ones in the search results. This is a known frontend limitation — the backend supports arbitrary pagination.

- **Quiz question reordering uses a remove-and-re-add workaround.** The `useMoveQuizQuestionMutation` hook removes the question at the old position and re-adds it at the new position, which creates a new `quiz_question` row. This means `marks_override` values are lost when a question is moved via the up/down buttons in the Quiz Builder.

- **Marks override cannot be edited after assignment.** Once a question is assigned to a quiz with a marks override, the override can only be changed by removing and re-adding the question. There is no `PATCH /quizzes/{id}/questions/{qid}` endpoint.

- **Available quizzes are not organization-scoped for students.** `GET /api/v1/quizzes/available` returns published quizzes from all organizations. Students can see and attempt quizzes from every organization on the platform.

- **No password reset flow.** There is no forgot-password or email verification system. Accounts can only be accessed with the original credentials.

- **Admin dashboard `recent_attempts` is capped at 10.** The dashboard always returns the 10 most recent attempts; there is no way to paginate through them from the dashboard endpoint.

- **`APP_ENV` guards Swagger docs only.** Setting `APP_ENV=production` disables `/docs` and `/redoc` but does not change any other behaviour (e.g., logging verbosity, error detail level).

- **No soft delete.** All deletes are hard deletes. Deleting a question bank, question, or quiz is permanent and immediate, subject to `RESTRICT` foreign key constraints.

---

## 13. Future Enhancements

The following features are not implemented but have been identified as natural extensions of the current system:

- **Quiz assignments** — assign specific quizzes to specific students or groups rather than making them globally available to all students.
- **Leaderboard** — ranked view of student scores per quiz, with configurable visibility.
- **Certificates** — auto-generated PDF certificates for students who pass a quiz above a configurable score threshold.
- **Email notifications** — notify students when new quizzes are published, and admins when students submit attempts.
- **AI-generated questions** — generate multiple-choice questions from a topic prompt or a pasted passage using an LLM API, with admin review before saving to a bank.
- **Question tagging / search** — tag questions by topic or difficulty and filter question banks by tag.
- **Rich text questions** — support Markdown or LaTeX in question and option text for mathematical content.
- **CSV export** — allow admins to export attempt results and analytics as CSV for offline analysis.
- **Password reset** — self-service forgot-password flow with email verification.
- **Organization management UI** — admin interface for creating organizations and assigning admins, rather than requiring direct database or seed script access.
