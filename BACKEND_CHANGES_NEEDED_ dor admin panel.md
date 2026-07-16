# Backend Changes Needed — Admin Panel

**Date:** 2026-07-06
**For:** Backend developer (BeSmartBackendDjango)
**Context:** The admin panel has been migrated so that **all data now comes
from Django** (only login/session auth stays on Supabase, same pattern as the
vendor dashboard). The build is clean and every route either calls Django or
has a documented reason it still calls Supabase.

The items below are the **only** things that need a backend change for the
admin panel to work fully. Ordered by impact. Anything not listed here
already works end-to-end.

---

## 1. Fix vendor logo field name — real bug, not just a gap

**Impact:** High — every order/vendor list shows a broken/missing logo.

`OrderAdminSerializer.get_vendors()` and related admin serializers read
`vendor.logo_url`, but the actual field on the `Vendor` model is
`business_logo`. This isn't a missing feature — it's a typo that makes vendor
logos always render null across the admin dashboard, orders, and vendor
list/detail views.

**Change:** fix the field reference to `business_logo` (or add a `logo_url`
property alias on the model/serializer).

---

## 2. Expand `ProductListSerializer` (admin) — same gap as vendor dashboard

**Impact:** High — affects admin products table, recent-activity feed, dashboard export.

`ProductAdminViewSet`'s list action uses `ProductListSerializer`, which is
missing: `approval_status`, `rejection_reason`, vendor id/name, `subtitle`,
`mrp`, `currency`, `colors`, `brand`, `created_at`. Admin currently has to do
an extra per-row detail fetch to show these (N+1, workable for now but slow at
scale).

**Change:** add these fields to `ProductListSerializer`, or reuse
`ProductDetailSerializer` for the list action (same fix needed here as item 2
in the vendor-dashboard doc — one change covers both).

---

## 3. Expand admin user serializer with profile fields

**Impact:** High — affects Users page, user detail, user export.

`UserManagementSerializer` only returns `{id, email, is_active, date_joined}`.
There's no nested profile data (`full_name`, `phone_number`, `role`,
`image_path`) the way `users.serializers.UserSerializer` already provides
elsewhere in the codebase. Also, `UserAdminCreateUpdateSerializer` has no
`phone_number`/`role` fields, and status is a plain `is_active` boolean where
the old system had 4 states (Active/Suspended/Pending/Inactive).

**Change:** extend the admin user serializer to include the linked `Profile`
fields (mirror the existing `UserSerializer`), and add `phone_number`/`role`
to create/update.

---

## 4. Add per-user order history to the admin API

**Impact:** Medium — Users page shows 0 orders / $0 spent for everyone.

There's no way to filter `OrderAdminViewSet` by customer, so `orders`,
`ordersCount`, and `totalSpent` are all zeroed out on the admin Users page and
export.

**Change:** add a `user_id`/`customer_id` filter to `OrderAdminViewSet`, or a
small `GET /api/admin/users/{id}/orders/` summary endpoint.

---

## 5. Add an admin-wide escrow endpoint

**Impact:** Medium — admin Escrow page has no data source at all.

Django only exposes `/api/vendors/escrow/`, hard-scoped to the logged-in
vendor (`VendorEscrowViewSet`). There is no admin-wide `EscrowTransaction`
viewset.

**Change:** add an admin `EscrowTransaction` viewset (list/filter across all
vendors), matching the `IsAdminUser` pattern used elsewhere in `admin_api`.

---

## 6. Loyalty program has almost no admin API surface

**Impact:** Medium — the whole Loyalty Program admin section is unusable.

- Rewards/badges: only public, read-only, active-only endpoints exist
  (`LoyaltyRewardListView`, `LoyaltyBadgeListView`) — no admin create/update/
  delete, no `include_inactive`, no redemption-count data.
- Earning rules: `LoyaltyEarningRule` model exists but has **zero** API
  surface anywhere (not in `loyalty/urls.py` or `admin_api`).
- Loyalty users list: no endpoint joins `User` with `LoyaltyPoints` for
  tier/points filtering — `LoyaltyAdminViewSet` only has a per-user
  "award points" action, nothing to list/search users by loyalty status.
- Analytics: no aggregation endpoint at all over points/vouchers/
  transactions/badges.

