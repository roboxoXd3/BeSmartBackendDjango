# API Inventory — ecom_admin (Admin Panel)

> **Repository:** `/home/unthinkable/Projects/ecom_admin`
> **Framework:** Next.js (App Router)
> **API Client:** Direct `fetch()` calls in Next.js API routes (BFF pattern)
> **Auth Strategy:** HTTP-only cookies (`admin_session_token`) validated against `admin_sessions` + `admin_users` tables in Supabase
> **Supabase Client:** `lib/supabase-admin.js` → `createSupabaseAdmin()` using service role key
> **Server Client:** `lib/supabase-server.js` → `getSupabaseClient()` for server-side calls

---

## Authentication Pattern

```javascript
// lib/supabase-admin.js (session validation)
async validateAdminSession(sessionToken) {
  // 1. Query admin_sessions table for token
  // 2. Check session not expired (24h TTL)
  // 3. Get admin_users record
  // 4. Return { valid, admin, session }
}
```
**NOTE:** The admin panel does NOT use Django JWT auth. It uses its own Supabase-based session system.

---

## DJANGO_API Calls (8 total)

These are calls from admin BFF routes to the Django API.

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| ADM-D-001 | GET | `${DJANGO_API}/api/admin/dashboard/stats/` | app/api/admin/dashboard/route.js | Bearer | MEDIUM | Dashboard stats (may use Supabase fallback) |
| ADM-D-002 | GET | `${DJANGO_API}/api/admin/orders/` | app/api/admin/orders/route.js | Bearer | MEDIUM | Admin order listing |
| ADM-D-003 | GET | `${DJANGO_API}/api/products/` | app/api/products/route.js | No | MEDIUM | Product listing (some routes try Django first, fallback to Supabase) |
| ADM-D-004 | PATCH | `${DJANGO_API}/api/admin/products/{id}/` | app/api/products/[id]/route.js | Bearer | MEDIUM | Product update |
| ADM-D-005 | POST | `${DJANGO_API}/api/admin/products/{id}/approve/` | app/api/products/approve/route.js | Bearer | HIGH | Approve product |
| ADM-D-006 | POST | `${DJANGO_API}/api/admin/products/{id}/reject/` | app/api/products/reject/route.js | Bearer | HIGH | Reject product |
| ADM-D-007 | GET | `${DJANGO_API}/api/admin/vendors/` | app/api/vendors/route.js | Bearer | MEDIUM | Vendor listing |
| ADM-D-008 | GET | `${DJANGO_API}/api/currency/rates/` | app/api/currency/route.js | No | HIGH | Currency exchange rates |

---

## SUPABASE_SDK Calls (18 total)

### User & Admin Management

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-S-001 | `admin_sessions` | SELECT | lib/supabase-admin.js | Session token validation |
| ADM-S-002 | `admin_users` | SELECT | lib/supabase-admin.js | Admin user lookup (by id, joined from session) |
| ADM-S-003 | `admin_sessions` | INSERT | lib/supabase-admin.js | Create new admin session |
| ADM-S-004 | `admin_sessions` | UPDATE | lib/supabase-admin.js | Refresh session expiry |
| ADM-S-005 | `admin_sessions` | DELETE | lib/supabase-admin.js | Invalidate session (logout) |
| ADM-S-006 | `profiles` | SELECT / UPDATE | app/api/users/route.js | User management (list, update) |
| ADM-S-007 | `profiles` | SELECT (count) | app/api/admin/dashboard/route.js | Total user count for dashboard |

### Product Management

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-S-008 | `products` | SELECT (with joins) | app/api/products/route.js | List products with vendor, category joins |
| ADM-S-009 | `products` | SELECT single | app/api/products/[id]/route.js | Single product detail |
| ADM-S-010 | `products` | UPDATE | app/api/products/[id]/route.js | Update product fields |
| ADM-S-011 | `products` | DELETE | app/api/products/[id]/route.js | Delete product |
| ADM-S-012 | `categories` | SELECT | app/api/categories/route.js | List categories with subcategories |
| ADM-S-013 | `categories` | INSERT/UPDATE/DELETE | app/api/categories/route.js | Category CRUD |

### Order Management

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-S-014 | `orders` | SELECT (with joins) | app/api/orders/route.js | Orders with order_items, profiles, vendors |
| ADM-S-015 | `orders` | UPDATE | app/api/orders/[id]/route.js | Update order status |
| ADM-S-016 | `order_items` | SELECT | app/api/orders/[id]/route.js | Order items for detail view |

### Vendor Management

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-S-017 | `vendors` | SELECT (with joins) | app/api/vendors/route.js | Vendor listing with profile joins |
| ADM-S-018 | `vendors` | UPDATE | app/api/vendors/[id]/route.js | Update vendor (approve, suspend, etc.) |

