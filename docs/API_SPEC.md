# API Specification (FastAPI, base path `/v1`)

All endpoints except `/health` require `Authorization: Bearer <Supabase access token>`.
Content type: `application/json`. Money in **paise** (integers). Dates `YYYY-MM-DD`, timestamps ISO-8601 UTC.
Interactive docs: `/docs` (dev only).

## 1. Errors

Every error has the same shape:
```json
{ "error": { "code": "not_found", "message": "Group not found." } }
```

| HTTP | code | When |
|---|---|---|
| 400 | `invalid_cursor` | Cursor can't be decoded |
| 401 | `unauthenticated` | Missing/expired/invalid token |
| 403 | `not_allowed` | Member but lacks permission (not owner / not creator or payer / not a party to the settlement) |
| 404 | `not_found` | Resource doesn't exist **or** caller can't see it (don't leak existence) |
| 409 | `conflict` | Idempotency id reused with a different payload; invite code collision retry exhausted |
| 409 | `balance_not_zero` | Leaving a group with a non-zero balance |
| 422 | `validation_error` | Pydantic or split-rule failure (`details` lists fields) |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal` | Unexpected (no stack traces in prod) |

Split-rule codes (inside 422): `empty_participants`, `duplicate_participant`, `participant_not_member`, `payer_not_member`, `percentages_must_sum_100`, `invalid_shares`, `exact_sum_mismatch`, `amount_out_of_range`.

## 2. Health

`GET /health` → `200 {"status":"ok"}` (no auth; used by Render and by the app's "waking up" check).

## 3. Me

### `GET /v1/me`
Creates the profile on first call (display name defaults to the email's local part).
```json
{ "id": "uuid", "email": "a@b.com", "display_name": "Vandit" }
```

### `PATCH /v1/me`
```json
{ "display_name": "Vandit K" }
```

## 4. Groups

### `GET /v1/groups`
My current groups with my net balance in each.
```json
{ "items": [ { "id": "uuid", "name": "Flat 302", "member_count": 4, "my_net_paise": -125050, "role": "owner" } ] }
```

### `POST /v1/groups`
```json
{ "name": "Goa trip" }
```
→ `201` group with `invite_code`. Creator becomes `owner`.

### `GET /v1/groups/{group_id}`
```json
{ "id": "uuid", "name": "Goa trip", "invite_code": "K7Q2MX", "created_at": "...", "my_role": "owner",
  "members": [ { "user_id": "uuid", "display_name": "Vandit", "role": "owner" } ] }
```
`invite_code` is returned to all members (anyone can invite).

### `POST /v1/groups/join`
```json
{ "invite_code": "k7q2mx" }
```
Case-insensitive. → `200` group. Re-joining after leaving clears `left_at`. Unknown code → `404`.

### `POST /v1/groups/{group_id}/invite-code`
Owner only. Rotates the code → `200 {"invite_code": "P3RTZ8"}`.

### `DELETE /v1/groups/{group_id}/members/me`
Leave the group. `409 balance_not_zero` unless my net is exactly 0. If the owner leaves, ownership passes to the longest-standing member; the last member leaving deletes nothing (group stays, read-only history).

## 5. Expenses

### `POST /v1/groups/{group_id}/expenses`
```json
{
  "id": "6f1c0c0e-6a2b-4b5c-9d6e-1f2a3b4c5d6e",
  "title": "Dinner at Thalassa",
  "notes": "Saturday",
  "amount_paise": 345000,
  "paid_by": "uuid-A",
  "expense_date": "2026-11-14",
  "split": {
    "type": "percentage",
    "participants": [
      { "user_id": "uuid-A", "value": 5000 },
      { "user_id": "uuid-B", "value": 3000 },
      { "user_id": "uuid-C", "value": 2000 }
    ]
  }
}
```
`value` meaning by type: `equal` → omitted; `exact` → paise; `percentage` → basis points (100% = 10000); `shares` → positive integer.

→ `201`:
```json
{
  "id": "6f1c...", "group_id": "uuid", "title": "Dinner at Thalassa", "notes": "Saturday",
  "amount_paise": 345000, "paid_by": { "user_id": "uuid-A", "display_name": "Vandit" },
  "split_type": "percentage", "expense_date": "2026-11-14",
  "splits": [
    { "user_id": "uuid-A", "display_name": "Vandit", "share_paise": 172500, "input_value": 5000 },
    { "user_id": "uuid-B", "display_name": "Riya",   "share_paise": 103500, "input_value": 3000 },
    { "user_id": "uuid-C", "display_name": "Aman",   "share_paise": 69000,  "input_value": 2000 }
  ],
  "created_by": "uuid-A", "created_at": "...", "updated_at": "..."
}
```
Idempotency: same `id` + same payload from the same user → `200` with the existing expense; same `id`, different payload → `409 conflict`.

### `GET /v1/groups/{group_id}/expenses`
Query params: `limit` (1–100, default 30), `cursor`, `q`, `paid_by`, `from`, `to`.
```json
{
  "items": [ { "id": "...", "title": "...", "amount_paise": 345000, "paid_by": {...},
               "expense_date": "2026-11-14", "my_share_paise": 103500, "split_type": "percentage" } ],
  "next_cursor": "eyJkIjoiMjAyNi0xMS0xNCIsImMiOiIuLi4iLCJpIjoiLi4uIn0"
}
```
Feed items are compact (no full split list); `my_share_paise` is the caller's share (0 if not a participant). `next_cursor` is `null` on the last page.

### `GET /v1/expenses/{expense_id}`
Full expense (same shape as create response). `404` if not a member of its group.

### `PUT /v1/expenses/{expense_id}`
Same body as create (without `id`). Allowed for the creator or the payer. Recomputes splits; bumps `updated_at`.

### `DELETE /v1/expenses/{expense_id}`
Soft delete (creator or payer). → `204`.

## 6. Balances

### `GET /v1/groups/{group_id}/balances`
```json
{
  "members": [
    { "user_id": "uuid-A", "display_name": "Vandit", "net_paise": 275000, "is_current_member": true },
    { "user_id": "uuid-B", "display_name": "Riya",   "net_paise": -103500, "is_current_member": true },
    { "user_id": "uuid-C", "display_name": "Aman",   "net_paise": -171500, "is_current_member": true }
  ],
  "transfers": [
    { "from_user": "uuid-C", "to_user": "uuid-A", "amount_paise": 171500 },
    { "from_user": "uuid-B", "to_user": "uuid-A", "amount_paise": 103500 }
  ]
}
```
Sum of `net_paise` is always 0.

## 7. Settlements

### `POST /v1/groups/{group_id}/settlements`
```json
{ "id": "uuid (client)", "from_user": "uuid-C", "to_user": "uuid-A", "amount_paise": 171500, "note": "GPay" }
```
Rules: both users are members (current or former); `from_user ≠ to_user`; the caller must be `from_user` or `to_user` (you can't record a payment between two other people). Idempotent like expenses. → `201`.

### `GET /v1/groups/{group_id}/settlements?limit=&cursor=`
Newest first, keyset paginated on `(settled_at DESC, id DESC)`.

### `DELETE /v1/settlements/{settlement_id}`
Only `created_by`, within 24 hours (undo a mistake). → `204`.

## 8. Rate limiting

Per user: 120 requests/minute; `POST`s 30/minute. Exceeding → `429` with `Retry-After`. (In-memory limiter is fine for one Render instance; document that it resets on restart.)
