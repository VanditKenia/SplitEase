# Security

SplitEase stores people's names, email addresses and who owes whom. Goals: only group members can see a group's data, nobody can act as someone else, and no secret ships in the app or the repo.

## 1. Threat model

| Threat | Impact | Mitigation |
|---|---|---|
| Reading another group's expenses (IDOR: guessing ids) | Privacy leak | Membership check in every service method; 404 (not 403) for groups you can't see; UUIDs; RLS on all tables |
| Calling Supabase's Data API with the public key | Bypass our API | RLS enabled everywhere; no write policies; read policies only for members |
| Forged or expired tokens | Impersonation | Verify JWT signature via Supabase JWKS, `exp`, `iss`, `aud`; reject `alg: none`/unexpected algorithms |
| Recording a settlement between two other people | Fake payments | Caller must be `from_user` or `to_user` |
| Editing someone else's expense | Tampering | Only creator or payer may edit/delete |
| Duplicate submissions on retry | Double-counted money | Client-generated ids + idempotent creates |
| Leaked secrets (DB URL, service key) | Full DB access | `.env` gitignored; Render env vars; never the service_role/secret key in the app; secret scanning before push |
| Tokens/passwords in logs | Account takeover | Never log `Authorization` headers, tokens, request bodies of auth calls; app's HTTP logger only in debug mode with redaction |
| Invite-code brute force | Joining strangers' groups | 6 chars from a 32-symbol alphabet (32^6 ≈ 1.07 billion codes); join endpoint rate-limited (10/min per user); owner can rotate |
| SQL injection | Data breach | SQLAlchemy bound parameters only; no string-built SQL; search term passed as a parameter |
| CORS abuse from other websites | CSRF-like calls | Explicit origin allowlist; bearer tokens (no cookies) |
| Mass requests | Free-tier exhaustion | Per-user rate limits; request size limit (32 KB) |

## 2. Authentication

- **Supabase Auth** handles sign-up, password hashing, sessions and refresh tokens. Our code never sees passwords.
- The app sends the Supabase **access token** to our API as `Authorization: Bearer <token>`.
- Backend verification (`app/auth.py`):
  1. Fetch signing keys from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` with `PyJWKClient` (cached).
  2. `jwt.decode(token, key, algorithms=[<the project's alg, e.g. "ES256" or "RS256">], audience="authenticated", issuer=f"{SUPABASE_URL}/auth/v1")`.
  3. Use `sub` as the user id. Reject tokens without `sub`.
  4. If the project still uses the legacy shared secret (HS256), verify with that secret from env instead — check which one your project uses in Supabase → Project Settings → JWT Keys, and prefer asymmetric keys.
- Token refresh is handled by supabase_flutter; the Dio interceptor retries a request once after a refresh.

## 3. Authorization (primary defence: the API)

Every service method that touches a group calls `require_member(user_id, group_id)` first; owner-only actions call `require_owner`. Rules:

| Action | Who |
|---|---|
| Read group, members, expenses, balances, settlements | Current member |
| Add expense | Current member; payer and participants must be current members |
| Edit / delete expense | Expense creator or payer |
| Record settlement | `from_user` or `to_user` (and both are/were members) |
| Delete settlement | Creator, within 24 h |
| Rotate invite code | Owner |
| Leave group | Self, only with zero balance |

Write tests for each rule (TESTING.md §4) — including "a member of group A gets 404 on group B's expense".

## 4. Row Level Security (defence in depth)

See DB_SCHEMA.md §4. Summary: RLS on every table, no INSERT/UPDATE/DELETE policies, member-only SELECT policies, privileges revoked from `anon`. After each migration run Supabase's **Security Advisor** and fix every warning.

## 5. Secrets & configuration

| Secret | Lives in | Never in |
|---|---|---|
| `DATABASE_URL` (with password) | `backend/.env` (local), Render env vars | git, app, logs |
| Supabase service_role / secret key | Not needed at all — don't create usage | anywhere in this project |
| Supabase publishable (anon) key | `app/env.json` (gitignored, but public by design) | — (safe to ship; RLS protects data) |

- `.gitignore`: `.env`, `env.json`, `*.env`, `.venv/`, `__pycache__/`, `build/`.
- Commit `backend/.env.example` and `app/env.example.json` with placeholders.
- Before every push: `git diff --cached` must not contain `postgresql://` with a password, `sb_secret_`, or `service_role`.

## 6. Input validation

- Pydantic models with strict types, lengths and ranges (DB_SCHEMA.md column limits).
- Amounts: integer paise in the API (the app converts rupees → paise); range-checked.
- Text fields trimmed; control characters rejected.
- Cursor decoded defensively (base64 + JSON + type checks) → `400 invalid_cursor` on anything odd.
- Request body max 32 KB.

## 7. Transport & platform

- HTTPS only (Render provides TLS). App rejects `http://` API URLs in release builds.
- Android: no cleartext traffic. Session storage: supabase_flutter default; consider `flutter_secure_storage` for the session on mobile (future hardening).
- Production: FastAPI docs UI disabled (`ENV=prod`), generic 500 messages, no stack traces.

## 8. Pre-push checklist

- [ ] No secrets in the diff (DB URL with password, secret/service keys)
- [ ] `ruff check` and `pytest` pass; `flutter analyze` and `flutter test` pass
- [ ] Authorization tests pass (cross-group access returns 404)
- [ ] Supabase Security Advisor: no RLS warnings
