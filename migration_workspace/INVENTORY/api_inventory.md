# API Inventory — Consolidated Summary

> This file provides a cross-frontend view of all discovered APIs.
> For detailed per-frontend breakdowns, see individual inventory files.
> Last Updated: 2026-06-18

---

## Supabase Tables Accessed Directly (Migration Targets)

These are the Supabase tables accessed directly from frontend code (via SDK) that need Django API equivalents.

| Table/View | Frontends Using It | Operations | Priority |
|---|---|---|---|
| `admin_sessions` | ecom_admin | SELECT, INSERT, UPDATE, DELETE | CRITICAL (auth) |
| `admin_users` | ecom_admin | SELECT | CRITICAL (auth) |
| `vendor_sessions` | vendor-dashboard | SELECT, INSERT, DELETE | CRITICAL (auth) |
| `vendors` | vendor-dashboard, ecom_admin | SELECT, UPDATE | HIGH |
| `products` | all three | SELECT, UPDATE, UPSERT, DELETE | HIGH |
| `categories` | ecom_admin, vendor-dashboard | SELECT, INSERT, UPDATE, DELETE | MEDIUM |
| `subcategories` | ecom_admin, vendor-dashboard | SELECT (joined) | MEDIUM |
| `orders` | ecom_admin | SELECT, UPDATE | HIGH |
| `order_items` | ecom_admin | SELECT | MEDIUM |
| `profiles` | ecom_admin, ecomWebsite | SELECT, UPDATE | HIGH |
| `reviews` | ecomWebsite (BFF) | SELECT, INSERT | MEDIUM |
| `product_questions` | ecomWebsite (BFF) | SELECT, INSERT | MEDIUM |
| `product_performance_summary` | vendor-dashboard | SELECT (view) | LOW |
| `loyalty_points` | ecom_admin | SELECT, UPDATE | MEDIUM |
| `loyalty_transactions` | ecom_admin | INSERT | MEDIUM |
| `loyalty_earning_rules` | ecom_admin | SELECT | LOW |
| `loyalty_badges` | ecom_admin | SELECT | LOW |
| `user_badges` | ecom_admin | SELECT, INSERT | LOW |
| `loyalty_vouchers` | ecom_admin | SELECT, UPDATE | MEDIUM |

---

## Supabase Auth Operations (Migration Targets)

| Operation | Frontends | Current Usage | Django Equivalent Needed |
|---|---|---|---|
| `signUp()` | ecomWebsite | User registration | `POST /api/auth/register/` |
| `signInWithPassword()` | all three | Login | `POST /api/auth/login/` (returns JWT) |
| `signOut()` | all three | Logout | `POST /api/auth/logout/` |
| `getSession()` | ecomWebsite | Token for API calls | Django JWT token (already exists) |
| `getUser()` | ecom_admin | Validate user exists | `GET /api/auth/me/` |
| `resetPasswordForEmail()` | ecomWebsite | Password reset | `POST /api/auth/password-reset/` |
| `admin.createUser()` | ecom_admin | Admin creates user | `POST /api/admin/users/` |
| `admin.updateUserById()` | ecom_admin | Admin updates user | `PATCH /api/admin/users/{id}/` |
| `admin.deleteUser()` | ecom_admin | Admin deletes user | `DELETE /api/admin/users/{id}/` |

---

## Supabase Storage Operations (Migration Targets)

| Bucket | Frontend | Operations | Django Equivalent |
|---|---|---|---|
| `product-images` | ecom_admin | upload, remove, getPublicUrl | `POST/DELETE /api/admin/products/{id}/images/` |
| `banners` | ecom_admin | upload, remove | `POST/DELETE /api/admin/content/banners/{id}/images/` |
| `product-media` | vendor-dashboard | upload (via R2 service) | Already migrated to R2 APIs |

---

## Django API Endpoints Used Across Frontends

These are the Django endpoints already called by frontends. They need verification (Phase 2).

### Shared Endpoints (used by 2+ frontends)

| Endpoint | Method | Used By | Notes |
|---|---|---|---|
| `/api/products/` | GET | Website, Admin, Vendor | Product listing |
| `/api/categories/` | GET | Website, Admin, Vendor | Category listing |
| `/api/currency/rates/` | GET | All | Exchange rates |
| `/api/auth/login/` | POST | All (via different auth flows) | Login |
| `/api/auth/logout/` | POST | All | Logout |
| `/api/vendors/profile/` | GET/PATCH | Vendor, Admin | Vendor profile |
| `/api/vendors/products/` | GET/POST | Vendor, Admin | Vendor product management |

### Website-Only Endpoints

| Category | Endpoint Count | Verified? |
|---|---|---|
| Cart & Wishlist | 9 | No |
| Checkout | 6 | No |
| Orders | 5 | No |
| Payments | 2 | No |
| Loyalty | 8 | No |
| Shipping Addresses | 4 | No |
| User Profile | 3 | No |
| Content | 2 | No |

### Admin-Only Endpoints

| Category | Endpoint Count | Verified? |
|---|---|---|
| Dashboard Stats | 1 | No |
| Product Approval | 2 | No |
| Vendor Management | 1 | No |

### Vendor-Only Endpoints

| Category | Endpoint Count | Verified? |
|---|---|---|
| Dashboard Stats | 1 | No |
| Orders | 4 | No |
| Analytics | 4 | No |
| Reviews/QA | 4 | No |
| Support | 4 | No |
| Currency | 4 | No |
| Earnings | 1 | No |

---

## Key Source Files Reference

### ecomWebsite
| File | Purpose |
|---|---|
| `lib/api.js` | Central API client (apiFetch, apiAuthFetch) |
| `utils/supabase/client.js` | Browser Supabase client |

### ecom_admin
| File | Purpose |
|---|---|
| `lib/supabase-admin.js` | Admin session validation, service role client |
| `lib/supabase-server.js` | Server-side Supabase client |
| `lib/storage-utils.js` | Supabase storage operations |
| `lib/loyalty-service.js` | Loyalty system Supabase operations |

### vendor-dashboard
| File | Purpose |
|---|---|
| `src/lib/besmart-api.js` | Django API client with token relay |
| `src/lib/besmart-product-api.js` | Product creation flow (Option B) |
| `src/lib/supabase.js` | Supabase client |
| `src/services/cookieAuthService.js` | Cookie-based auth service |
| `src/services/productsService.js` | Product service (mixed Supabase + BFF) |
| `src/services/vendorService.js` | Vendor service (mixed Supabase + BFF) |
| `src/services/ordersService.js` | Order service (BFF only) |
| `src/services/reviewsService.js` | Review service (BFF only) |
| `src/services/qaService.js` | Q&A service (BFF only) |
| `src/services/supportService.js` | Support service (BFF only) |
| `src/services/currencyService.js` | Currency service (BFF only) |
| `src/services/imageUploadService.js` | Image upload (via R2 service) |
