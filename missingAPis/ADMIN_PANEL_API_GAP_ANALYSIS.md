# Admin Panel → Django Backend: API Gap Analysis

> **Purpose:** Identify APIs required by the admin panel (Next.js) and what exists vs what is missing in BeSmartBackendDjango.  
> **Related docs:** `VENDOR_DASHBOARD_API_GAP_ANALYSIS.md`, `API_SPECIFICATION_MOBILE_MIGRATION.md`

**Date:** February 12, 2026  
**Admin Panel:** `adminPanel` (Next.js + Supabase)  
**Backend:** `BeSmartBackendDjango`

---

## Overview

The admin panel uses Next.js API routes that proxy to Supabase. To migrate to Django, we need Django endpoints that match the admin panel’s behavior.

---

## Django Admin APIs That Exist

| Endpoint | Django Path | Notes |
|----------|-------------|-------|
| Admin users (staff accounts) | `GET/POST/PUT/PATCH/DELETE /api/admin/users/` | `AdminUserViewSet` – admin accounts only |
| App settings | `GET/POST/PUT/PATCH/DELETE /api/admin/settings/` | `AppSettingsViewSet` |
| Action logs | `GET /api/admin/logs/` | `AdminActionLogListView` |
| Manage customer (ban/unban) | `GET/PUT/PATCH/DELETE /api/admin/manage-users/<pk>/` | `UserManagementView` – single user |
| System stats | `GET /api/admin/stats/` | `SystemStatsView` – total_users, total_vendors, total_orders, pending_vendors |
| Currency rates | `GET /api/currency/rates/` | ✅ |
| Currency convert | `POST /api/currency/convert/` | ✅ |
| Support tickets | `GET/POST /api/support/tickets/` | Customer/vendor scope; admin needs all tickets |
| Promotional banners | `GET/POST/PUT/PATCH/DELETE /api/content/banners-manage/` | `PromotionalBannerViewSet` |
| Orders (customer) | `GET/POST /api/orders/`, `GET/PUT /api/orders/<id>/` | Customer orders; admin needs list/detail/status/export |

---

## Admin Panel API Inventory (by area)

### 1. Admin Auth

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `POST /api/auth/admin-login` | — | ❌ Missing |
| `GET /api/auth/validate-session` | — | ❌ Missing |
| `POST /api/auth/refresh-session` | — | ❌ Missing |
| `POST /api/auth/logout` | — | ❌ Missing |
| `POST /api/auth/reset-admin-password` | — | ❌ Missing |
| `POST /api/auth/create-admin-users` | `AdminUserViewSet` (POST) | ⚠️ Partial – structure may differ |

**Notes:** Admin auth uses Supabase `admin_sessions`, `admin_users`. Django has `AdminUser`, `AdminSession`. Need admin login endpoint that creates session (or JWT) and validates it.

---

### 2. Dashboard

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/dashboard/stats` | `GET /api/admin/stats/` | ⚠️ Partial – different shape |
| `GET /api/admin/dashboard/recent-orders` | — | ❌ Missing |
| `GET /api/admin/dashboard/revenue-chart` | — | ❌ Missing |
| `GET /api/admin/dashboard/top-vendors` | — | ❌ Missing |
| `GET /api/admin/dashboard/recent-activity` | `GET /api/admin/logs/` | ⚠️ Similar – may need alignment |
| `GET /api/admin/dashboard/export` | — | ❌ Missing |

**Required shape for stats:** `totalRevenue`, `totalOrders`, `totalVendors`, `totalProducts`, `avgOrderValue`, `ordersChange`, `vendorsChange`, `revenueChange`, `avgOrderValueChange`.

---

### 3. Analytics

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/analytics` | — | ❌ Missing |
| `GET /api/admin/analytics/dashboard` | — | ❌ Missing |
| `GET /api/admin/analytics/revenue` | — | ❌ Missing |
| `GET /api/admin/analytics/users` | — | ❌ Missing |
| `GET /api/admin/analytics/products` | — | ❌ Missing |
| `GET /api/admin/analytics/conversion` | — | ❌ Missing |
| `GET /api/admin/analytics/vendors` | — | ❌ Missing |
| `GET /api/admin/analytics/export` | — | ❌ Missing |

