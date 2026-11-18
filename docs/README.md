# SplitEase — Group Expense Splitting (Flutter + FastAPI + PostgreSQL)

Split shared expenses with friends, flatmates and trips. Add an expense once, split it four ways (equal, exact, percentage, shares), and SplitEase tells everyone who owes whom with the **fewest payments**.

> All money is stored as **integer paise** and every split sums to the bill **exactly**: no lost or extra paisa.

## Docs index

Read in this order. Each file has one job.

| File | What it covers |
|---|---|
| [PRD.md](PRD.md) | Product requirements: problem, users, features, scope, success criteria |
| [TRD.md](TRD.md) | Technical requirements: stack, algorithms, business rules, performance, config |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram, backend and app layers, folder structure, key decisions |
| [DB_SCHEMA.md](DB_SCHEMA.md) | Tables, constraints, indexes, Row Level Security policies |
| [API_SPEC.md](API_SPEC.md) | Every REST endpoint: request/response shapes, errors, pagination |
| [APP_FLOW.md](APP_FLOW.md) | Screens, navigation and user journeys |
| [UI_UX.md](UI_UX.md) | Design system, screen layouts, states, interactions |
| [SECURITY.md](SECURITY.md) | Auth, authorization, RLS, secrets, threat model |
| [TESTING.md](TESTING.md) | Test strategy, required tests, worked examples, manual QA |
| [ROADMAP.md](ROADMAP.md) | Step-by-step build plan with ready-to-paste Claude Code prompts |
| [CLAUDE.md](../CLAUDE.md) | Rules for Claude Code in this repo (lives at the repo root) |

## Tech stack (summary)

**App:** Flutter 3.50 · Dart 3.14 · Riverpod · Dio · go_router · supabase_flutter (auth only)
**Backend:** Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Alembic · PyJWT · pytest · Hypothesis
**Data & auth:** Supabase (PostgreSQL + Auth) · Row Level Security
**Hosting:** Render (free web service, Docker)

## Repo layout

```
splitease/
  CLAUDE.md
  docs/        ← these files
  backend/     ← FastAPI service
  app/         ← Flutter app
  .github/workflows/
```

## Quick start (once the code exists)

```bash
# backend
cd backend
cp .env.example .env            # fill in DATABASE_URL, SUPABASE_URL
docker compose up -d db         # local Postgres for dev/tests
alembic upgrade head
uvicorn app.main:app --reload
pytest

# app
cd app
flutter pub get
flutter run -d chrome --profile --dart-define-from-file=env.json
flutter test
```
