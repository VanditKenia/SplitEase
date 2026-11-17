# CLAUDE.md — Instructions for Claude Code

You are helping build **SplitEase**, a group expense-splitting app: Flutter app + FastAPI backend + Supabase (PostgreSQL + Auth). The developer is learning while building and must be able to explain every line in a job interview.

## Source of truth

Docs live in `docs/`. Read the relevant ones before each step:
PRD.md · TRD.md · ARCHITECTURE.md · DB_SCHEMA.md · API_SPEC.md · APP_FLOW.md · UI_UX.md · SECURITY.md · TESTING.md · ROADMAP.md

If code and docs disagree, ask before changing either.

## How to work

1. Build **only the current ROADMAP step**. Don't jump ahead or add unrequested features.
2. Keep changes small and readable. Clear code over clever code.
3. After each step:
   - backend: `ruff check .` and `pytest -q`; app: `flutter analyze` and `flutter test`
   - summarise files created/changed
   - **explain the key concepts in simple terms**
   - suggest the commit message from ROADMAP.md
4. Commit only when asked; **never push unless asked**.
5. Never run two Flutter commands at once (e.g. `flutter test` while `flutter run` is active).

## Hard rules — money

- **Money is always integer paise** (`int` in Dart/Python, `BIGINT` in SQL). Never `float`/`double`/`numeric` for amounts.
- Percentages are integer **basis points** (100% = 10000).
- Every split must sum **exactly** to the expense amount using the **largest-remainder** method (TRD.md §3). Deterministic tie-breaks by participant order.
- All balances in a group must sum to zero. Tests must prove both invariants (Hypothesis).

## Hard rules — backend

- Layers: `api/` (HTTP only) → `services/` (rules + authorization) → `repositories/` (SQL only). `domain/` is pure Python with no app imports.
- Every service method touching a group checks membership first. Return **404** (not 403) for groups the caller can't see.
- SQL only through SQLAlchemy with bound parameters. No string-built SQL.
- Errors use the format in API_SPEC.md §1.
- Never log tokens, Authorization headers, passwords, or full request bodies of auth calls.
- Tests never call real Supabase: use a test key pair + JWKS dependency override, and the docker-compose test database.
- Schema changes only through Alembic migrations (including RLS policies).

## Hard rules — app

- Always import `package:material_ui/material_ui.dart`, never `package:flutter/material.dart` (deprecated since Flutter 3.47).
- UI never calls Dio or Supabase directly: screens → providers → repositories → ApiClient / AuthService.
- Supabase is used **only for auth** in the app; all data goes through our API.
- Riverpod `Notifier`/`AsyncNotifier` (no legacy StateNotifier).
- Config only via `--dart-define-from-file=env.json`; only public values (API URL, Supabase URL, publishable key). **Never** a service_role/secret key or DB URL in the app.
- Use `FontFeature.tabularFigures()` for amounts; format with `en_IN` (`₹1,23,456.50`).
- Every data screen handles loading / empty / error / offline states.

## Secrets

- `backend/.env` and `app/env.json` are gitignored; commit only `.env.example` / `env.example.json`.
- Before committing, check the staged diff has no DB URL with a password, `sb_secret_`, or `service_role`.

## Conventions

- Python: snake_case, type hints everywhere, ruff formatting.
- Dart: files `snake_case.dart`, classes `PascalCase`, providers end with `Provider`.
- Tests mirror source structure (`backend/tests/...`, `app/test/...`).
- Commit style: `feat(scope):`, `fix:`, `chore:`, `docs:`, `test:`, `ci:`.

## Commands

```bash
# backend
cd backend
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
ruff check . && pytest -q

# app
cd app
flutter pub get
flutter run -d chrome --profile --dart-define-from-file=env.json
flutter analyze && flutter test
```
