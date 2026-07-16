# Backend Changes Needed — Vendor Dashboard

**Date:** 2026-07-04
**For:** Backend developer (BeSmartBackendDjango)
**Context:** The vendor dashboard has been fully migrated so that **all data
now comes from Django** (only login/session auth stays on Supabase). Every
route builds, lints, and returns correctly against the live Django API.

The items below are the **only** things that still need a backend change for
the dashboard to work 100% correctly. They're ordered by impact. Nothing else
is required — everything not listed here already works end-to-end.

---

## 1. Add a customer name to vendor orders  →  *fixes "Unknown Customer" everywhere*

**Impact:** High — visible on every order.
**Where the dashboard shows it:** Recent Orders (dashboard), Escrow list.

Django's `OrderSerializer` only exposes the customer's `user` id, with no name
or email. There's no vendor-facing way to resolve who placed an order, so the
dashboard currently displays **"Unknown Customer"** on every row.

**Change:** add the customer's display name (and email if available) to the
vendor order responses — either as fields on `OrderSerializer`
(e.g. `customer_name`, `customer_email`) or a dedicated lookup endpoint,
scoped so a vendor can only see customers who ordered from them.

Affected endpoints: `GET /api/vendors/orders/`, `GET /api/vendors/orders/recent/`,
`GET /api/vendors/escrow/`.

---

## 2. Add missing fields to `ProductListSerializer`  →  *fixes product cards*

**Impact:** High — visible on the main Products page.

The product list (`GET /api/vendors/own-products/`) uses `ProductListSerializer`,
which is missing fields the product cards render:

- `description` — cards show generic fallback text instead of the real description
- `approval_status` + `rejection_reason` — the approve/pending/rejected badge and
  rejection notice never appear
- `video_url` — the "Video" badge never appears
- `colors` — color swatches are always empty
- `subtitle`, `brand`

`ProductDetailSerializer` (used for single-product GET) already has all of
these via `fields = '__all__'` — only the **list** serializer is missing them.

**Change:** add those fields to `ProductListSerializer` (or reuse
`ProductDetailSerializer` for the `list` action).

---

## 3. Add server-side filtering + adjustable page size to 3 list endpoints  →  *fixes performance at scale*

**Impact:** Medium — works today, but gets slow as a vendor's catalog/history grows.

These three list endpoints have **no** `filterset_fields`/`search_fields` and a
**fixed** `PAGE_SIZE=20` with no `page_size_query_param`:

- `VendorOwnProductViewSet` — needs search (name/SKU/category), category filter,
  status filter, ordering (name, price)
- `VendorOrderViewSet` — needs status filter, date range, ordering
- `SupportTicketViewSet` — needs status filter, priority filter, search

The dashboard needs all of these, so it currently **fetches every page from
Django and filters/sorts in the Next.js layer**. That works, but a vendor with
a large catalog triggers many sequential requests on each list load.

**Change:** add `filterset_fields` (or a `get_queryset` query-param filter —
`VendorProductReviewViewSet` and `VendorProductQAViewSet` already do this well,
supporting `product_id`/`status`/`rating`/`has_answer`) plus a
`page_size_query_param` to those three viewsets. Once done, the frontend can be
switched back to a single filtered request.

---

## 4. Add a "resubmit rejected application" endpoint  →  *unblocks the last Supabase-dependent flow*

**Impact:** Medium — one flow still can't leave Supabase without this.

When a vendor's application is rejected, they edit it and resubmit for review,
which needs to reset `status → 'pending'` and clear
`rejection_reason`/`admin_notes`. Django correctly marks `status` and
`verification_status` **read-only** on `/api/vendors/profile/` (a vendor
shouldn't be able to un-reject themselves via a generic profile update) — but
that means there's no Django path for the *legitimate* resubmit action, so it's
the one data flow still running on Supabase.

**Change:** add a dedicated `POST /api/vendors/resubmit/` (narrower than the
profile PATCH) that resets `status`/`verification_status` to `pending` and
clears the rejection fields, for the authenticated vendor only.

---

## 5. Build (or confirm dropping) the two analytics endpoints with no backend

**Impact:** Medium — two analytics widgets still read from Supabase.

`analytics/funnel` (product views → cart → checkout → purchased) and
`analytics/performance` (per-product performance) have **no Django endpoint at
all**, and need view / add-to-cart / checkout event-tracking data that Django
doesn't currently capture. They're the only remaining analytics widgets still
on Supabase.

**Change:** if these are still wanted, add event tracking on the Django side
and build `GET /api/vendors/analytics/funnel/` and
`GET /api/vendors/analytics/performance/`. If they're being dropped, let us
know and we'll remove the widgets.

*(Also note: `VendorAnalyticsMetricsView` still returns a hardcoded
`conversion_rate: 0.05`. That route turned out to be unused by the dashboard,
so it's low priority — but if it's ever wired back up, that number is fake.)*

---

## 6. KYC document upload: store documents keyed by type

**Impact:** Low — works via a workaround, but the workaround is fragile.

`POST /api/vendors/kyc/upload/` stores `verification_documents` as a flat
**array** (`[{name, url, uploaded_at}]`). The dashboard needs it keyed by
document type (`{id_proof: {...}, business_license: {...}, address_proof: {...}}`)
to track which of the 3 required documents are present.

The frontend currently uploads via Django, then immediately re-`PATCH`es
`verification_documents` back into the object-keyed shape — it works, but it
briefly writes a shape the model doesn't expect.

**Change:** have `VendorKYCUploadView` accept a `document_type` param and store
documents keyed by type (instead of appending to an array).

---

## Not required — for your awareness only

- **Escrow status filter:** Django's `EscrowTransaction.status` has only
  `held`/`released`/`refunded` (no `pending`). The dashboard's "Pending" tab is
  mapped to `held`. Fine as-is unless you want a distinct pending state.
- **Two orphaned routes** (`/api/storage/upload`, `/api/storage/delete`) are
  unused dead code in the frontend — no backend equivalent needed; can be
  deleted from the frontend at some point.
- **Auth stays on Supabase** by design (login, session, initial vendor
  application). No backend change wanted here.
