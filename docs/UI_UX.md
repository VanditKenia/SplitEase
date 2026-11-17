# UI / UX Specification

## 1. Principles

1. **One number that matters**: on every screen, "you owe / you're owed" is the most prominent thing.
2. **Fast entry**: adding a typical expense takes 3 fields and 1 tap.
3. **No surprises with money**: the split preview shows the exact paise that will be saved.
4. **Friendly, not financial**: light theme by default, warm accent, plain language ("Riya owes you").

## 2. Design system

### Colours (light theme default; dark theme optional)

| Token | Hex | Use |
|---|---|---|
| `bg` | `#F7F8FA` | App background |
| `surface` | `#FFFFFF` | Cards, sheets |
| `textPrimary` | `#111827` | Main text |
| `textSecondary` | `#6B7280` | Labels, metadata |
| `accent` | `#0F9D8A` | Primary buttons, FAB, selection (teal) |
| `owed` | `#16A34A` | "You're owed" (positive) |
| `owe` | `#DC2626` | "You owe" (negative) |
| `settled` | `#6B7280` | "Settled up" (zero) |
| `warning` | `#D97706` | Waking-up / offline banners |

Always pair colour with words and sign: "you owe −₹1,715.00", never colour alone.

### Typography
Material 3 defaults (or Inter). Amounts use `FontFeature.tabularFigures()`.
| Style | Size/weight | Use |
|---|---|---|
| display | 32 / bold | Group balance hero |
| title | 20 / semibold | Screen titles |
| body | 16 / regular | List rows |
| label | 13 / medium | Metadata, chips |

### Shape & spacing
4-pt grid · card radius 16 · bottom-sheet radius 24 · min tap target 48dp · avatars: initials in a coloured circle (colour derived from user id).

## 3. Screens

### 3.1 Sign in / Sign up
Logo + tagline "Split bills, not friendships." · email, password (show/hide) · primary button · switch link · errors inline ("Wrong email or password").

### 3.2 Groups (home)
```
┌───────────────────────────────┐
│ SplitEase              (👤)   │
│ ┌───────────────────────────┐ │
│ │ Overall                   │ │
│ │ You're owed ₹4,320.00     │ │ ← sum across groups
│ └───────────────────────────┘ │
│ Flat 302           you owe    │
│ 4 members      −₹1,250.50     │ ← red
│ Goa trip       you're owed    │
│ 6 members      +₹5,570.50     │ ← green
│ Office lunch     settled up   │
│                               │
│   [ Join with code ]   ( + )  │
└───────────────────────────────┘
```
Pull to refresh. Empty state with both actions.

### 3.3 Group screen (tabs)
App bar: group name, share-invite icon. Header card: "You owe ₹1,250.50" / "You're owed …" / "All settled up 🎉". Tabs: **Expenses · Balances · Members**. FAB **Add expense** on Expenses tab.

#### Expenses tab (feed)
```
[ 🔍 Search expenses          ]
[Paid by ▾] [Date ▾] [Clear]
── November 2026 ─────────────
14 Nov  Dinner at Thalassa     ₹3,450.00
        Vandit (you) paid · you lent ₹1,725.00   ← green
12 Nov  Electricity bill       ₹2,100.00
        Riya paid · you owe ₹525.00        ← red
── October 2026 ──────────────
...
        (spinner while loading more)
```
Month headers flattened into the list · tiles are lightweight (no images) · "That's everything" footer · skeleton rows for first load.

#### Balances tab
- Member list with net amounts (sorted: most owed first).
- **Suggested payments** card: "Aman → Vandit ₹1,715.00"; rows involving me show **Record payment**.
- **History** link → settlements list.

#### Members tab
Invite code in large monospace (`K7Q2MX`) with Copy / Share / (owner) Rotate · member rows with role badge · **Leave group** (destructive, bottom).

### 3.4 Add / Edit expense (full screen)
```
Title          [ Dinner                 ]
Amount   ₹     [ 3450                   ]
Paid by        [ (V) You            ▾   ]
Date           [ Today, 15 Nov      ▾   ]
Notes (opt.)   [                        ]

Split   ( Equal | Exact | % | Shares )
 ☑ (V) You          ₹1,150.00
 ☑ (R) Riya         ₹1,150.00
 ☑ (A) Aman         ₹1,150.00
 ─────────────────────────────
 Total ₹3,450.00 ✓

[            Save            ]
```
- **Exact**: rupee field per person; footer shows remaining/over.
- **%**: percent field per person (2 decimals); footer "Total 100% ✓" or what's left.
- **Shares**: stepper per person (min 1 when included).
- Unchecking a person removes them from the split.
- Save disabled until valid; server errors shown inline.
- Amount keyboard: decimal; max 2 decimals enforced while typing.

### 3.5 Expense detail
Title, amount (display style), "Paid by Vandit on 14 Nov", split type chip, list of each person's share (highlight me), notes, created/edited info · Edit / Delete (when allowed).

### 3.6 Settle-up sheet
"Record a payment" · From → To (pre-filled from suggestion; me must be one side) · amount (pre-filled, editable for partial) · note (e.g. "GPay") · **Confirm** · success snackbar "Payment recorded".

### 3.7 Profile
Display name (editable) · email · Sign out · app version.

## 4. States checklist (every data screen)

| State | Treatment |
|---|---|
| Loading | Skeletons, not blank screens |
| Empty | Friendly message + next action |
| Error | Short message + Retry |
| Offline | Amber banner, last data shown, writes disabled |
| Waking server | Amber banner "Waking up the server…" with spinner |

## 5. Micro-interactions

- Haptic + snackbar on save/settle.
- Balance numbers animate (AnimatedSwitcher) when they change.
- Copy invite code → "Copied" toast.
- Swipe left on a feed item → Delete (with Undo snackbar for 5 s, then the API call).
