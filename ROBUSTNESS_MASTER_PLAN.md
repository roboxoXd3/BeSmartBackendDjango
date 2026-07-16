# Be Smart — Robustness Master Plan (2-Day Sprint)

**Date:** 2026-07-02
**Purpose:** Single consolidated priority list of everything outstanding, with exact issue + exact resolution, split by owner (Avi = backend/Django, Hitesh = frontend/vendor-dashboard), scoped to what's realistically achievable in 2 focused days. This is a **planning document for your review** — nothing here has been filed to ClickUp yet.

**How to read this:** Each item has a Priority (P0 = drop everything / P1 = today / P2 = tomorrow / P3 = backlog, after this sprint), the exact problem, the exact fix, where the code is, and an effort estimate. Items are grouped by owner so each person can work their list independently, with cross-dependencies called out explicitly.

---

## 🚦 Priority legend

| Priority | Meaning |
|---|---|
| 🔴 P0 | Security/data-integrity risk live right now — fix before anything else |
| 🟠 P1 | Confirmed bug affecting real users — fix today (Day 1) |
| 🟡 P2 | Important, not on fire — fix tomorrow (Day 2) |
| 🟢 P3 | Backlog — good to do, doesn't fit this sprint, don't force it |

---

# 👤 HITESH (Frontend — vendor-dashboard)

## 🔴 P0 — Security: IDOR vulnerabilities (do this first, today, before anything else)

**The issue:** Six API routes trust a resource ID or `vendorId` sent by the client without verifying it belongs to the logged-in vendor. Any vendor can act on another vendor's data.

**The fix pattern (same for all 6):** Never use a client-supplied `vendorId`. Always derive the vendor from the session cookie (`getSessionFromCookie()` — already exists and is used correctly on the *safe* routes below, copy that pattern), then add an ownership filter to every query.

| # | File | Exact problem | Exact fix |
|---|---|---|---|
| 1 | `src/app/api/products/[id]/route.js` GET | `.eq('id', id)` with no vendor filter — any vendor can read any product | Add `.eq('vendor_id', sessionVendorId)` to the query |
| 2 | `src/app/api/products/[id]/route.js` PUT | Same — any vendor can edit any product | Same fix — verify ownership before the update RPC/query runs |
| 3 | `src/app/api/products/[id]/route.js` DELETE | Same — any vendor can delete any product | Same fix — verify ownership before delete |
| 4 | `src/app/api/reviews/route.js` PUT | Updates `product_reviews` by `id` with no check that the review's product belongs to the caller | Before updating, look up the review's `product_id` → confirm that product's `vendor_id` matches session vendor; 403 if not |
| 5 | `src/app/api/product-qa/route.js` PUT | Same pattern, **plus** accepts `vendorId` directly from the request body (line ~202) with zero validation | Remove client-supplied `vendorId` entirely from this route's logic; derive server-side, same ownership check as #4 |
| 6 | `src/app/api/orders/route.js` PUT | Accepts `vendorId` from request body (line ~172) and uses it directly in the query filter (line ~192) — a vendor can claim any order is theirs | Derive `vendorId` from session only; ignore/reject any `vendorId` in the request body |

