# TRD — Technical Requirements Document

## 1. Tech stack

### Backend

| Concern | Choice | Why |
|---|---|---|
| Language | **Python 3.12** | Fast to build, great typing with Pydantic |
| Framework | **FastAPI** | Async, automatic OpenAPI docs, Pydantic validation |
| ORM | **SQLAlchemy 2.0 (async) + asyncpg** | Typed queries, explicit SQL control for pagination |
| Migrations | **Alembic** | Versioned schema, RLS policies live in migrations too |
| Auth | **Supabase Auth** tokens verified with **PyJWT** (JWKS) | No password handling in our code |
| Validation | **Pydantic v2** | Request/response schemas |
| Testing | **pytest, pytest-asyncio, httpx (ASGI client), Hypothesis** | Unit, API and property-based tests |
| Lint/format | **ruff** | One tool for lint + format |
| Container | **Docker** | Same image locally and on Render |

### App

| Concern | Choice | Why |
|---|---|---|
| Framework | **Flutter 3.50 / Dart 3.14** | Android + Web from one codebase |
| State | **flutter_riverpod** (Notifier / AsyncNotifier) | Same MVVM pattern as PaperTrade |
| HTTP | **dio** | Interceptors (auth header), `CancelToken` for search |
| Routing | **go_router** | Deep links, auth redirect |
| Auth | **supabase_flutter** (auth only — never queries tables) | Sign-up, sign-in, token refresh |
| Formatting | **intl** (`en_IN`) | `₹1,23,456.50` |
| UI | **material_ui** | `package:flutter/material.dart` is deprecated since Flutter 3.47 |
| Testing | **flutter_test, mocktail** | Unit + widget tests |

## 2. Money

- All amounts are **`int` paise** in Dart and **`int` / `BIGINT`** in Python/Postgres. Never float.
- Parsing user input: `"1234.5"` → `123450`. Reject more than 2 decimals, negatives, empty, > `100000000` (₹10,00,000.00).
- Percentages are stored as **basis points** (`int`, 100.00% = `10000`).
- Display: `₹1,23,456.50` (Indian grouping); signed amounts with `+` / `−`.

## 3. Split algorithms (pure Python in `backend/app/domain/splits.py`)

All split types return `dict[user_id, share_paise]` whose values **sum exactly** to `amount_paise`. Participant order is the order given in the request (deterministic tie-breaks).

### Largest-remainder method (shared by equal, percentage, shares)

Given weights `w_i` (all > 0) and total `A`:
1. `raw_i = A × w_i / W` where `W = Σ w_i` (exact rational: use integer numerator `A × w_i` and denominator `W`)
2. `base_i = floor(raw_i)` → `A × w_i // W`
3. `remainder = A − Σ base_i` (always `0 ≤ remainder < n`)
4. Give **+1 paisa** to the `remainder` participants with the **largest fractional parts** (`(A × w_i) % W`), ties broken by participant order.

| Type | Input | Weights |
|---|---|---|
| **Equal** | participants | `w_i = 1` |
| **Percentage** | `bp_i` per participant, Σ = 10000 | `w_i = bp_i` |
| **Shares** | `shares_i` (int ≥ 1) | `w_i = shares_i` |
| **Exact** | `paise_i` per participant | none — must already sum to `A`, each ≥ 0 |

Validation errors (typed): `EmptyParticipants`, `DuplicateParticipant`, `PercentagesMustSum100`, `InvalidShares`, `ExactSumMismatch`, `NegativeShare`.

Worked example (equal): ₹100.00 = 10000 paise, 3 people → base 3333 each, remainder 1 → first participant gets 3334. Shares sum: 3334 + 3333 + 3333 = 10000 ✔

## 4. Balances & settlement (pure Python in `backend/app/domain/balances.py`)

### Net balance per member
```
net[u] =  Σ amount of expenses u paid
        − Σ share_paise owed by u
        + Σ settlements u paid out      (u → someone)
        − Σ settlements u received      (someone → u)
```
Invariant: `Σ net[u] = 0` for every group (property-tested).

### Debt simplification (greedy)
1. Split members into creditors (`net > 0`) and debtors (`net < 0`).
2. Repeatedly match the **largest creditor** with the **largest debtor**; transfer `min(credit, debt)`; reduce both; drop anyone who reaches 0.
3. Ties broken by user id (deterministic output).

Properties (tested): every transfer amount > 0; applying all transfers makes every balance 0; number of transfers ≤ (number of non-zero members − 1). The greedy result is **not always the theoretical minimum** (that problem is NP-hard) — be honest about this in interviews.

## 5. Expense feed pagination

- **Keyset (cursor) pagination**, ordered by `(expense_date DESC, created_at DESC, id DESC)`.
- Cursor = base64url(JSON `{"d": "2026-11-14", "c": "2026-11-14T10:22:31.123Z", "i": "<uuid>"}`); opaque to the client.
- Query: `WHERE group_id = :g AND deleted_at IS NULL AND (expense_date, created_at, id) < (:d, :c, :i) ORDER BY ... LIMIT :limit + 1` → if `limit + 1` rows come back, there is a next page.
- `limit` 1–100, default 30.
- Filters: `q` (case-insensitive substring of title or notes, uses a pg_trgm GIN index), `paid_by` (uuid), `from` / `to` (dates, inclusive).
- Why not OFFSET: OFFSET gets slower deeper into the list and skips/duplicates rows when new expenses are inserted between page loads.

## 6. Idempotent creates

Expense and settlement creates take a **client-generated UUID** (`id` in the body). If a row with that id already exists **for the same user and same payload**, return it with `200` instead of creating a duplicate; if the payload differs, `409 Conflict`. This makes retries on flaky mobile networks safe.

## 7. Performance requirements

| Requirement | Target |
|---|---|
| Feed page (30 items) server time | < 300 ms with 5,000 expenses in the group |
| Balances endpoint | < 300 ms for a group with 5,000 expenses (single aggregate SQL query) |
| App feed scroll | No dropped frames with 5,000 loaded items (`ListView.builder`, lightweight tiles) |
| Search | 300 ms debounce; in-flight request cancelled when the query changes |
| Cold start (Render free) | App shows "Waking up the server…" after 3 s, retries automatically |

## 8. Configuration

### Backend (`backend/.env`, never committed)
| Variable | Example | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Supabase **session pooler** (port 5432) or direct; with the transaction pooler (6543) set `statement_cache_size=0` |
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Used for JWKS + issuer check |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` | |
| `CORS_ORIGINS` | `http://localhost:5000,https://...` | No wildcard |
| `ENV` | `dev` / `prod` | `prod` disables docs UI and debug logs |

### App (`app/env.json`, gitignored)
| Variable | Notes |
|---|---|
| `API_BASE_URL` | e.g. `https://splitease-api.onrender.com` |
| `SUPABASE_URL` | public |
| `SUPABASE_PUBLISHABLE_KEY` | public by design (anon/publishable key) — **never** the service_role/secret key |

## 9. Non-functional

- Backend: `ruff check` clean, type hints everywhere, structured JSON logs (no tokens, no emails at info level).
- App: `flutter analyze` with zero issues; loading / empty / error states on every data screen.
- Accessibility: 48dp tap targets; owed/owing shown with text and sign, not colour alone.
- All timestamps stored as `timestamptz` (UTC); expense dates as `date`.
