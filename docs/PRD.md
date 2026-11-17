# PRD — Product Requirements Document

**Product:** SplitEase — group expense splitting
**Platforms:** Android + Web (Flutter); iOS from the same codebase later
**Version:** 1.0 (MVP)
**Owner:** Vandit Kenia

---

## 1. Problem

Groups that share costs (flatmates, trips, office lunches) lose track of who paid what. Splitting by hand causes rounding mistakes ("who pays the extra paisa?"), awkward reminders, and too many small payments between people.

## 2. Solution

A shared group ledger. Anyone in the group adds an expense, picks how to split it, and the app keeps a live balance for every member. A **debt simplification** step turns a web of IOUs into a short list of payments, and members record settlements when they pay.

## 3. Target users

| Persona | Need |
|---|---|
| **Flatmates** (primary) — rent, groceries, utilities every month | Long expense history that stays fast and searchable |
| **Trip group** — many expenses in a few days | Quick entry, uneven splits, settle up at the end |
| **Friends' outings** — occasional shared bills | Simple equal splits, easy invite |

## 4. Goals & success criteria

| Goal | Measure |
|---|---|
| Correct money | Every split sums to the expense **exactly** (paise); all balances in a group sum to **0** — enforced by property-based tests |
| Fewer payments | Settle-up suggestions need at most `n − 1` transfers for `n` members with non-zero balances |
| Fast history | Expense feed loads a page in < 300 ms (server) and scrolls smoothly with 5,000+ expenses |
| Easy start | New user can create a group, invite a friend and add the first expense in under 2 minutes |
| Secure | Users can only see groups they belong to — enforced in the API and by RLS |

## 5. Scope

### In scope (MVP — v1.0)

| # | Feature | Priority |
|---|---|---|
| F1 | **Sign up / sign in** with email + password (Supabase Auth) | P0 |
| F2 | **Profile** — display name | P0 |
| F3 | **Create group** (name) — creator becomes owner | P0 |
| F4 | **Join group by invite code** (6 characters); owner can rotate the code | P0 |
| F5 | **Members list**; leave group (only when your balance is 0) | P1 |
| F6 | **Add expense**: title, amount, date, payer, participants, notes | P0 |
| F7 | **Four split types**: equal, exact amounts, percentage, shares — with a live preview | P0 |
| F8 | **Edit / delete expense** (creator or payer; soft delete) | P1 |
| F9 | **Expense feed**: cursor-paginated, newest first, search by text, filter by payer and date range | P0 |
| F10 | **Balances**: each member's net balance in the group | P0 |
| F11 | **Settle up**: simplified "A pays B ₹X" suggestions; record a settlement | P0 |
| F12 | **Groups list** showing your net balance in each group | P0 |
| F13 | **Settlement history** | P1 |

### Out of scope (v1.0)

- Real payments / UPI integration (record-only; payments happen outside the app)
- Multiple currencies (INR only)
- Receipt scanning, comments, push notifications
- Recurring expenses
- Offline editing (read cache only, if time allows)

### Future (v2+)

Recurring expenses · push notifications ("you were added to an expense") · receipt photo + OCR · multi-currency with FX · export to CSV · offline-first write queue

## 6. User stories

- As a user, I can **sign up** and set my **display name**.
- As a user, I can **create a group** and share its **invite code**.
- As a user, I can **join a group** with a code a friend sent me.
- As a member, I can **add an expense** I paid and split it **equally** among chosen members.
- As a member, I can split by **exact amounts**, **percentages** or **shares** and see the split **before saving**.
- As a member, I can **search** old expenses ("electricity") and **filter** by who paid or by month.
- As a member, I can see **my balance** and **everyone's balance** in the group.
- As a member, I can see **who should pay whom** with the fewest payments and **record a payment**.
- As a user, I can see all my groups and **how much I owe or am owed** in each.

## 7. Business rules (summary — full detail in TRD.md)

1. Money is integer **paise**; amounts entered in rupees with up to 2 decimals.
2. Expense amount: ₹0.01 to ₹10,00,000.00.
3. Payer and every participant must be current group members.
4. Every split must sum exactly to the expense amount (largest-remainder rounding).
5. Percentages must sum to exactly 100.00%; shares must be positive whole numbers.
6. Positive balance = the group owes you; negative = you owe.
7. All balances in a group always sum to zero.
8. A settlement from A to B for ₹X increases A's balance by X and decreases B's by X.
9. A member can leave only if their balance is exactly 0.

## 8. Assumptions & constraints

- Backend hosted on Render's free tier: it sleeps after ~15 minutes idle, so the first request can take 30–60 s ("waking up the server" state in the app).
- Supabase free tier for Postgres + Auth.
- Single currency (₹), Indian number formatting (`₹1,23,456.50`).
