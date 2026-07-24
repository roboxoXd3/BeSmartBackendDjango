# Backend TODO — everything currently open (2026-07-08)

Single source of truth for what the backend team still needs to fix, checked
against `staging` as of today. Older docs (`BACKEND_N+1_PERFORMANCE_BUGS`,
`ECOM_WEBSITE_PRODUCT_LISTING_PERF_BUG`, `ADMIN_PANEL_TESTING_NOTES`,
`VENDOR_PANEL_TESTING_NOTES`) are superseded by this one — most of what they
listed is already fixed (verified below); this doc is just the remainder.

---

## 1. N+1 queries make nearly every list endpoint slow (High)

**Confirmed still broken today:** `GET /api/products/?paginate=true` takes
~15s locally (243 queries for 20 products).

Root cause, same pattern repeated across endpoints: `SerializerMethodField`s
and `.only()` querysets that don't batch related-object lookups, so Django
fires one extra query per row per field.

Affected endpoints:
- `GET /api/products/`, `/featured/`, `/new-arrivals/`, `/on-sale/`, `/search/`
  — `.only()` in `get_optimized_product_queryset()` (`products/views.py`)
  excludes fields `ProductListSerializer` actually reads, and
  `get_vendor_name()` does a per-row `Vendor.objects.get()` instead of a
  batched subquery/annotate (category already does this correctly — copy
  that pattern for vendor).
- `GET /api/vendors/own-products/` — same serializer, same fix.
- `GET /api/admin/vendors/` — 3 separate per-row `.count()` calls plus an
  unselected `user` FK (~81 queries/page).
- `GET /api/admin/orders/` — `get_vendors()` rebuilds querysets instead of
  reusing the already-prefetched `items`, plus an unselected
  `user__profile` FK (~60-65 queries/page).
- `GET /api/admin/payouts/` — unselected `vendor`/`vendor__user` FK chain
  plus a per-row bank-account `.filter().first()` (~61 queries/page).
- `GET /api/admin/products/` — same serializer as above, missing even the
  category optimization the storefront view has (~41 queries/page).
- `GET /api/admin/users/` — missing `select_related('profile')`
  (~21-22 queries/page).

**Fix:** add the missing fields to `.only()` (or drop `.only()`), replace
per-row lookups with `Subquery`/`annotate`/`select_related` following the
pattern already used for category, and collapse repeated `.count()` calls
into a single `.annotate(Count(...))`.

*(Full query-log detail for the product-listing case specifically: see
`ECOM_WEBSITE_PRODUCT_LISTING_PERF_BUG_2026-07-08.md`.)*

---

## 2. Product Q&A is completely broken — both asking and listing (Critical)

`ProductQuestion.status` model default is `'published'`, but the DB check
constraint only allows `pending`/`answered`/`hidden` — every "ask a
question" request 500s. Separately, the list endpoint filters on
`status='published'`, a value that can never legally exist, so even a
manually-inserted question would never display.

**Fix:** default `status` to `'pending'` (set it explicitly in
`ProductQAListCreateView.perform_create` too), and change the list
endpoint's filter to `status__in=['answered']` (or whatever the intended
public-visibility rule is).

---

## 3. Support ticket replies are completely broken, both sides (Critical)

Nobody — vendor or admin — can currently reply to a support ticket.

- **Vendor side** (`POST /api/support/tickets/{id}/messages/`):
  `SupportMessageView.perform_create` never sets `sender_role`, so it falls
  back to the model default `''`, which the DB check constraint (only
  `vendor`/`admin` allowed) rejects. Fix: pass `sender_role='vendor'`
  explicitly.
- **Admin side** (`POST /api/admin/support-tickets/{id}/reply/`):
  `SupportTicketAdminViewSet.reply` calls
  `SupportMessage.objects.create(..., message=message_text)` — the model
  field is `message_content`, not `message`, so this always raises
  `TypeError`. Fix: rename the kwarg.

Both confirmed live via the actual vendor/admin panel UI, not just in theory.

*(Full repro detail for all three items above: see
`BACKEND_WRITE_PATH_BUGS_2026-07-08.md`.)*

---

## Already fixed — no action needed (listed so nothing gets re-reported)

Verified against `staging` today:
- Admin dashboard stats 500 (`Sum`/`Avg` alias collision) — fixed.
- Loyalty transactions had no endpoint — fixed (`LoyaltyTransactionAdminViewSet`).
- Admin vendors list had no filtering/ordering — fixed.
- Vendor own-products had no stats endpoint — fixed (`statistics` action).
- Vendor analytics had no time-bucketed endpoint — fixed (`views-over-time`).
- Escrow release/hold/refund had no write endpoint — fixed, tested end-to-end.
- Payout `cancelled` status was silently ignored — fixed, tested end-to-end.
