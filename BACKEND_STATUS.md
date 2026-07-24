# Backend status — fixed vs pending

Admin panel **business data → Django**.  
**Supabase only for admin auth** (login, sessions, `admin_users`, profile images) and a few **file storage** uploads noted below.

---

## Fixed (ready to deploy)

| # | What was broken | What we fixed |
|---|-----------------|---------------|
| 1 | Admin product create could not set vendor | Admin product API accepts `vendor_id` / `approval_status` |
| 2 | Product reject ignored the reason | Saves `rejection_reason`; approve clears it |
| 3 | Payout transfer crashed (`is_primary`) | Uses `is_default`; saves `squad_transaction_ref` |
| 4 | Escrow hold after release didn’t undo balance | Hold subtracts from `available_balance` (locked) |
| 5 | No admin size-chart approve/reject | `/api/admin/size-charts/` + approve/reject |
| 6 | No admin contact-branch CRUD | `/api/admin/contact-branches/` |
| 7 | Squad transfer webhook on Supabase | Django webhook; idempotent (only from `processing`) |
| 8 | Escrow search 500 (`reference_id`) | Search uses `vendor__business_name` only |
| 9 | Transfer initiate could 500 / mis-read Squad | try/except + accept `success` or `status == 200` |
| 10 | Analytics category chart empty | BFF returns `categories` / `vendors` keys UI expects |
| 11 | Product form image remove could drop wrong file | Blob vs existing URL indexes fixed |
| 12 | Payment webhook/verify & legacy order status on Supabase | Proxied to Django |
| 13 | `orderService.updateOrder` used unsupported PUT | Status → Django status action; other fields → PATCH |

**Django files:** `admin_api/serializers.py`, `admin_api/views.py`, `admin_api/urls.py`, `payments/views.py`, `vendors/views.py`

---

## Still needs fixing (must do / track)

| # | Issue | What to do |
|---|--------|------------|
| 1 | New admins can get **403** on Django APIs | On admin create/login set Django `is_staff=True` (manual until then) |
| 2 | Squad webhooks in production | Point Squad (or BFF) at Django `/api/payments/webhook/` with signature header |
| 3 | Order detail **status history** always empty | Django has no admin endpoint for `order_status_history` — add one if UI needs history |
| 4 | Loyalty overview recent redemptions **points** | Django analytics doesn’t return points per redemption — UI shows “—” until API adds it |
| 5 | Legacy `ecom_admin/app/api/loyalty/*` stubs | Unused by admin UI; still hit Supabase if called — migrate or delete |
| 6 | Dev-only routes `check-subcategories-table` / `create-subcategories-table` | Still hit Supabase; not used in UI — delete or ignore |

---

## Intentional (not bugs)

| Area | Why OK |
|------|--------|
| Admin login / sessions / `admin_users` / roles | Auth stays on Supabase |
| Admin profile image upload | Supabase Storage (`admin-profiles`) |
| Hero section media upload | Supabase Storage for files; metadata via Django |
| Analytics vendor breakdown empty | Django revenue chart has categories, not vendors yet |

---

## Deploy order

1. Deploy **Django**  
2. Deploy **ecom_admin**  
3. Smoke test: product approve/reject + create with vendor, size charts, contact branches, analytics categories, payout transfer (staging), payment webhook
