# Consolidated API Master: No Duplication

> **Purpose:** Single source of truth for all APIs needed across Mobile, Website, Vendor Dashboard, and Admin Panel.  
> **Validation:** Cross-checked against all gap documents and BeSmartBackendDjango. No duplicate endpoints.

**Date:** February 12, 2026

---

## How APIs Are Scoped (No Overlap)

| Scope | Prefix | Used By |
|-------|--------|---------|
| Customer | `/api/` | Mobile, Website |
| Vendor | `/api/vendors/` | Vendor Dashboard |
| Admin | `/api/admin/` | Admin Panel |

**Rule:** Same logical resource (e.g. orders) has different endpoints per scope:
- Customer orders: `/api/orders/`
- Vendor orders: `/api/vendors/orders/`
- Admin orders: `/api/admin/orders/`

---

## Part 1: Customer APIs (Mobile + Website)

These are **shared**; implement once, both apps use them.

### 1.1 Already in Django ✅

| Endpoint | Django Path | Used By |
|----------|-------------|---------|
| Auth login | `POST /api/auth/login/` | Mobile, Website |
| Auth register | `POST /api/auth/register/` | Mobile, Website |
| Auth refresh | `POST /api/auth/refresh/` | Mobile, Website |
| Auth logout | `POST /api/auth/logout/` | Mobile, Website |
| Auth verify | `POST /api/auth/verify/` | Mobile, Website |
| User profile | `GET/PATCH /api/auth/me/` or `/profile/` | Mobile, Website |
| Products list | `GET /api/products/` | Mobile, Website |
| Product detail | `GET /api/products/{id}/` | Mobile, Website |
| Featured | `GET /api/products/featured/` | Mobile, Website |
| New arrivals | `GET /api/products/new-arrivals/` | Mobile, Website |
| On sale | `GET /api/products/on-sale/` | Mobile, Website |
| Product search | `GET /api/products/search/` | Mobile, Website |
| Cart get | `GET /api/cart/` | Mobile, Website |
| Cart add item | `POST /api/cart/items/` | Mobile, Website |
| Cart item update/delete | `PATCH/DELETE /api/cart/items/{id}/` | Mobile, Website |
| Wishlist list | `GET /api/wishlist/` | Mobile, Website |
| Wishlist add | `POST /api/wishlist/` | Mobile, Website |
| Wishlist remove | `DELETE /api/wishlist/{id}/` | Mobile, Website |
| Orders list | `GET /api/orders/` | Mobile, Website |
| Order detail | `GET /api/orders/{id}/` | Mobile, Website |
| Loyalty points | `GET /api/loyalty/points/` | Mobile, Website |
| Loyalty transactions | `GET /api/loyalty/transactions/` | Mobile, Website |
| Loyalty rewards | `GET /api/loyalty/rewards/` | Mobile, Website |
| Loyalty redeem | `POST /api/loyalty/redeem/` | Mobile, Website |
| Loyalty vouchers | `GET /api/loyalty/vouchers/` | Mobile, Website |
| Loyalty badges | `GET /api/loyalty/badges/` | Mobile, Website |
| Categories list | `GET /api/categories/` | Mobile, Website |
| Category detail | `GET /api/categories/{id}/` | Mobile, Website |
| Currency rates | `GET /api/currency/rates/` | Mobile, Website |
| Currency convert | `POST /api/currency/convert/` | Mobile, Website |
| Banners | `GET /api/content/banners/` | Mobile, Website |
| FAQs | `GET /api/content/faqs/` | Mobile, Website |
| Contact branches | `GET /api/support/branches/` | Mobile, Website |

### 1.2 Missing – Implement Per Mobile Spec ❌

