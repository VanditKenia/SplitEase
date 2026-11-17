# SplitEase

> 🚧 **Work in progress.** This is a placeholder README; the full version (features, screenshots, setup, performance numbers) comes in Step 14 of the [roadmap](docs/ROADMAP.md).

SplitEase is a group expense-splitting app for flatmates, trips and friends' outings. Anyone in a group adds an expense, picks how to split it (equal, exact amounts, percentage or shares), and the app keeps a live balance for every member. A debt simplification step turns a web of IOUs into a short list of "A pays B ₹X" payments, and members record settlements when they pay. All money is stored as integer paise, so every split sums to the bill exactly.

## Tech stack

- **App:** Flutter (Android + Web)
- **Backend:** FastAPI (Python)
- **Data & auth:** Supabase (PostgreSQL + Auth)

## Documentation

| File | What it covers |
|---|---|
| [docs/README.md](docs/README.md) | Docs index and reading order |
| [docs/PRD.md](docs/PRD.md) | Product requirements: problem, users, features, scope |
| [docs/TRD.md](docs/TRD.md) | Technical requirements: stack, money rules, split algorithms, config |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, backend and app layers, folder structure |
| [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md) | Tables, constraints, indexes, Row Level Security |
| [docs/API_SPEC.md](docs/API_SPEC.md) | REST endpoints, request/response shapes, errors |
| [docs/APP_FLOW.md](docs/APP_FLOW.md) | Screens, navigation and user journeys |
| [docs/UI_UX.md](docs/UI_UX.md) | Design system, screen layouts and states |
| [docs/SECURITY.md](docs/SECURITY.md) | Threat model, auth, authorization, secrets |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy, required tests, manual QA |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Step-by-step build plan |