**Params:** `dateFrom`, `dateTo`, `period`, `compareWith`, `format`.

---

### 4. User Management (Customer Users)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/users` | — | ❌ Missing (AdminUserViewSet serves admin staff) |
| `GET /api/admin/users/list` | — | ❌ Missing |
| `GET /api/admin/users/{id}` | `GET /api/admin/manage-users/<pk>/` | ⚠️ Partial |
| `PUT /api/admin/users/{id}` | `PUT /api/admin/manage-users/<pk>/` | ⚠️ Partial |
| `DELETE /api/admin/users/{id}` | `DELETE /api/admin/manage-users/<pk>/` | ✅ Soft delete |
| `POST /api/admin/users/create` | — | ❌ Missing |
| `GET /api/admin/users/export` | — | ❌ Missing |
| `PUT /api/admin/users/{id}/status` | — | ❌ Missing |
| `PUT /api/admin/users/{id}/role` | — | ❌ Missing |

**Notes:** Admin panel manages **customer users** (profiles), not admin staff. Django `AdminUserViewSet` is for admin accounts. Need customer user list with pagination, filters (search, status, role), create, update, export, status, role.

---

### 5. Vendor Management

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/vendors` | — | ❌ Missing |
| `GET /api/admin/all-vendors` | — | ❌ Missing |
| `GET /api/admin/vendors/{id}` | — | ❌ Missing |
| `PATCH /api/admin/vendors/{id}/status` | — | ❌ Missing |
| `PATCH /api/admin/vendors/{id}/verification` | — | ❌ Missing |
| `GET /api/admin/vendors/stats` | — | ❌ Missing |
| `GET /api/admin/vendors/export` | — | ❌ Missing |

**Notes:** Admin needs to list vendors, approve/reject/suspend, verify KYC. Django vendor app is vendor-facing only.

---

### 6. Product Management (Admin Approval)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/products` | — | ❌ Missing |
| `GET /api/admin/products/pending` | — | ❌ Missing |
| `GET /api/admin/products/{id}` | — | ❌ Missing (products app is customer-facing) |
| `POST /api/admin/products/{id}/approve` | — | ❌ Missing |
| Product reject | — | ❌ Missing |

**Notes:** Products app exposes customer list/detail. Admin needs full list, pending products, approve/reject.

---

### 7. Order Management (Admin)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/orders` | — | ❌ Missing |
| `GET /api/admin/orders/{id}` | — | ❌ Missing (orders app returns customer’s orders) |
| `PUT /api/admin/orders/{id}` | — | ❌ Missing |
| `DELETE /api/admin/orders/{id}` | — | ❌ Missing (cancel) |
| `POST /api/admin/orders` | — | ❌ Missing |
| `GET /api/admin/orders/stats` | — | ❌ Missing |
| `PUT /api/admin/orders/bulk` | — | ❌ Missing (status, cancel, labels, notifications) |
| `GET /api/admin/orders?export=true` | — | ❌ Missing |
| `GET /api/admin/orders/search-suggestions` | — | ❌ Missing |
| `PATCH /api/orders/{id}/status` | — | ❌ Missing |

**Notes:** Orders app is customer-scoped. Admin needs list (no user filter), detail, update, cancel, create, stats, bulk actions, export, search suggestions, status change.

---