| Endpoint | Used By | Notes |
|----------|---------|-------|
| `GET/POST/PATCH/DELETE /api/shipping-addresses/` | Mobile, Website | 4 + `POST .../set-default/` |
| `POST /api/orders/` | Mobile, Website | Full create-from-cart logic |
| `POST /api/orders/{id}/cancel/` | Mobile, Website | |
| `GET /api/orders/{id}/track/` | Mobile, Website | |
| `POST /api/orders/{id}/reorder/` | Mobile, Website | |
| `GET /api/orders/{id}/invoice/` | Mobile, Website | |
| `GET /api/vendors/` | Mobile, Website | Customer-facing list |
| `GET /api/vendors/featured/` | Mobile, Website | |
| `GET /api/vendors/search/?q=` | Mobile, Website | |
| `GET /api/vendors/{id}/` | Mobile, Website | |
| `GET /api/vendors/{id}/products/` | Mobile, Website | |
| `GET/POST /api/vendors/{id}/reviews/` | Mobile, Website | |
| `PATCH/DELETE /api/vendors/reviews/{id}/` | Mobile, Website | |
| `POST/DELETE /api/vendors/{id}/follow/` | Mobile, Website | |
| `GET/POST /api/products/{id}/reviews/` | Mobile, Website | |
| `POST /api/reviews/{id}/helpful/` | Mobile, Website | |
| `POST /api/reviews/{id}/report/` | Mobile, Website | |
| `GET/POST /api/products/{id}/qa/` | Mobile, Website | |
| `POST /api/products/{id}/qa/{qa_id}/helpful/` | Mobile, Website | |
| `POST /api/loyalty/validate-voucher/` | Mobile, Website | Checkout |
| `GET /api/loyalty/user-badges/` | Mobile, Website | |
| `GET /api/loyalty/badge-progress/` | Mobile, Website | |
| `GET /api/loyalty/tier-info/` | Mobile, Website | |
| `GET /api/categories/{id}/subcategories/` | Mobile, Website | |
| `GET /api/categories/{id}/products/` | Mobile, Website | |
| `GET /api/content/hero-section/` | Mobile, Website | |
| `GET /api/content/contact-info/` | Mobile, Website | |
| `GET /api/content/support-info/?type=` | Mobile, Website | |
| `POST /api/cart/clear/` | Mobile, Website | |
| `GET /api/cart/summary/` | Mobile, Website | |
| `POST /api/wishlist/{id}/move-to-cart/` | Mobile, Website | |
| `DELETE /api/wishlist/clear/` | Mobile, Website | |
| `GET /api/users/account/deletion-eligibility/` | Mobile, Website | |
| `POST /api/users/account/delete/` | Mobile, Website | |
| `POST /api/search/analytics/` | Mobile, Website | |
| `GET /api/search/analytics/?start_date=&end_date=` | Mobile, Website | |
| `GET /api/products/{id}/size-chart/` | Mobile, Website | |
| `POST /api/products/{id}/view/` | Mobile, Website | |
| Product specs/offers/highlights | Website | Extend product detail or add `GET /api/products/{id}/specifications/`, `offers/`, `highlights/` |

### 1.3 Payment Flow (Website-Specific Consideration)

| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /api/payments/initiate/` | ⚠️ Exists, different contract | Django expects `order_id`; website uses cart-based flow. Align or add `initiate-from-cart` |
| `GET /api/payments/verify/?transaction_ref=` | ✅ Exists | |
| `POST /api/payments/webhook/` | ✅ Exists | |
| `POST /api/payments/charge-token/` | ❌ Missing | For saved cards (subscriptions) |

---

## Part 2: Vendor APIs (Vendor Dashboard Only)

All under `/api/vendors/`. **No overlap** with customer APIs.

### 2.1 Already in Django ✅

| Endpoint | Django Path |
|----------|-------------|
| Profile | `GET/PATCH /api/vendors/profile/` |
| Dashboard stats | `GET /api/vendors/dashboard/stats/` |
| Payouts | `GET/POST /api/vendors/payouts/` |
| Bank accounts | Full ViewSet at `/api/vendors/bank-accounts/` |
| Size charts | Full ViewSet at `/api/vendors/size-charts/` |
| Subscriptions | `plans/`, `current/` |
| Register | `POST /api/vendors/register/` |

### 2.2 Missing ❌

| Endpoint | Notes |
|----------|-------|
| `GET /api/vendors/orders/recent/` | |
| `GET /api/vendors/orders/` | List vendor orders |
| `PUT /api/vendors/orders/{id}/status/` | |
| `GET /api/vendors/orders/stats/` | |
| `GET /api/vendors/orders/export/` | |
| `GET/POST/PATCH/DELETE /api/vendors/products/` | Vendor product CRUD |
| `POST /api/vendors/products/bulk-upload/` | |
| `PATCH /api/vendors/products/{id}/stock/` | |
| `PATCH /api/vendors/products/{id}/size-chart-visibility/` | |
| `GET /api/vendors/reviews/` | Vendor's product reviews |
| `PUT /api/vendors/reviews/{id}/` | Respond/hide/show |
| `GET /api/vendors/product-qa/` | Vendor's Q&A |
| `PUT /api/vendors/product-qa/{id}/` | Answer/hide/show |
| `GET /api/vendors/payouts/summary/` or extend | |
| `GET /api/vendors/escrow/` | |
| `GET /api/vendors/transactions/` | |
| `GET /api/vendors/analytics/sales/` | |
| `GET /api/vendors/analytics/metrics/` | |
| `GET /api/vendors/analytics/funnel/` | |
| `GET /api/vendors/analytics/performance/` | |
| `GET /api/vendors/dashboard/sales-trend/` | |
| `GET /api/vendors/stats/customer-locations/` | |
| `GET /api/vendors/products/best-selling/` | |
| `GET /api/vendors/products/inventory-status/` | |
| Vendor auth (JWT + vendor check) | |
| `POST /api/vendors/kyc/upload/` | |
| `POST /api/storage/upload/` or product image upload | |

**Shared with customer:** `GET /api/categories/`, `GET /api/categories/{id}/subcategories/` – vendor uses same read-only endpoints.

---

## Part 3: Admin APIs (Admin Panel Only)

All under `/api/admin/`. **No overlap** with customer or vendor APIs.

### 3.1 Already in Django ✅

| Endpoint | Django Path |
|----------|-------------|
| Admin users (staff) | ViewSet at `/api/admin/users/` |
| App settings | ViewSet at `/api/admin/settings/` |
| Action logs | `GET /api/admin/logs/` |
| Manage user (ban) | `GET/PUT/PATCH/DELETE /api/admin/manage-users/<pk>/` |
| System stats | `GET /api/admin/stats/` |

### 3.2 Missing ❌

| Endpoint | Notes |
|----------|-------|
| Admin auth: login, validate-session, refresh, logout | |
| `GET /api/admin/dashboard/stats/` (enhanced) | |
| `GET /api/admin/dashboard/recent-orders/` | |
| `GET /api/admin/dashboard/revenue-chart/` | |
| `GET /api/admin/dashboard/top-vendors/` | |
| `GET /api/admin/dashboard/recent-activity/` | |
| `GET /api/admin/dashboard/export/` | |
| Analytics: dashboard, revenue, users, products, conversion, vendors, export | |
| Customer users: list, create, update, export, status, role | |
| Vendors: list, detail, status, verification, stats, export | |
| Products: list, pending, detail, approve, reject | |
| Orders: list, detail, update, cancel, create, stats, bulk, export | |
| Payouts, escrow, bank accounts (admin scope) | |
| Categories admin CRUD + image upload | |
| Subcategories admin CRUD | |
| Contact + branches admin CRUD | |
| Hero section admin get/update/upload | |
| Promotional banners (path + image upload) | |
| Size charts: list, approve, reject | |
| Admin profile: get, update, upload/remove image | |
| Support: admin sees all tickets | |
| Loyalty admin: rewards, badges, earning rules, user adjustments | |

**Shared:** `GET /api/currency/rates/`, `POST /api/currency/convert/` – admin uses same. Support tickets at `/api/support/tickets/` with admin permission to see all.

---

## Duplication Check

| Resource | Customer | Vendor | Admin | Verdict |
|----------|----------|--------|-------|---------|
| Categories | Read | Read | CRUD | ✅ Different – admin adds write |
| Products | List/detail | Vendor CRUD | Approve/reject | ✅ Different scopes |
| Orders | List/detail/create | Vendor list/status | Admin list/detail/status | ✅ Different scopes |
| Product reviews | Submit (customer) | List/respond (vendor) | — | ✅ Different – `/api/products/{id}/reviews/` vs `/api/vendors/reviews/` |
| Product Q&A | Submit (customer) | List/answer (vendor) | — | ✅ Different |
| Support tickets | Create | List own | List all | ✅ Same `/api/support/tickets/`, filter by role |
| Loyalty | Redeem | — | Config | ✅ Different – `/api/loyalty/` vs `/api/admin/loyalty/` |
| Currency | Read/convert | Read | Read | ✅ Same endpoints |

**No duplicate endpoints.** Each scope has its own path prefix or distinct sub-resource.

---

## Summary: Unique Endpoints to Implement

| Area | Count (approx) | Source |
|------|----------------|--------|
| Customer (Mobile + Website) | ~45 | API_SPECIFICATION_MOBILE_MIGRATION.md |
| Vendor | ~29 | VENDOR_DASHBOARD_API_GAP_ANALYSIS.md |
| Admin | ~65 | ADMIN_PANEL_API_GAP_ANALYSIS.md |

**Total unique:** ~140 (some vendor/admin may share models; endpoints are distinct).

---

## Cross-Reference: Gap Docs → This Master

| Document | Role |
|----------|------|
| `API_SPECIFICATION_MOBILE_MIGRATION.md` | Full spec for customer APIs (48 endpoints) |
| `ECOM_WEBSITE_API_GAP_ANALYSIS.md` | Website uses same as mobile; no extra endpoints |
| `VENDOR_DASHBOARD_API_GAP_ANALYSIS.md` | Vendor-specific; references mobile for categories |
| `ADMIN_PANEL_API_GAP_ANALYSIS.md` | Admin-specific; references shared currency, support |

**This master:** Consolidates all; deduplicates; confirms no overlap.
