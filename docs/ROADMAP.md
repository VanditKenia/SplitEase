# Roadmap — Step-by-Step Build Plan

Build **one step at a time**. After each step: run the tests, read the code, ask Claude Code to explain anything unclear, then **commit** (and push when you choose).

**Minimum for the resume bullets:** Steps 0–12. Steps 13–14 make it shippable.

| # | Step | Area | Est. |
|---|---|---|---|
| 0 | Repo, Supabase project, local Postgres | setup | 45 min |
| 1 | Backend skeleton (FastAPI, config, DB, health, Docker) | backend | 45 min |
| 2 | Money + split algorithms + balances (pure, property-tested) | backend | 1 h |
| 3 | Database schema, indexes, RLS (Alembic) | backend | 1 h |
| 4 | Auth (JWT via JWKS) + `/me` | backend | 45 min |
| 5 | Groups, invite codes, membership guards | backend | 1 h |
| 6 | Expenses CRUD + idempotent create | backend | 1 h |
| 7 | Paginated, searchable feed + seed script | backend | 1 h |
| 8 | Balances, simplification, settlements | backend | 1 h |
| 9 | Flutter app setup + auth | app | 1 h |
| 10 | Groups UI (list, create, join, members) | app | 1 h |
| 11 | Add/edit expense with split editor | app | 1.5 h |
| 12 | Expense feed (pagination, search, filters) + balances/settle-up UI | app | 1.5 h |
| 13 | CI + deploy backend to Render | ops | 1 h |
| 14 | README, screenshots, APK release | ship | 1 h |

---

## Step 0 — Setup

**You:**
1. Create a GitHub repo **SplitEase** (public, no template files) and clone it to `C:\dev\SplitEase`.
2. Copy these docs into `docs/` and `CLAUDE.md` to the repo root.
3. Create a free **Supabase** project named `splitease` (region: Mumbai / `ap-south-1`). Note the project URL and publishable key; get the **session pooler** connection string (Project → Connect).
4. Auth → Providers → Email: enabled. For faster testing you may turn off "Confirm email" (turn it back on before release).
5. Check Docker Desktop is installed and running (`docker --version`). Python 3.12: `py -3.12 --version`.

**Claude Code prompt:**
> Read CLAUDE.md and every file in docs/. Set up the monorepo skeleton only: `backend/` and `app/` folders, root `.gitignore` covering Python, Flutter, `.env`, `env.json`, `.venv`, and a root README pointing to docs/. Don't write application code yet. Summarise the plan for Steps 1–14 in 10 lines.

Commit: `chore: repo skeleton and docs`

---

## Step 1 — Backend skeleton

> Implement Step 1 from docs/ROADMAP.md. In `backend/`: pyproject.toml (FastAPI, uvicorn, SQLAlchemy 2 async, asyncpg, alembic, pydantic-settings, PyJWT[crypto], httpx; dev: pytest, pytest-asyncio, hypothesis, ruff), `app/main.py` with CORS from settings and the error format from API_SPEC.md §1, `app/config.py` (pydantic-settings, TRD.md §8), `app/db.py` (async engine + session dependency; support `statement_cache_size=0` when using a transaction pooler), `app/errors.py` (AppError hierarchy → JSON errors), `GET /health`. Add `docker-compose.yml` with Postgres 16 for dev and a separate test database, a Dockerfile (non-root user, uvicorn), `.env.example`, Alembic initialised for async. Add a pytest setup with an ASGI httpx client and a test for /health. Run ruff and pytest. Explain the layering in ARCHITECTURE.md §2.

Commit: `feat(backend): FastAPI skeleton, config, db, health, docker`

---

## Step 2 — Money, splits, balances (pure domain)

> Implement Step 2. Create `backend/app/domain/money.py`, `splits.py`, `balances.py` exactly per TRD.md §2–4 (integer paise, largest-remainder method with deterministic tie-breaks, equal/exact/percentage/shares, typed errors, net balances, greedy simplify_debts with deterministic ties). No imports from the rest of the app. Write every test in TESTING.md §2 including the worked example and the Hypothesis property tests. Run them. Then explain the largest-remainder method and why greedy simplification isn't always optimal.