**Also check (lower confidence, verify while you're in there):**
7. `src/app/api/products/route.js` POST — accepts `vendorId` from body without validating against session. Confirm whether downstream logic double-checks this; if not, apply the same server-side-derivation fix.

**Reference — routes that already do this correctly, copy their pattern:**
- `src/app/api/bank-accounts/[id]/route.js` — `.eq('id', id).eq('vendor_id', vendor.id)` where `vendor` comes from the session
- `src/app/api/storage/delete/route.js` — checks the file path starts with `vendors/${sessionVendorId}/`
- `src/app/api/vendor/support/tickets/[id]/messages/route.js` — `.eq('id', ticketId).eq('vendor_id', vendor.id)`

**Effort:** ~3-4 hours (mechanical once the pattern is applied once; the hard part is #4/#5 which need an extra lookup query to find the owning vendor before checking).

**How to verify the fix worked:** Log in as Vendor A, try to GET/PUT/DELETE a product ID that belongs to Vendor B (grab a real ID from the DB or from Vendor B's own dashboard). Should get a 403/404, not the data.

---

## 🔴 P1 — `vendor.id` null-crash pattern (5 locations)

**The issue:** `vendor` comes from `useAuth()` (`src/contexts/AuthContext.jsx`), starts as `null`, and only populates after an async session check completes. Multiple places access `vendor.id` without checking it's non-null first — crashes with `Cannot read properties of null (reading 'id')` if the user acts before auth finishes loading, or if the session expires mid-session.

**The fix (3-layer guard, apply at each location):**
1. In the component: don't render the interactive form/button until `AuthContext`'s `loading` is `false` and `vendor` is non-null — show a skeleton/spinner instead.
2. In the handler function itself: first line, `if (!vendor?.id) { alert('Still loading your profile, please wait and try again.') return }` (or better UX than `alert`, see P2 item below).
3. On the trigger button: `disabled={loading || !vendor?.id}`.

| # | File:Line | Trigger |
|---|---|---|
| 1 | `src/app/(Tabs)/products/components/hooks/useProductSubmit.js:56,86` | Product create/update submit (already reported by a client — this is the one that triggered this whole audit) |
| 2 | `src/app/(Tabs)/size-charts/page.jsx:125` | Save handler for size charts |
| 3 | `src/app/(Tabs)/products/bulk-upload/media/page.jsx:62` | Bulk image upload handler |
| 4 | `src/app/(Tabs)/products/bulk-upload/media/page.jsx:91` | Bulk video upload handler |
| 5 | `src/app/(Tabs)/products/bulk-upload/page.jsx:95` | ZIP bulk-upload handler |

**Also worth a quick look (guarded but fragile, lower priority within P1):**
- `src/app/(Tabs)/products/components/ProductsFilterBar.jsx:79` — has an early-return guard already, but there's a small race window; add `vendor?.id` optional chaining as a cheap extra safety net.

**Effort:** ~1-2 hours — same fix pattern repeated 5 times.

**How to verify:** Throttle network to slow 3G in devtools, reload the page, immediately try to trigger each action before the page finishes loading — should show a friendly "still loading" message, not crash.

---

## 🟠 P1 — Remove debug/test routes from production

**The issue:** 9 routes are dev-only scaffolding, one is a genuine credential leak.

| Route | Priority within this item | Why |
|---|---|---|
| `src/app/api/setup-vendor-accounts/route.js` | 🔴 Do first | **Hardcoded plaintext test credentials, reachable in production right now** |
| `src/app/api/debug-login/route.js` | 🟠 | Verbose auth logging exposed |
| `src/app/api/debug-current-auth/route.js` | 🟠 | Exposes session/token details |
| `src/app/api/setup-rls/route.js` | 🟡 | Tests RLS policies, lower risk |
| `src/app/api/debug-products/route.js` | 🟡 | Exposes raw vendor-ID debug info |
| `src/app/api/test-auth/route.js` | 🟡 | |
| `src/app/api/test-followers/route.js` | 🟡 | Writes test data |
| `src/app/api/test-supabase/route.js` | 🟢 | Minimal — env var lengths only |

**The fix:** Delete these route files entirely, or if any are still needed for local dev, gate them behind `if (process.env.NODE_ENV !== 'production') { ... }` at the top of each handler.

**Effort:** ~30 minutes.

---

## 🟡 P2 — Migrate the 22 confirmed-safe routes to Django

**The issue:** 40 of 56 vendor-dashboard routes still talk to Supabase directly instead of the Django backend, which is meant to be the single source of truth. 22 of them have a confirmed-working Django equivalent already (verified by reading the actual Django view code, not just the URL).

**The fix:** Swap `getSupabaseServer()` / `supabase.from(...)` calls for `besmartRequest()` calls (the helper already exists in `src/lib/besmart-api.js` and is used correctly by the 5 routes already on Django).

**⚠️ Dependency:** Do this AFTER the P0 IDOR fixes above are done and verified. Don't migrate a vulnerable route as-is — either fix the vulnerability first in the Supabase version, or migrate straight to Django (which is already correctly scoped) instead of patching Supabase first. **Recommendation: for the 6 IDOR routes specifically, migrate straight to Django instead of patching Supabase — it's already safe there, so this kills two birds at once.**

**Suggested batches (do in this order):**
1. **Auth → `vendors/sessions/` BFF** — replaces `auth/vendor-login`, `auth/validate-session`, `auth/refresh-session`, `auth/logout` (4 routes → 1 consistent system). Do this first since everything else depends on auth being solid.
2. Profile/KYC group: `my-vendor-profile`, `vendor-profile`, `vendor-kyc`, `storage/kyc-upload`, `bank-accounts` (+`[id]`)
3. Products group: `products` (GET), `products/[id]` (**this is also the IDOR fix — migrate straight to Django**), `products/size-chart-visibility` (⚠️ blocked, see Avi's P1 below)
4. Orders/payouts group: `orders` (**also an IDOR route — migrate to Django**), `recent-orders`, `payouts`, `escrow`, `transactions`
5. Reviews/Q&A group: `reviews` (**also IDOR**), `product-qa` (**also IDOR**)
6. Remaining: `categories`, `currency`, `currency/convert`, `dashboard-stats` (+`sales-trend`), `vendor-stats` (+`customer-locations`), `vendor/support/tickets` (+messages)

**Do NOT migrate yet (blocked on Avi's fixes, see his list):** `products/bulk-upload` (stub), `payouts/summary`-dependent flows if any (crash bug).

**Effort:** ~4-6 hours across all batches — this is mechanical but there are a lot of routes; realistically this is most of Day 2 for one person.

---

## 🟢 P3 — Backlog (good to do, don't force into 2 days)

- **Replace `alert()` error handling** with proper toast/modal UX across the product form and anywhere else it's used — currently shows raw JS error text (`"Error: Cannot read properties of null..."`) directly to real vendors.
- **Delete 5 duplicate/dead product-edit files**: `page_old.jsx`, `page_old_backup.jsx`, `page_new.jsx`, `page_old_tabs.jsx`, `page_enhanced.jsx` in `src/app/(Tabs)/products/edit/[id]/` — confirm nothing references them first.
- **Add rollback/compensating logic** to the multi-step product-create flow (Django create → Supabase upsert same ID → R2 media upload) — currently no visible handling if step 2 or 3 fails after step 1 succeeds.

---

# 👤 AVI (Backend — Django)

## 🔴 P0/P1 — Live bugs (fix regardless of anything else, these are broken right now)

| # | Issue | File:Line | Exact fix | Effort |
|---|---|---|---|---|
| 1 | **`vendors/payouts/summary/` crashes on every call** — `EscrowTransaction` used but never imported | `vendors/views.py:832-870` | Add `from .models import EscrowTransaction` (or wherever it lives) to the top of the file/method | 15 min |
| 2 | **`size-chart-visibility` PATCH is a silent no-op** — returns success but writes nothing to the DB | `vendors/views.py:717-719` | Implement the actual field update (looks like it should toggle a boolean on the product, e.g. `product.size_chart_visible = request.data.get('visible'); product.save()` — confirm exact field name against the model) | 1-2 hrs |
| 3 | **`support/tickets/<id>/messages/` has no GET** (can post messages, can't list them) **and its ownership check does nothing** (`if ticket.vendor.user != self.request.user: pass` — the `pass` should be a `raise PermissionDenied` or `return Response(..., status=403)`) | `support/views.py:37-49` | (a) Add a GET method/view to list messages for a ticket, scoped the same way the POST already resolves the ticket. (b) Fix the `pass` to actually deny access. | 1-2 hrs |

## 🟠 P1 — Gunicorn/infra (confirm and fix — this was left unresolved)

**The issue:** Procfile was updated to `--workers 2 --timeout 60` and pushed to `main`, but production is still running the old single-worker command with no timeout override. The deployed commit hash matches (`63a943f8` and later), so the *code* is deploying fine — the *start command* isn't picking up the Procfile change. Strong signal this is a Railway dashboard "Custom Start Command" override that takes precedence over the Procfile — need to check Railway's service settings directly (Settings → Deploy → Start Command field) for the `BeSmartBackendDjango` service.

**The fix:** Either clear the override so Railway falls back to the Procfile, or update the override field directly to `gunicorn besmart_backend.wsgi:application --workers 2 --timeout 60 --log-file -`.

**Effort:** 15-30 min once in the Railway dashboard.

## 🟠 P1 — Missing timeouts on external calls (already scoped, ClickUp ticket 86d3hhd3h exists)

- Add `timeout=15` to every `requests.post()`/`requests.get()` call to Squad in `payments/services/squad_service.py` and `payments/views.py` (~5-6 call sites).
- Add `timeout=20.0` to every `OpenAI(api_key=api_key)` client instantiation in `ai_services/*.py` (4 files).

**Why this still matters even after the worker fix:** more workers reduces blast radius, but an unbounded external call can still tie up a worker indefinitely without a timeout. Both fixes are needed together.

**Effort:** ~1 hour.

## 🟡 P2 — Migration-readiness (needed before Hitesh can safely migrate the corresponding routes)

| # | Issue | File:Line | Exact fix | Effort |
|---|---|---|---|---|
| 1 | **`bulk-upload` is a stub** — `return Response({'message': 'Bulk upload logic pending'}, status=501)` | `vendors/views.py:709-710` | Implement real CSV bulk-upload logic (parse multipart CSV + optional media, create products under the authenticated vendor) — this blocks Hitesh from migrating the ZIP/CSV bulk-upload feature off Supabase | Half day+ (biggest single item on this list) |
| 2 | **`analytics/metrics` returns hardcoded fake data** — `conversion_rate: 0.05` and `return_rate: 0.01` are constants, not computed | `vendors/views.py:456-475` | Compute real values from order/view data, or if that data doesn't exist yet, clearly document to Hitesh that these two fields are placeholders so the frontend doesn't display them as real numbers | 2-4 hrs (depends on whether the underlying tracking data exists) |
| 3 | **`stats/customer-locations` returns hardcoded mock data** — always "Lagos" (real count) + "Abuja" (always 0), never queries real shipping addresses | `vendors/views.py:477-493` | Query actual order/shipping-address data grouped by region for the vendor's orders | 2-3 hrs |
| 4 | **`dashboard/stats` has a duplicate-field bug** — `monthlyRevenue` is literally a copy of `totalSales` | `vendors/views.py:344-393` | Confirm with product/Hitesh whether these should differ (e.g. monthly vs. all-time); implement correctly or remove the duplicate field | 30 min - 1 hr |

## 🟢 P3 — Genuinely missing endpoints (backlog, scope with product first)

- Analytics funnel (conversion-stage breakdown) — no Django equivalent exists at all
- Per-product performance breakdown — `analytics/metrics` is vendor-wide, not per-product
- Orders CSV export — fine to keep as a dashboard-side transform if it reads from the (now-migrated) Django orders endpoint first
- Generic file-delete endpoint — Django only has uploads, no matching delete
- Vendor-application resubmit as a distinct flow

## 🟢 P3 — Security hardening (not urgent, but real — flag for a future pass)

- **`approval_status` on the Product model is writable by any authenticated vendor via a direct API call** — the serializer doesn't mark it read-only, and `perform_create` doesn't check `vendor.verification_status` before allowing product creation. Today this is safe in practice because the vendor-dashboard app always explicitly sends `approval_status: 'pending'` — but nothing on the server stops a vendor from bypassing the official app (e.g. via curl with their own valid token) and self-approving their own products. Recommend: mark `approval_status` read-only in `ProductDetailSerializer`, and gate `perform_create`/`perform_update` on `vendor.status == 'approved'`.

---

# 📅 Suggested 2-day sequencing

## Day 1 — Security + confirmed bugs (both in parallel)

**Hitesh:**
1. IDOR fixes (6 routes) — morning
2. `vendor.id` null-crash guards (5 locations) — early afternoon
3. Remove debug/test routes — late afternoon, 30 min

**Avi:**
1. `payouts/summary` import fix — first thing, 15 min
2. Confirm/fix Railway start-command override (gunicorn workers) — first thing, 30 min
3. Add Squad/OpenAI timeouts — late morning
4. `size-chart-visibility` real implementation — afternoon
5. `support/tickets/messages` GET + fix ownership check — afternoon

**End of Day 1 checkpoint:** all P0/P1 items done, both people verify their own fixes live.

## Day 2 — Migration + data-quality fixes

**Avi (morning):**
- `analytics/metrics` real data
- `stats/customer-locations` real data
- `dashboard/stats` field fix
- Start on `bulk-upload` real implementation if time allows (may spill into Day 3)

**Hitesh (all day, can start once Avi's Day-1 items are confirmed):**
- Migrate the 22 confirmed-safe routes in the batch order listed above
- Prioritize the auth → `vendors/sessions/` migration first (everything else benefits from it being solid)
- For the 6 IDOR routes specifically: migrate straight to Django rather than patching-then-migrating

**End of Day 2 checkpoint:** auth on Django BFF, ~26-28 of 40 Supabase-direct routes migrated, all P0/P1 security and crash bugs fixed and verified.

## Explicitly NOT in this 2-day scope (backlog, P3 items above)
- `bulk-upload` full implementation (likely spills past Day 2 given its size)
- The 5 genuinely-missing endpoints
- `alert()` → toast UX cleanup
- Dead file removal
- Multi-step create-flow rollback logic
- `approval_status` security hardening
- Vendor subscriptions feature (product decision needed first — is anyone building the frontend for it?)

---

# ✅ For context — already shipped this session (not part of the 2-day plan, listed for completeness)

- Mobile app (`ecom_app`): Nigerian/UK address parsing, infinite refresh-loop fix, filter crash fixes, splash auth routing, print/opacity codemods — all merged to `main` and pushed.
- Supabase storage quota crisis — resolved via safe cleanup (2.88 GB freed), login restored.
- Q&A/Reviews 403 auth bug — Avi fixed (`SupabaseAuthentication` registered in DRF settings), deployed.
- `ecomWebsite` — pulled Hitesh's 19 commits, removed hardcoded secrets from a storage-backup script, gitignored `mcp.json`.

---

**Next step once you've reviewed this:** tell me how you want this split into ClickUp — as-is (one ticket per numbered item), grouped by priority tier, or grouped by day. I'll file whatever structure you pick.
