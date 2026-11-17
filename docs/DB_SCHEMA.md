# Database Schema (PostgreSQL on Supabase)

All tables live in the `public` schema and are created by **Alembic** migrations in `backend/alembic/`. Money columns are `BIGINT` paise. Timestamps are `timestamptz` (UTC).

## 1. Tables

### `profiles`
One row per user; `id` equals the Supabase Auth user id (`auth.users.id`).

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK, FK → `auth.users(id)` ON DELETE CASCADE |
| display_name | text | NOT NULL, length 1–40 |
| created_at | timestamptz | NOT NULL DEFAULT now() |

Created by the API on the first authenticated request (`GET /v1/me`) if missing.

### `groups`
| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| name | text | NOT NULL, length 1–50 |
| invite_code | text | NOT NULL UNIQUE, 6 chars from `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` |
| created_by | uuid | NOT NULL FK → profiles(id) |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### `group_members`
| Column | Type | Constraints |
|---|---|---|
| group_id | uuid | FK → groups(id) ON DELETE CASCADE |
| user_id | uuid | FK → profiles(id) ON DELETE CASCADE |
| role | text | NOT NULL CHECK (role IN ('owner','member')) |
| joined_at | timestamptz | NOT NULL DEFAULT now() |
| left_at | timestamptz | NULL (set when a member leaves; keeps history valid) |

PK `(group_id, user_id)`. "Current member" = `left_at IS NULL`.

### `expenses`
| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK (client-generated) |
| group_id | uuid | NOT NULL FK → groups(id) ON DELETE CASCADE |
| title | text | NOT NULL, length 1–80 |
| notes | text | NULL, length ≤ 500 |
| amount_paise | bigint | NOT NULL CHECK (amount_paise BETWEEN 1 AND 100000000) |
| paid_by | uuid | NOT NULL FK → profiles(id) |
| split_type | text | NOT NULL CHECK (split_type IN ('equal','exact','percentage','shares')) |
| expense_date | date | NOT NULL |
| created_by | uuid | NOT NULL FK → profiles(id) |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |
| deleted_at | timestamptz | NULL (soft delete) |

### `expense_splits`
| Column | Type | Constraints |
|---|---|---|
| expense_id | uuid | FK → expenses(id) ON DELETE CASCADE |
| user_id | uuid | FK → profiles(id) |
| share_paise | bigint | NOT NULL CHECK (share_paise >= 0) |
| input_value | bigint | NULL — what the user typed: exact paise, basis points, or shares (for editing) |
| position | smallint | NOT NULL — participant order (deterministic remainders) |

PK `(expense_id, user_id)`.
Invariant `Σ share_paise = expenses.amount_paise` is enforced by the service **and** by a **constraint trigger** (deferred, checked at commit).

### `settlements`
| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK (client-generated) |
| group_id | uuid | NOT NULL FK → groups(id) ON DELETE CASCADE |
| from_user | uuid | NOT NULL FK → profiles(id) — who paid |
| to_user | uuid | NOT NULL FK → profiles(id) — who received |
| amount_paise | bigint | NOT NULL CHECK (amount_paise BETWEEN 1 AND 100000000) |
| note | text | NULL, length ≤ 200 |
| settled_at | timestamptz | NOT NULL DEFAULT now() |
| created_by | uuid | NOT NULL FK → profiles(id) |

CHECK `(from_user <> to_user)`.

## 2. Indexes

| Index | Purpose |
|---|---|
| `expenses (group_id, expense_date DESC, created_at DESC, id DESC) WHERE deleted_at IS NULL` | Keyset pagination of the feed |
| `expenses USING gin ((title || ' ' || coalesce(notes,'')) gin_trgm_ops)` | Fast `ILIKE '%q%'` search (needs `CREATE EXTENSION pg_trgm`) |
| `expenses (group_id, paid_by) WHERE deleted_at IS NULL` | Payer filter + balance aggregation |
| `expense_splits (user_id)` | Balance aggregation |
| `group_members (user_id) WHERE left_at IS NULL` | "My groups" |
| `settlements (group_id, settled_at DESC)` | Settlement history |

## 3. Balance aggregation query (sketch)

```sql
WITH paid AS (
  SELECT paid_by AS user_id, SUM(amount_paise) AS v
  FROM expenses WHERE group_id = :g AND deleted_at IS NULL GROUP BY paid_by
), owed AS (
  SELECT s.user_id, SUM(s.share_paise) AS v
  FROM expense_splits s JOIN expenses e ON e.id = s.expense_id
  WHERE e.group_id = :g AND e.deleted_at IS NULL GROUP BY s.user_id
), sent AS (
  SELECT from_user AS user_id, SUM(amount_paise) AS v FROM settlements WHERE group_id = :g GROUP BY from_user
), received AS (
  SELECT to_user AS user_id, SUM(amount_paise) AS v FROM settlements WHERE group_id = :g GROUP BY to_user
)
SELECT m.user_id,
       COALESCE(paid.v,0) - COALESCE(owed.v,0) + COALESCE(sent.v,0) - COALESCE(received.v,0) AS net_paise
FROM group_members m
LEFT JOIN paid USING (user_id) LEFT JOIN owed USING (user_id)
LEFT JOIN sent USING (user_id) LEFT JOIN received USING (user_id)
WHERE m.group_id = :g;
```
(Includes members who left, so history still balances to zero.)

## 4. Row Level Security (defence in depth)

The app never queries tables directly — but Supabase exposes every `public` table through its Data API, and the publishable key ships inside the app. So:

1. **Enable RLS on every table** (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
2. **Revoke** table privileges from `anon`; grant only `SELECT` to `authenticated`.
3. **Read-only policies for members** (in case a client ever reads directly):

```sql
-- helper: is the current user a current member of a group?
CREATE FUNCTION public.is_member(g uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (SELECT 1 FROM group_members
                 WHERE group_id = g AND user_id = auth.uid() AND left_at IS NULL)
$$;

CREATE POLICY profiles_self_or_shared ON profiles FOR SELECT TO authenticated
  USING (id = auth.uid() OR EXISTS (
    SELECT 1 FROM group_members a JOIN group_members b ON a.group_id = b.group_id
    WHERE a.user_id = auth.uid() AND b.user_id = profiles.id));

CREATE POLICY groups_member_read     ON groups          FOR SELECT TO authenticated USING (is_member(id));
CREATE POLICY members_member_read    ON group_members   FOR SELECT TO authenticated USING (is_member(group_id));
CREATE POLICY expenses_member_read   ON expenses        FOR SELECT TO authenticated USING (is_member(group_id));
CREATE POLICY splits_member_read     ON expense_splits  FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM expenses e WHERE e.id = expense_id AND is_member(e.group_id)));
CREATE POLICY settlements_member_read ON settlements    FOR SELECT TO authenticated USING (is_member(group_id));
```
4. **No INSERT/UPDATE/DELETE policies** → all writes through the Data API are denied. Only the backend writes.
5. The backend connects with the database owner role (bypasses RLS) and enforces membership in its **service layer** — that's the primary authorization; RLS is the safety net.

Verify after migrating: with the publishable key, `GET https://<ref>.supabase.co/rest/v1/expenses` returns `[]` (or 401) for anonymous requests, and Supabase's **Security Advisor** shows no "RLS disabled" warnings.

## 5. Seed data

`backend/scripts/seed_expenses.py --group <id> --count 5000` inserts realistic expenses (random titles like "Groceries", "Electricity bill", random payer, equal splits, dates over the last 18 months) using the real split function, so balances stay valid.