### Loyalty Management

> Note: Loyalty operations use `lib/loyalty-service.js` which makes Supabase calls.

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-S-019* | `loyalty_points` | SELECT/UPDATE | lib/loyalty-service.js | Points balance management |
| ADM-S-020* | `loyalty_transactions` | INSERT | lib/loyalty-service.js | Transaction records |
| ADM-S-021* | `loyalty_earning_rules` | SELECT | lib/loyalty-service.js | Get active earning rules |
| ADM-S-022* | `loyalty_badges` | SELECT | lib/loyalty-service.js | Badge criteria checking |
| ADM-S-023* | `user_badges` | SELECT/INSERT | lib/loyalty-service.js | Badge awarding |
| ADM-S-024* | `loyalty_vouchers` | SELECT/UPDATE | lib/loyalty-service.js | Voucher validation and usage |

> *IDs ADM-S-019 through ADM-S-024 are counted as part of the loyalty service bundle.

---

## SUPABASE_AUTH Calls (6 total)

| ID | Operation | Source File | Notes |
|---|---|---|---|
| ADM-A-001 | `supabase.auth.signInWithPassword()` | app/api/auth/login/route.js | Admin login |
| ADM-A-002 | `supabase.auth.signOut()` | app/api/auth/logout/route.js | Admin logout |
| ADM-A-003 | `supabase.auth.getUser()` | lib/supabase-admin.js | Validate user exists |
| ADM-A-004 | `supabase.auth.admin.createUser()` | app/api/users/create/route.js | Create new user (admin only) |
| ADM-A-005 | `supabase.auth.admin.updateUserById()` | app/api/users/[id]/route.js | Update user auth fields |
| ADM-A-006 | `supabase.auth.admin.deleteUser()` | app/api/users/[id]/route.js | Delete user from auth |

---

## SUPABASE_STORAGE Calls (3 total)

| ID | Bucket | Operation | Source File | Notes |
|---|---|---|---|---|
| ADM-ST-001 | `product-images` | upload / remove | app/api/products/[id]/images/route.js | Product image management |
| ADM-ST-002 | `banners` | upload / remove | app/api/content/banners/route.js | Banner image management |
| ADM-ST-003 | various | remove (via storage-utils.js) | lib/storage-utils.js | Generic file deletion utility |

---

## NEXT_BFF Routes (22 total)

These are the Next.js API routes that act as Backend-For-Frontend middleware.

| Route | Methods | Calls Django? | Calls Supabase? | Notes |
|---|---|---|---|---|
| `/api/auth/login` | POST | No | Yes (auth + sessions) | Admin-specific auth flow |
| `/api/auth/logout` | POST | No | Yes (auth + sessions) | Session invalidation |
| `/api/auth/validate-session` | GET | No | Yes (sessions) | Cookie validation |
| `/api/admin/dashboard` | GET | Maybe | Yes (Supabase primary) | Dashboard stats |
| `/api/products` | GET | Maybe | Yes (Supabase primary) | Product listing |
| `/api/products/[id]` | GET/PUT/DELETE | No | Yes | Product CRUD |
| `/api/products/approve` | POST | Yes | Maybe | Product approval |
| `/api/products/reject` | POST | Yes | Maybe | Product rejection |
| `/api/categories` | GET/POST/PUT/DELETE | No | Yes | Category CRUD |
| `/api/orders` | GET | Maybe | Yes | Order listing |
| `/api/orders/[id]` | GET/PATCH | No | Yes | Order detail & update |
| `/api/vendors` | GET | Maybe | Yes | Vendor listing |
| `/api/vendors/[id]` | GET/PATCH | No | Yes | Vendor detail & update |
| `/api/users` | GET/POST | No | Yes | User management |
| `/api/users/[id]` | GET/PATCH/DELETE | No | Yes (auth admin) | User CRUD |
| `/api/content/hero-section` | GET/PATCH | No | Yes | Hero section CRUD |
| `/api/content/banners` | GET/POST/PUT/DELETE | No | Yes | Banner CRUD |
| `/api/content/banners/[id]/images` | POST/DELETE | No | Yes (storage) | Banner images |
| `/api/currency` | GET/POST | Maybe | Yes | Currency rates |
| `/api/loyalty/*` | Various | No | Yes | Loyalty admin operations |
| `/api/support/tickets` | GET/POST | No | Yes | Support ticket management |
| `/api/support/tickets/[id]/messages` | GET/POST | No | Yes | Ticket messaging |

---

## UNKNOWN (1 total)

| ID | Pattern | Source File | Notes |
|---|---|---|---|
| ADM-U-001 | Content FAQ management routes | Suspected but not confirmed | May exist as additional BFF routes for FAQ CRUD |