### 8. Payouts, Escrow, Bank Accounts

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/payouts` | — | ❌ Missing |
| `POST /api/admin/payouts` | — | ❌ Missing (process payout) |
| `GET /api/admin/escrow` | — | ❌ Missing |
| `GET /api/admin/escrow?stats=true` | — | ❌ Missing |
| `GET /api/admin/bank-accounts` | — | ❌ Missing |
| `POST /api/admin/bank-accounts` | — | ❌ Missing (approve/reject) |

**Notes:** Django has vendor payouts and bank accounts. Admin needs platform-wide view and ability to approve payouts and bank accounts.

---

### 9. Categories & Subcategories (Admin CRUD)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/categories` | `GET /api/categories/` | ⚠️ Partial (no admin CRUD) |
| `POST /api/admin/categories` | — | ❌ Missing |
| `GET /api/admin/categories/{id}` | `GET /api/categories/{id}/` | ⚠️ Partial |
| `PUT /api/admin/categories/{id}` | — | ❌ Missing |
| `DELETE /api/admin/categories/{id}` | — | ❌ Missing |
| `POST /api/admin/categories/upload-image` | — | ❌ Missing |
| `DELETE /api/admin/categories/delete-image` | — | ❌ Missing |
| `GET /api/admin/subcategories` | — | ❌ Missing |
| `POST /api/admin/subcategories` | — | ❌ Missing |
| `GET /api/admin/subcategories/{id}` | — | ❌ Missing |
| `PUT /api/admin/subcategories/{id}` | — | ❌ Missing |
| `DELETE /api/admin/subcategories/{id}` | — | ❌ Missing |

**Notes:** Django categories are read-only for customers. Subcategories may not exist; admin needs full CRUD and image upload.

---

### 10. Contact Info & Branches

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/contact` | — | ❌ Missing |
| `PUT /api/admin/contact` | — | ❌ Missing |
| `GET /api/admin/contact/branches` | `GET /api/support/branches/` | ⚠️ Check path/scope |
| `POST /api/admin/contact/branches` | — | ❌ Missing |
| `GET /api/admin/contact/branches/{id}` | — | ❌ Missing |
| `PUT /api/admin/contact/branches/{id}` | — | ❌ Missing |
| `DELETE /api/admin/contact/branches/{id}` | — | ❌ Missing |

**Notes:** `ContactBranchListView` exists under support. Verify path and whether admin CRUD is needed.

---

### 11. Hero Section

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/hero-section` | — | ❌ Missing |
| `PUT /api/admin/hero-section` | — | ❌ Missing |
| `POST /api/admin/hero-section/upload-media` | — | ❌ Missing |

**Notes:** Content app has banners, FAQs. Hero section is a separate concept; may need new model/endpoints.

---

### 12. Promotional Banners

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/promotional-banners` | `GET /api/content/banners-manage/` | ⚠️ Path differs |
| `POST /api/admin/promotional-banners` | ViewSet has create | ⚠️ Path differs |
| `GET /api/admin/promotional-banners/{id}` | ViewSet | ⚠️ Path differs |
| `PUT /api/admin/admin/promotional-banners/{id}` | ViewSet | ⚠️ Path differs |
| `DELETE /api/admin/promotional-banners/{id}` | ViewSet | ⚠️ Path differs |
| `POST /api/admin/promotional-banners/upload-image` | — | ❌ Missing |

**Notes:** Django `PromotionalBannerViewSet` at `/api/content/banners-manage/`. Admin panel expects `/api/admin/promotional-banners`. Align paths or add proxy. Add image upload.

---

### 13. Size Charts (Admin Approval)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/size-charts` | — | ❌ Missing |
| `POST /api/admin/size-charts/{id}/approve` | — | ❌ Missing |
| `POST /api/admin/size-charts/{id}/reject` | — | ❌ Missing |

**Notes:** Django has `VendorSizeChartTemplateViewSet` at `/api/vendors/size-charts/`. Admin needs list of pending size charts and approve/reject actions.

---