**Change:** add admin CRUD for rewards/badges, a read/write endpoint for
earning rules, a loyalty-users list endpoint (join `User`+`LoyaltyPoints`),
and a loyalty analytics aggregate endpoint.

---

## 7. Payout approval doesn't actually trigger a transfer

**Impact:** Medium — approving a payout in the admin UI only flips a status flag.

Django's payout status action just updates `VendorPayout.status`; unlike the
old Supabase-era flow, it never calls Squad to initiate the actual transfer.
Status choices also lack `cancelled` (reject currently maps to `failed`), and
`PayoutAdminSerializer` doesn't expand vendor logo/email or bank details.

**Change:** wire the approve action to actually call Squad's transfer API (or
confirm that's intentionally handled elsewhere), add a `cancelled` status
choice, and expand `PayoutAdminSerializer` with vendor/bank details.

---

## 8. No write endpoints for site content (hero section, contact info, banners)

**Impact:** Medium — several admin content-editing forms have no save path.

- `HeroSectionView` and `ContactInfoView` are read-only/`AllowAny` — no PUT.
- `ContactBranchListView` is read-only — no admin CRUD for `ContactBranch`.
- Banner image upload (`AdminBannerImageUploadView`) requires an existing
  banner id, but the admin UI needs to upload an image **before** the banner
  is created (new-banner flow).
- No generic media-upload/delete endpoint for the hero section.

**Change:** add admin-authenticated write endpoints for hero section, contact
info, and contact branches; allow banner image upload without a pre-existing
banner id (or add a two-step create-then-attach flow the frontend can use).

---

## 9. No admin-wide bank-accounts or support-ticket access

**Impact:** Medium — Admin can't view/manage vendor bank accounts or support tickets.

- `VendorBankAccountViewSet` is scoped to `vendor__user=request.user` — no
  admin listing/approval endpoint exists.
- `SupportTicketViewSet` filters to `vendor__user=request.user`, and
  `SupportMessageView` raises `PermissionDenied` unless the ticket belongs to
  the requesting vendor — this blocks admin read/reply entirely.

**Change:** add admin-scoped viewsets/permission branches (`IsAdminUser` OR
vendor-owner) for both bank accounts and support tickets + messages, so
support staff can see and respond to any vendor's ticket.

---

## 10. No category image upload endpoint

**Impact:** Low — category image upload/delete still goes through Supabase Storage directly.

Only products and banners have image upload endpoints in `admin_api`; there's
no equivalent for categories.

**Change:** add a category image upload/delete endpoint, mirroring the
existing product/banner ones.

---

## 11. Add richer admin analytics + a self-service admin profile endpoint

**Impact:** Low — a few analytics widgets and the "my profile" page are limited.

- Analytics: Django only has `SystemStatsView` (30d/60d rolling) and
  `AdminRevenueChartView` (flat daily trend) — no arbitrary date ranges,
  `period`/`compareWith` params, or per-category/per-vendor breakdowns.
- Admin profile: `AdminUserViewSet` has no "me" action, and there's no
  verified mapping from the logged-in admin's Supabase session to their
  Django admin-user row.

**Change:** if wanted, add date-range/comparison params to the analytics
endpoints, and a `GET/PATCH /api/admin/admin-users/me/` endpoint.

---

## Not required — for your awareness only

- **Customer-facing loyalty routes** (`/api/loyalty/*` — rewards,
  award-points, redeem, balance, transactions, vouchers) authenticate the
  *end customer*, not the admin, so they're a different concern from this
  migration and were left untouched. Separately: these routes call
  `supabase.auth.getUser()` with no token argument on a
  `persistSession: false` service-role client — that almost certainly already
  fails in production, independent of anything here. Worth a look, but it's a
  pre-existing issue, not something this migration introduced.
- **Admin account management** (`users/list`, `users/create`,
  `users/[id]/role` — i.e. managing *admin* accounts, not customers) stays on
  Supabase by design — it's part of the auth layer, not app data.
- **Payment/webhook routes** (`payments/*`, `webhooks/squad/transfer`,
  `orders/[id]/status`) are external-provider callbacks verified by signature,
  not admin-session requests — correctly left as-is, not part of this
  migration's scope.
- **Auth stays on Supabase** by design (admin login, session). No backend
  change wanted here — the one adjacent change made was storing the Supabase
  access/refresh token in the admin session's `device_info` so the admin
  panel can call Django with a Bearer token, mirroring the vendor dashboard.
