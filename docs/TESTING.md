# Testing

## 1. Strategy

| Layer | Type | Tools | Priority |
|---|---|---|---|
| Backend `domain/` (money, splits, balances) | Unit + **property-based** | pytest, Hypothesis | **Must** |
| Backend API (auth, groups, expenses, feed, balances, settlements) | Integration against a real test Postgres | pytest-asyncio, httpx ASGI client, docker-compose Postgres | **Must** |
| Authorization rules | Integration | same | **Must** |
| App `domain/` (money parsing, split preview) | Unit | flutter_test | Must |
| App controllers (feed pagination, debounce/cancel, add-expense validation) | Unit with fake repositories | flutter_test, mocktail | Should |
| App widgets (split editor, feed, settle-up sheet) | Widget | flutter_test | Should |
| End-to-end | Manual QA checklist | device/emulator + deployed API | Must before release |

Commands:
```bash
cd backend && docker compose up -d db && pytest -q
cd app && flutter test
```
Auth in API tests: generate test tokens signed with a **test key pair** and point the verifier at a test JWKS (dependency override) — never call real Supabase from tests.

## 2. Backend domain tests

### Splits (`tests/domain/test_splits.py`)
```
equal
  ✓ 10000 paise / 3 → [3334, 3333, 3333] (extra paisa to first by order)
  ✓ 1 paisa / 3 → [1, 0, 0]
  ✓ single participant gets everything
percentage
  ✓ 345000 at 50/30/20 % → [172500, 103500, 69000]
  ✓ 10000 at 33.33/33.33/33.34 % (3333/3333/3334 bp) sums exactly to 10000
  ✓ rejects totals ≠ 10000 bp
shares
  ✓ 10000 with shares 2,1,1 → [5000, 2500, 2500]
  ✓ 100 with shares 1,1,1 → [34, 33, 33]
  ✓ rejects shares ≤ 0
exact
  ✓ accepts when sum == amount
  ✓ rejects sum mismatch and negatives
common
  ✓ rejects empty and duplicate participants
  ✓ deterministic: same input → same output
```

**Property tests (Hypothesis)** — for random amounts (1 … 10^8) and random weights (1–20 participants):
- result sums **exactly** to the amount
- every share ≥ 0
- for equal splits, max share − min share ≤ 1 paisa
- for weighted splits, each share is within 1 paisa of the exact proportional value

### Balances (`tests/domain/test_balances.py`)
```
✓ worked example below
✓ settlements move balances in the right direction
✓ deleted expenses are excluded (repository-level test)
simplify_debts
  ✓ simple chain A→B→C collapses
  ✓ output is deterministic
```
**Property tests:** for random valid ledgers:
- Σ net = 0
- applying the simplified transfers zeroes every balance
- every transfer > 0, nobody pays themselves
- number of transfers ≤ (non-zero members − 1)

### Worked example (use as a test)
Members A, B, C.
1. A pays ₹300.00 (30000), equal split A/B/C → shares 10000 each.
2. B pays ₹150.00 (15000), split shares A:1, B:2 (C not included) → A 5000, B 10000.
3. C pays B ₹50.00 (settlement C→B 5000).

Net:
- A: paid 30000 − owed (10000 + 5000) = **+15000**
- B: paid 15000 − owed (10000 + 10000) − received 5000 = **−10000**
- C: paid 0 − owed 10000 + sent 5000 = **−5000**
- Sum = 0 ✓

Simplified transfers: **B → A ₹100.00 (10000)**, **C → A ₹50.00 (5000)**.

## 3. Backend API tests (`tests/api/`)

```
me
  ✓ first GET creates profile; second returns same
groups
  ✓ create → creator is owner, invite code 6 chars from the alphabet
  ✓ join by code (case-insensitive); unknown code → 404
  ✓ rotate code: owner only (member → 403)
  ✓ leave with non-zero balance → 409; with zero → 204
expenses
  ✓ create each split type; response splits sum to amount
  ✓ payer/participant not a member → 422
  ✓ idempotent create: same id+payload → 200 same expense; different payload → 409
  ✓ edit by creator/payer OK; by other member → 403
  ✓ delete is soft; excluded from feed and balances
feed
  ✓ walking all pages returns every expense exactly once, in order
  ✓ inserting an expense between page fetches → no duplicates or gaps on later pages
  ✓ q, paid_by, from/to filters
  ✓ limit bounds; bad cursor → 400
balances & settlements
  ✓ worked example end-to-end via the API
  ✓ recording a settlement between two other members → 403
  ✓ settlement delete: creator within 24 h only
authorization
  ✓ non-member gets 404 for group, expense, balances, settlements
  ✓ missing/invalid/expired token → 401; wrong audience/issuer → 401
```

## 4. App tests

```
domain
  ✓ parseRupees: "1234.5" → 123450, "0.01" → 1, rejects "1.234", "-5", "", "abc"
  ✓ formatINR: 12345650 → "₹1,23,456.50"
  ✓ splitPreview mirrors backend examples (same numbers as §2)
expense feed controller (fake repository)
  ✓ first page loads; loadMore appends; no double-loading while busy
  ✓ stops when next_cursor is null
  ✓ setQuery debounces 300 ms and cancels the in-flight request; stale response never overwrites newer
  ✓ error then retry
add expense
  ✓ Save disabled until valid for each split type (100%, exact total)
  ✓ uses one client-generated id per screen (double tap → same id)
widgets
  ✓ split editor footer messages ("10% left", "₹50.00 left")
  ✓ feed shows month headers and "That's everything"
  ✓ settle-up sheet pre-fills from suggestion
```

## 5. Performance check (record numbers for the README/resume)

1. `python scripts/seed_expenses.py --group <id> --count 5000`
2. Measure server time for the first and the 100th feed page (log timing middleware or `EXPLAIN ANALYZE`): both should be similar and < 300 ms.
3. Compare with an OFFSET query at the same depth (write the numbers down).
4. App: Flutter DevTools in **profile mode**, scroll the feed through ~1,000 items → note average frame build/raster times.

## 6. Manual QA checklist (before release)

- [ ] Sign up, confirm email (if enabled), sign in, sign out, sign back in
- [ ] Create group, copy code, join from a second account (second browser profile)
- [ ] Add one expense of each split type; preview matches saved values to the paisa
- [ ] Balances correct for the worked example; suggested payments make sense
- [ ] Record a payment → balances update; history shows it
- [ ] Edit and delete an expense → balances update
- [ ] Search and filters; infinite scroll with seeded data
- [ ] Leave group blocked with a non-zero balance
- [ ] Second account cannot open the first account's other group (404 screen)
- [ ] Cold start: open the app after the server slept → "Waking up" banner, then data
- [ ] Airplane mode → offline banner, no crash