### 14. Admin Profile

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/profile` | — | ❌ Missing |
| `PUT /api/admin/profile` | — | ❌ Missing |
| `POST /api/admin/profile/upload-image` | — | ❌ Missing |
| `DELETE /api/admin/profile/remove-image` | — | ❌ Missing |

**Notes:** AdminUser has `profile_image_url`. Need endpoints for current admin profile and image upload.

---

### 15. Support (Admin View)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/support/tickets` | `GET /api/support/tickets/` | ⚠️ Scope – admin needs all tickets |
| `GET /api/admin/support/admin-users` | — | ❌ Missing |
| `GET /api/admin/support/tickets/{id}/messages` | `GET /api/support/tickets/<id>/messages/` | ⚠️ Path differs |
| `POST /api/admin/support/tickets/{id}/messages` | `POST /api/support/tickets/<id>/messages/` | ⚠️ Path differs |

**Notes:** Support API exists. Ensure admin can see all tickets (no user/vendor filter). Add admin-users list if needed for assignment.

---

### 16. Loyalty (Admin Management)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/loyalty/analytics` | — | ❌ Missing |
| `GET /api/admin/loyalty/users` | — | ❌ Missing |
| `POST /api/admin/loyalty/users/{id}/adjust` | — | ❌ Missing |
| `GET /api/admin/loyalty/rewards` | `GET /api/loyalty/rewards/` | ⚠️ Customer read-only |
| `POST /api/admin/loyalty/rewards` | — | ❌ Missing |
| `PUT /api/admin/loyalty/rewards/{id}` | — | ❌ Missing |
| `DELETE /api/admin/loyalty/rewards/{id}` | — | ❌ Missing |
| `GET /api/admin/loyalty/badges` | `GET /api/loyalty/badges/` | ⚠️ Customer read-only |
| `GET /api/admin/loyalty/badges/{id}` | — | ❌ Missing |
| `PUT /api/admin/loyalty/badges/{id}` | — | ❌ Missing |
| `GET /api/admin/loyalty/earning-rules` | — | ❌ Missing |

**Notes:** Loyalty app exposes customer endpoints. Admin needs CRUD for rewards, badges, earning rules, and user point adjustments.

---

### 17. Misc / DB Helpers

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `GET /api/admin/check-subcategories-table` | — | N/A (Supabase migration helper) |
| `POST /api/admin/create-subcategories-table` | — | N/A (Supabase migration helper) |

**Notes:** Supabase-specific; not needed in Django if subcategories are modeled normally.

---

### 18. Shared Endpoints (Used by Admin)

| Admin Panel | Django | Status |
|-------------|--------|--------|
| `PATCH /api/orders/{id}/status` | — | ❌ Missing |
| `GET /api/currency` | `GET /api/currency/rates/` | ⚠️ Path differs |
| `POST /api/currency/convert` | `POST /api/currency/convert/` | ✅ |
| `POST /api/loyalty/award-points` | — | ❌ Missing |
| Squad webhook | `POST /api/payments/webhook` | Check Squad integration |
| Payment verify/success/failed | Payment views | Check paths |

---

## Summary: Missing API Groups

### Critical

| # | Endpoint / Feature | Notes |
|---|--------------------|-------|
| 1 | Admin auth (login, validate-session, refresh, logout) | Admin session or JWT flow |
| 2 | `GET /api/admin/dashboard/stats` | Align with admin panel shape |
| 3 | `GET /api/admin/dashboard/recent-orders` | Recent orders list |
| 4 | `GET /api/admin/dashboard/revenue-chart` | Revenue time series |
| 5 | Customer users: list, create, update, export, status, role | Different from AdminUserViewSet |
| 6 | Vendors: list, detail, status, verification, stats, export | Admin vendor management |
| 7 | Products: list, pending, detail, approve, reject | Admin product approval |
| 8 | Orders: list, detail, update, cancel, create, stats, bulk, export | Admin order management |
| 9 | `PATCH /api/orders/{id}/status` | Order status update (used by admin) |

### High

