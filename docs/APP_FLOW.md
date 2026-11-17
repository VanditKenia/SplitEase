# App Flow

## 1. Navigation map

```
            ┌─────────────┐   not signed in   ┌─────────────┐
 launch ──▶ │ Splash/Auth │ ────────────────▶ │  Sign in    │ ◀──▶ Sign up
            │   gate      │                   └─────────────┘
            └─────┬───────┘ signed in
                  ▼
           ┌──────────────┐  [+] create   ┌──────────────────┐
           │   Groups     │ ────────────▶ │ Create group     │
           │ (home)       │  [join]       │ Join with code   │
           └──────┬───────┘               └──────────────────┘
                  │ tap group
                  ▼
           ┌──────────────────────────────────────────────┐
           │ Group screen — tabs: Expenses · Balances · Members │
           └───┬───────────────┬──────────────────┬───────┘
               │ FAB "Add"      │ "Settle up"      │ share invite code
               ▼                ▼                  ▼
        Add/Edit expense   Settle-up sheet     Share sheet / copy
               │
        Expense detail ◀── tap feed item (edit / delete)

 Groups app bar → Profile (display name, sign out)
```

## 2. First launch

1. Auth gate: no Supabase session → **Sign in**.
2. **Sign up** with email + password (min 8 chars) → Supabase may require email confirmation (show "Check your inbox" if so).
3. After sign-in: app calls `GET /v1/me` (creates profile) → if the display name is the default, show a one-time "What should friends call you?" prompt.
4. **Groups** screen, empty state: "Create a group" and "Join with a code".

## 3. Returning launch

1. Session restored by supabase_flutter (token auto-refresh).
2. `GET /health` in parallel; if it takes > 3 s show "Waking up the server…" banner (Render free tier cold start).
3. Groups list with my balance per group.

## 4. User journeys

### J1 — Create a group and invite
1. Groups → **+** → name "Goa trip" → Create.
2. Lands on the group → Members tab shows **invite code `K7Q2MX`** with Copy and Share buttons.
3. Share text: "Join my SplitEase group 'Goa trip' with code K7Q2MX".

### J2 — Join a group
1. Groups → **Join** → enter `k7q2mx` (auto-uppercase, 6 chars) → Join.
2. Unknown code → inline error "No group with that code".
3. Success → opens the group.

### J3 — Add an equal expense
1. Group → **Add expense**.
2. Title "Dinner", amount `3450`, paid by **me** (default), date **today** (default).
3. Split: **Equal** (default) among **all members** (default, toggle chips to exclude).
4. Live preview: "Vandit ₹1,150.00 · Riya ₹1,150.00 · Aman ₹1,150.00".
5. Save → back to feed; new expense at the top; balances update.

### J4 — Add an uneven expense
1. Split type selector: Equal · Exact · % · Shares.
2. **Percentage**: enter 50 / 30 / 20 → footer "Total 100% ✓"; if not 100 → "Total 90% — 10% left" and Save disabled.
3. **Exact**: enter rupees per person → footer "₹3,450.00 of ₹3,450.00 ✓" / "₹50.00 left".
4. **Shares**: steppers (default 1) → preview shows rupees per person.
5. Preview always shows final paise-exact amounts (with the extra paisa where applicable).

### J5 — Find an old expense
1. Expenses tab → search "elec" → results update 300 ms after typing stops.
2. Filter chips: **Paid by** (member picker), **Date** (this month / last month / custom range).
3. Scroll → next page loads automatically near the end; footer spinner; "That's everything" at the end.

### J6 — Settle up
1. Balances tab → my card: "You owe ₹1,715.00" (red) or "You're owed ₹2,750.00" (green).
2. Suggested payments list: "Aman pays Vandit ₹1,715.00".
3. Rows involving **me** have **Record payment** → sheet pre-filled (amount editable for partial payments) → Confirm.
4. Balances recompute; settlement appears in **History**.

### J7 — Edit or delete an expense
Feed → tap → detail (who paid, each share) → **Edit** (creator/payer only) or **Delete** (confirm dialog) → balances update.

### J8 — Leave a group
Members tab → **Leave group** → allowed only if my balance is ₹0.00; otherwise "Settle up first: you owe ₹X".

## 5. Edge flows

| Situation | Behaviour |
|---|---|
| Server sleeping (cold start) | "Waking up the server…" banner, automatic retry with backoff up to 60 s |
| Token expired | Interceptor refreshes once via supabase_flutter and retries; if refresh fails → sign-in |
| Offline | Banner "You're offline"; show last loaded data; disable Save |
| Duplicate tap on Save | Same client-generated id → server returns the existing expense (no duplicate) |
| Removed from group / group not visible | 404 → "This group isn't available" → back to Groups |
| Validation error from server | Show the field message inline (server is the source of truth) |
| Empty feed | "No expenses yet — add the first one" |
| Search with no results | "No expenses match 'xyz'" + Clear filters |
