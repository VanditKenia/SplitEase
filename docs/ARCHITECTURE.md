# Architecture

## 1. System overview

```
┌──────────────┐  1. sign in (email+password)   ┌──────────────────┐
│ Flutter app  │ ─────────────────────────────▶ │  Supabase Auth   │
│ (Android/Web)│ ◀──── access token (JWT) ───── │                  │
│              │                                └──────────────────┘
│              │  2. REST + "Authorization: Bearer <JWT>"
│              │ ─────────────────────────────▶ ┌──────────────────┐   SQL    ┌──────────────────┐
│              │ ◀──────────── JSON ─────────── │ FastAPI backend  │ ───────▶ │ Supabase Postgres│
└──────────────┘                                │ (Render, Docker) │          │ (RLS enabled)    │
                                                └──────────────────┘          └──────────────────┘
                                                  verifies JWT via JWKS
```

Rules:
- The app talks to **Supabase only for authentication**. All data goes through **our API**.
- The API is the only thing that reads/writes tables. It checks **membership on every request**.
- RLS is enabled on every table as **defence in depth**: even with the public key, nobody can read tables through Supabase's auto-generated Data API.

## 2. Backend layers

```
api/ (routers)          HTTP only: parse request, call service, map errors → HTTP
   │
services/               business rules + authorization (membership/role checks), transactions
   │
repositories/           SQL only (SQLAlchemy); no business rules
   │
models/ (ORM)  schemas/ (Pydantic)

domain/                 pure Python: money, splits, balances, simplification — no DB, no FastAPI
```

Dependencies point downward only. `domain/` imports nothing from the rest of the app.

## 3. Backend folder structure

```
backend/
  app/
    main.py                 # FastAPI app, CORS, error handlers, routers
    config.py               # pydantic-settings
    db.py                   # async engine, session dependency
    auth.py                 # JWT verification (JWKS), current_user dependency
    errors.py               # AppError hierarchy → HTTP mapping
    domain/
      money.py              # parse_rupees, format, constants
      splits.py             # largest remainder, equal/exact/percentage/shares
      balances.py           # net balances, simplify_debts
    models/                 # SQLAlchemy ORM models
    schemas/                # Pydantic request/response models
    repositories/           # profile_repo, group_repo, expense_repo, settlement_repo
    services/               # group_service, expense_service, balance_service, settlement_service
    api/v1/                 # me.py, groups.py, expenses.py, balances.py, settlements.py
  alembic/                  # migrations (schema + RLS)
  scripts/seed_expenses.py  # 5,000 demo expenses for performance testing
  tests/
    domain/                 # pure unit + Hypothesis property tests
    api/                    # endpoint tests against a real test Postgres
  Dockerfile
  docker-compose.yml        # local Postgres for dev/tests
  pyproject.toml
  .env.example
```

## 4. App layers (same MVVM as PaperTrade)

```
UI (screens/widgets) ─watches─▶ Providers (Riverpod Notifiers = ViewModels)
                                     │ calls
                                     ▼
                               Repositories (one per resource)
                                     │ uses
                                     ▼
                               ApiClient (Dio + auth interceptor)    AuthService (supabase_flutter)

domain/  pure Dart: Money (paise), split preview (mirror of backend rules), formatting
```

The app's split **preview** uses the same largest-remainder rules as the backend so the user sees exactly what will be saved; the **backend result is the source of truth**.

## 5. App folder structure

```
app/lib/
  main.dart / app.dart / router.dart
  core/        config.dart, money.dart, format.dart, theme.dart, api_client.dart, api_error.dart
  domain/      models/ (Group, Member, Expense, Split, Balance, Transfer, Settlement), split_preview.dart
  data/        auth_service.dart, group_repository.dart, expense_repository.dart,
               balance_repository.dart, settlement_repository.dart
  features/
    auth/          sign_in_screen.dart, sign_up_screen.dart, auth_provider.dart
    groups/        groups_screen.dart, create_group_sheet.dart, join_group_sheet.dart, groups_provider.dart
    group_detail/  group_screen.dart (tabs), members_tab.dart
    expenses/      expense_feed.dart, expense_feed_controller.dart, add_expense_screen.dart,
                   split_editor.dart, expense_detail_screen.dart
    balances/      balances_tab.dart, settle_up_sheet.dart, settlements_list.dart
    profile/       profile_screen.dart
```

## 6. Key request flows

### Add expense
```
AddExpenseScreen → splitPreview (instant, local)
   → expenseRepository.create(id: uuid v4, ...)          (client-generated id)
   → POST /v1/groups/{g}/expenses
        api → expense_service.create:
              check payer + participants are members
              domain.splits.compute(...)                 (exact paise)
              repo insert expense + splits (one transaction)
   ← 201 Expense with splits
   → invalidate feed, balances, groups list
```

### Expense feed with search
```
type "elec" → 300 ms debounce → cancel previous CancelToken
   → GET /v1/groups/{g}/expenses?q=elec&limit=30
   ← {items, next_cursor}
scroll near end → GET ...&cursor=<next_cursor> → append
```

### Balances
```
GET /v1/groups/{g}/balances
   → one aggregate SQL query (paid, owed, settlements per member)
   → domain.balances.net + simplify_debts
   ← {members:[{user, net_paise}], transfers:[{from, to, amount_paise}]}
```

## 7. Key design decisions

| Decision | Reason |
|---|---|
| Integer paise everywhere | Floats can't represent money exactly; splits must sum exactly |
| Largest-remainder rounding | Fair and deterministic: no paisa lost, at most 1 paisa difference between equal shares |
| Pure `domain/` modules | Money logic tested exhaustively without DB or HTTP |
| Keyset pagination | Constant speed at any depth; no duplicates/gaps when new expenses arrive |
| Client-generated ids | Safe retries (idempotent creates) on flaky networks |
| Supabase Auth, own API for data | No password code to get wrong; one place for authorization rules |
| RLS deny-by-default | The public key can't be used to read tables directly |
| Soft delete for expenses | History stays consistent; deleted expenses drop out of balances |
| Balances computed on read | Always correct; one aggregate query is fast enough at this scale (no cached totals to drift) |