| # | Endpoint / Feature | Notes |
|---|--------------------|-------|
| 10 | Payouts: list, process | Admin payout management |
| 11 | Escrow: list, stats | Admin escrow view |
| 12 | Bank accounts: list, approve/reject | Admin bank account approval |
| 13 | Categories: admin CRUD + image upload | Extend categories app |
| 14 | Subcategories: full CRUD | Add subcategories if needed |
| 15 | Size charts: list, approve, reject | Admin size chart approval |
| 16 | Admin profile: get, update, upload/remove image | Current admin profile |
| 17 | Loyalty rewards: admin CRUD | Extend loyalty app |
| 18 | Loyalty badges: admin CRUD | Extend loyalty app |
| 19 | Loyalty users: list, adjust points | Admin point adjustment |
| 20 | Loyalty earning rules: list, CRUD | Admin config |

### Medium

| # | Endpoint / Feature | Notes |
|---|--------------------|-------|
| 21 | Analytics: dashboard, revenue, users, products, conversion, vendors, export | Admin analytics |
| 22 | Hero section: get, update, upload media | Content / hero model |
| 23 | Promotional banners: align path + image upload | Path + upload |
| 24 | Contact: get, update | Contact info |
| 25 | Contact branches: full CRUD | Branches CRUD |
| 26 | Top vendors, recent activity, export | Dashboard extras |
| 27 | Support: ensure admin sees all tickets | Permission / filtering |

---

## Overlap with Other Specs

| Area | Admin Panel | Vendor Dashboard | Mobile | Action |
|------|-------------|------------------|--------|--------|
| Categories | Admin CRUD | Read | Read | Single source: Django categories + admin CRUD |
| Subcategories | Admin CRUD | Read | Read | Add subcategories if needed |
| Orders | Admin list/detail/status | Vendor list/status | Customer list/detail | Admin and vendor are distinct scopes |
| Products | Admin approve | Vendor CRUD | Customer list | Admin approval separate |
| Support | Admin all tickets | Vendor own tickets | Customer tickets | Same backend, different filters |
| Currency | Read, convert | Read | Read | Use existing Django currency API |
| Loyalty | Admin config | — | Customer redeem | Admin CRUD for rewards/badges/rules |

---

## Total Count

| Category | Existing (Django) | Missing | Partial |
|----------|------------------|---------|---------|
| Auth | 0 | 5 | 1 |
| Dashboard | 1 | 4 | 1 |
| Analytics | 0 | 8 | 0 |
| Users | 1 | 7 | 2 |
| Vendors | 0 | 7 | 0 |
| Products | 0 | 5 | 0 |
| Orders | 0 | 10 | 0 |
| Payouts/Escrow/Bank | 0 | 6 | 0 |
| Categories | 1 | 8 | 2 |
| Contact | 0 | 7 | 1 |
| Hero | 0 | 3 | 0 |
| Banners | 1 | 1 | 4 |
| Size Charts | 0 | 3 | 0 |
| Admin Profile | 0 | 4 | 0 |
| Support | 1 | 1 | 3 |
| Loyalty (admin) | 0 | 9 | 2 |
| Misc | 0 | 2 | 2 |

**Approximate new endpoints/features:** ~90+ (some are enhancements or path alignment).

---

## Recommended Implementation Order

**Phase 1 – Admin auth and dashboard**
1. Admin login, session validation, refresh, logout  
2. Dashboard stats (extend or replace `SystemStatsView`)  
3. Recent orders, revenue chart, top vendors  

**Phase 2 – Core admin management**
4. Customer user list, create, update, export, status, role  
5. Vendor list, detail, status, verification, stats, export  
6. Product list, pending, approve, reject  
7. Order list, detail, update status, cancel, export, bulk  

**Phase 3 – Financial and content**
8. Payouts, escrow, bank account approval  
9. Categories and subcategories admin CRUD  
10. Size chart approval  
11. Hero section, promotional banners (path + image upload)  
12. Contact and branches  

**Phase 4 – Loyalty and analytics**
13. Loyalty rewards, badges, earning rules, user adjustments  
14. Analytics endpoints  
15. Admin profile and image upload  