Commit: `feat(domain): paise money, split algorithms, balances with property tests`

---

## Step 3 — Schema, indexes, RLS

> Implement Step 3. Create SQLAlchemy models and an Alembic migration for every table in docs/DB_SCHEMA.md §1 with all constraints, the deferred constraint trigger that checks splits sum to the expense amount, the indexes in §2 (enable pg_trgm), and a second migration for RLS per §4 (enable RLS on all tables, revoke from anon, is_member() helper, member-only SELECT policies, no write policies). Make migrations run on both local Postgres and Supabase (guard `auth.users`/`auth.uid()` references so local tests work, e.g. create a minimal `auth` schema stub in the test DB only). Add tests: the split-sum trigger rejects a bad commit. Run `alembic upgrade head` locally and the tests. Tell me the exact command to run the migration against Supabase.

**You:** run the migration against Supabase, then open Supabase → Advisors → Security and confirm no RLS warnings.

Commit: `feat(db): schema, indexes and row level security`

---

## Step 4 — Auth + `/me`

> Implement Step 4 per docs/SECURITY.md §2 and API_SPEC.md §3. `app/auth.py`: verify the Supabase access token with PyJWKClient against `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (cached), checking exp, audience "authenticated" and issuer; support the legacy HS256 secret only if configured. A `current_user` dependency returning the user id + email. `GET/PATCH /v1/me` (create profile on first call). Tests use a locally generated key pair and a dependency override for the JWKS — never real Supabase. Cover: valid token, expired, wrong audience/issuer, wrong signature, missing header. Never log tokens.

Commit: `feat(backend): supabase jwt auth and profile endpoints`

---

## Step 5 — Groups

> Implement Step 5 per API_SPEC.md §4. Repositories + group_service with require_member/require_owner, invite codes (6 chars from the alphabet in DB_SCHEMA.md, retry on collision), join by code (case-insensitive, re-join clears left_at), rotate code (owner), leave (409 unless balance is zero — use the balance query from DB_SCHEMA.md §3; ownership transfer rule). Return 404 for groups the caller can't see. Rate-limit join to 10/min per user. Tests from TESTING.md §3 (groups + authorization).

Commit: `feat(backend): groups, invite codes and membership guards`

---

## Step 6 — Expenses

> Implement Step 6 per API_SPEC.md §5 (create, get, update, soft delete). expense_service validates payer/participants are current members, computes splits with domain.splits, and writes expense + splits in one transaction. Idempotent create using the client-generated id (TRD.md §6). Edit/delete only by creator or payer. Tests from TESTING.md §3 (expenses).

Commit: `feat(backend): expenses with four split types and idempotent create`

---

## Step 7 — Feed + seed

> Implement Step 7 per TRD.md §5 and API_SPEC.md §5 (GET list). Keyset pagination on (expense_date DESC, created_at DESC, id DESC) with an opaque base64url cursor, filters q (ILIKE on title/notes using the trigram index), paid_by, from/to, compact items with my_share_paise. Add `scripts/seed_expenses.py` (DB_SCHEMA.md §5). Add a timing log line per request (path + ms, no query values). Tests: walk all pages exactly once, insert-between-pages has no duplicates/gaps, filters, limits, bad cursor. Then seed 5,000 expenses locally and report page-1 vs page-100 timings and the same depth with OFFSET.

Commit: `feat(backend): keyset-paginated searchable expense feed and seed script`

---

## Step 8 — Balances & settlements

> Implement Step 8 per API_SPEC.md §6–7. balance_service runs the aggregate query (DB_SCHEMA.md §3) and domain.balances for nets + simplified transfers. Settlements: create (idempotent; caller must be from_user or to_user), list (keyset), delete (creator within 24 h). `GET /v1/groups` includes my_net_paise per group. Tests: the worked example end-to-end through the API, settlement rules, and that every group's nets sum to zero.

Commit: `feat(backend): balances, debt simplification and settlements`

---

## Step 9 — Flutter app + auth

> Implement Step 9. Create the Flutter app in `app/` (Android + Web) following ARCHITECTURE.md §4–5. Dependencies: flutter_riverpod, dio, go_router, supabase_flutter, intl, uuid; dev: mocktail. Import `package:material_ui/material_ui.dart`, never flutter/material. Config from `--dart-define-from-file=env.json` (API_BASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY) with a setup-error screen if missing; env.example.json committed. Theme per UI_UX.md §2. AuthService (sign up, sign in, sign out, session stream). Dio ApiClient with an auth interceptor (adds bearer token, refreshes once on 401) and ApiError mapping from API_SPEC.md §1. go_router with an auth redirect. Sign in/up screens per UI_UX.md §3.1. "Waking up the server…" banner when /health takes > 3 s. `core/money.dart` (parseRupees, formatINR with en_IN) with tests from TESTING.md §4.

Commit: `feat(app): flutter setup, auth and api client`

---

## Step 10 — Groups UI

> Implement Step 10 per APP_FLOW.md J1, J2, J8 and UI_UX.md §3.2, §3.3 (Members tab). Groups list with overall balance and per-group balance, create group sheet, join with code sheet, group screen shell with tabs, members tab with invite code copy/share/rotate (owner) and leave group. Loading/empty/error states. Widget tests for the groups list states.

Commit: `feat(app): groups list, create, join and members`

---

## Step 11 — Add / edit expense

> Implement Step 11 per APP_FLOW.md J3, J4, J7 and UI_UX.md §3.4–3.5. Add/edit screen with the split editor (equal/exact/%/shares), `domain/split_preview.dart` mirroring the backend largest-remainder rules (use the same test numbers as TESTING.md §2), one client-generated uuid per screen, Save disabled until valid, server errors shown inline. Expense detail with edit/delete permissions. Tests from TESTING.md §4 (add expense + split editor widget).

Commit: `feat(app): add and edit expenses with split editor`

---

## Step 12 — Feed + balances UI

> Implement Step 12 per APP_FLOW.md J5, J6 and UI_UX.md §3.3, §3.6. ExpenseFeedController (Riverpod) with first page, loadMore near the end, refresh, setQuery with 300 ms debounce and Dio CancelToken cancellation, filters (paid by, date range), month headers, "That's everything" footer, ListView.builder with lightweight tiles. Balances tab with member nets and suggested payments; Record payment sheet (only for rows involving me); settlements history. Tests from TESTING.md §4 (feed controller with a fake repository, settle-up sheet).

Commit: `feat(app): paginated searchable feed, balances and settle up`

---

## Step 13 — CI + deploy

> Implement Step 13. Add `.github/workflows/ci.yml`: backend job (Python 3.12, Postgres service container, ruff, alembic upgrade head, pytest) and app job (Flutter stable, flutter analyze, flutter test). Prepare Render deployment: `render.yaml` (Docker web service, health check /health, env vars listed but no values). Tell me the exact steps to create the Render service and which env vars to set. Make sure prod settings disable /docs and use the Supabase session pooler URL.

**You:** create the Render service from the repo, set env vars (DATABASE_URL, SUPABASE_URL, CORS_ORIGINS, ENV=prod), deploy, open `https://<service>.onrender.com/health`.

Commit: `ci: backend and app pipelines; render deploy config`

---

## Step 14 — Ship

> Implement Step 14. Write the root README: description, features, screenshots table (docs/screenshots/*.jpg placeholders), architecture diagram, tech stack, key engineering decisions (paise + largest remainder, keyset pagination, idempotent creates, RLS defence in depth, JWKS verification), measured performance numbers from Step 7, how to run backend/app/tests, future scope. Add INTERNET permission to the Android release manifest, app label "SplitEase", then build: `flutter build apk --release --obfuscate --split-debug-info=build/symbols --dart-define-from-file=env.json`. Confirm the APK contains only public config (API URL, Supabase URL, publishable key).

**You:** test the APK on your phone with two accounts, take screenshots, publish a GitHub Release `v1.0.0` with the APK, update your resume with real numbers.

Commit: `docs: README, screenshots; chore: android release config`
