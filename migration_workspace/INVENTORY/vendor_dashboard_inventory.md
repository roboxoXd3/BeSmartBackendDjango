# API Inventory — vendor-dashboard (Vendor Frontend)

> **Repository:** `/home/unthinkable/Projects/vendor-dashboard`
> **Framework:** Next.js (App Router)
> **API Clients:**
>   - `src/lib/besmart-api.js` → Django API calls with Bearer token from vendor_sessions
>   - `src/lib/besmart-product-api.js` → Product creation (Option B: Supabase-first then Django sync)
>   - `src/services/*.js` → Service layer calling `/api/*` BFF routes
>   - `src/services/cookieAuthService.js` → Cookie-based session management
> **Auth Strategy:** Dual — Supabase auth for login, then vendor_sessions table for token storage, HTTP-only cookies for BFF routes
> **Supabase Client:** `src/lib/supabase.js` → `getSupabase()`

---

## Authentication Pattern

```javascript
// besmart-api.js — Token retrieval from vendor_sessions
const session = await supabase.from('vendor_sessions')
  .select('*').eq('vendor_id', vendorId).eq('is_active', true)
const token = session.supabase_access_token || session.session_token
headers['Authorization'] = `Bearer ${token}`
// Then calls api.xbesmart.com

// cookieAuthService.js — Cookie-based BFF auth
fetch('/api/auth/validate-session', { credentials: 'include' })
// Server validates vendor_session_token cookie against vendor_sessions table
```

---

## DJANGO_API Calls (34 total)

### Via besmart-api.js (Direct Django calls)

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| VND-D-001 | GET | `${DJANGO_API}/api/vendors/profile/` | besmart-api.js | Bearer | HIGH | Get vendor profile |
| VND-D-002 | PATCH | `${DJANGO_API}/api/vendors/profile/` | besmart-api.js | Bearer | HIGH | Update vendor profile |
| VND-D-003 | GET | `${DJANGO_API}/api/vendors/products/` | besmart-api.js | Bearer | HIGH | List vendor products |
| VND-D-004 | POST | `${DJANGO_API}/api/vendors/products/` | besmart-api.js | Bearer | HIGH | Create product |
| VND-D-005 | GET | `${DJANGO_API}/api/vendors/products/{id}/` | besmart-api.js | Bearer | HIGH | Get product detail |
| VND-D-006 | PATCH | `${DJANGO_API}/api/vendors/products/{id}/` | besmart-api.js | Bearer | HIGH | Update product |
| VND-D-007 | DELETE | `${DJANGO_API}/api/vendors/products/{id}/` | besmart-api.js | Bearer | HIGH | Delete product |
| VND-D-008 | POST | `${DJANGO_API}/api/vendors/products/{id}/upload-image/` | besmart-api.js | Bearer | HIGH | Upload product image |
| VND-D-009 | POST | `${DJANGO_API}/api/vendors/products/{id}/upload-video/` | besmart-api.js | Bearer | HIGH | Upload product video |
| VND-D-010 | GET | `${DJANGO_API}/api/vendors/orders/` | besmart-api.js | Bearer | HIGH | List vendor orders |
| VND-D-011 | GET | `${DJANGO_API}/api/vendors/orders/{id}/` | besmart-api.js | Bearer | HIGH | Order detail |
| VND-D-012 | PATCH | `${DJANGO_API}/api/vendors/orders/{id}/status/` | besmart-api.js | Bearer | HIGH | Update order status |
| VND-D-013 | GET | `${DJANGO_API}/api/vendors/dashboard-stats/` | besmart-api.js | Bearer | HIGH | Dashboard statistics |
| VND-D-014 | GET | `${DJANGO_API}/api/vendors/earnings/` | besmart-api.js | Bearer | HIGH | Earnings summary |
| VND-D-015 | GET | `${DJANGO_API}/api/vendors/analytics/` | besmart-api.js | Bearer | HIGH | Vendor analytics |

### Via BFF Routes (Service layer → Next.js API → may call Django)

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| VND-D-016 | GET | `/api/products?vendorId=` | productsService.js → BFF | Cookie | HIGH | List vendor products (paginated, filtered) |
| VND-D-017 | GET | `/api/products/{id}?vendorId=` | productsService.js → BFF | Cookie | HIGH | Single product detail |
| VND-D-018 | POST | `/api/products` | productsService.js → BFF | Cookie | HIGH | Create product. Body: {vendorId, productData} |
| VND-D-019 | PUT | `/api/products/{id}` | productsService.js → BFF | Cookie | HIGH | Update product. Body: {updates} |
| VND-D-020 | DELETE | `/api/products/{id}` | productsService.js → BFF | Cookie | HIGH | Delete product |
| VND-D-021 | GET | `/api/orders?vendorId=` | ordersService.js → BFF | Cookie | HIGH | List vendor orders (paginated, filtered) |
| VND-D-022 | PUT | `/api/orders` | ordersService.js → BFF | Cookie | HIGH | Update order status. Body: {orderId, status, vendorId, trackingNumber?, notes?} |
| VND-D-023 | GET | `/api/orders/stats?vendorId=&dateRange=` | ordersService.js → BFF | Cookie | HIGH | Order statistics |
| VND-D-024 | GET | `/api/orders/export?vendorId=&format=` | ordersService.js → BFF | Cookie | HIGH | Export orders (returns blob) |
| VND-D-025 | GET | `/api/dashboard-stats?vendorId=` | vendorService.js → BFF | Cookie | HIGH | Dashboard statistics |
| VND-D-026 | GET | `/api/recent-orders?vendorId=&limit=` | vendorService.js → BFF | Cookie | HIGH | Recent orders for dashboard |
| VND-D-027 | GET | `/api/analytics/sales?vendorId=&period=` | vendorService.js → BFF | Cookie | HIGH | Sales analytics |
| VND-D-028 | GET | `/api/analytics/metrics?vendorId=` | vendorService.js → BFF | Cookie | HIGH | Analytics metrics |
| VND-D-029 | GET | `/api/analytics/funnel?vendorId=` | vendorService.js → BFF | Cookie | HIGH | Conversion funnel |
| VND-D-030 | GET | `/api/analytics/performance?vendorId=` | vendorService.js → BFF | Cookie | HIGH | Product performance |
| VND-D-031 | GET | `/api/reviews?vendorId=` | reviewsService.js → BFF | No | HIGH | List vendor reviews (paginated) |
| VND-D-032 | PUT | `/api/reviews` | reviewsService.js → BFF | No | HIGH | Respond to / update review visibility |
| VND-D-033 | GET | `/api/product-qa?vendorId=` | qaService.js → BFF | No | HIGH | List vendor Q&A (paginated) |
| VND-D-034 | PUT | `/api/product-qa` | qaService.js → BFF | No | HIGH | Answer question / update visibility |

### Support Service

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| VND-D-035 | GET | `/api/vendor/support/tickets` | supportService.js → BFF | Cookie | HIGH | List support tickets |
| VND-D-036 | POST | `/api/vendor/support/tickets` | supportService.js → BFF | Cookie | HIGH | Create ticket |
| VND-D-037 | GET | `/api/vendor/support/tickets/{id}/messages` | supportService.js → BFF | Cookie | HIGH | Get ticket messages |
| VND-D-038 | POST | `/api/vendor/support/tickets/{id}/messages` | supportService.js → BFF | Cookie | HIGH | Send message |

### Currency Service

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| VND-D-039 | GET | `/api/currency` | currencyService.js → BFF | No | HIGH | Get currencies & exchange rates |
| VND-D-040 | GET | `/api/currency/convert?amount=&from=&to=` | currencyService.js → BFF | No | HIGH | Convert currency amount |
| VND-D-041 | POST | `/api/currency/convert` | currencyService.js → BFF | No | HIGH | Convert product prices (batch) |
| VND-D-042 | POST | `/api/currency` | currencyService.js → BFF | No | HIGH | Update currency rates (admin) |

---

## SUPABASE_SDK Calls (10 total)

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| VND-S-001 | `vendor_sessions` | SELECT | besmart-api.js | Get active session for token retrieval |
| VND-S-002 | `vendor_sessions` | INSERT | cookieAuthService.js | Create vendor session |
| VND-S-003 | `vendor_sessions` | DELETE | cookieAuthService.js | Cleanup old sessions |
| VND-S-004 | `vendors` | SELECT | vendorService.js | Get vendor profile (direct Supabase) |
| VND-S-005 | `vendors` | UPDATE | vendorService.js | Update vendor profile (direct Supabase) |
| VND-S-006 | `products` | SELECT (various) | vendorService.js | Best selling, inventory status queries |
| VND-S-007 | `products` | UPDATE | productsService.js | Update stock (direct Supabase) |
| VND-S-008 | `products` | UPSERT | productsService.js | Bulk update products (direct Supabase) |
| VND-S-009 | `categories` + `subcategories` | SELECT | productsService.js | Get categories with subcategories |
| VND-S-010 | `product_performance_summary` | SELECT | vendorService.js | View: best selling products |

---

## SUPABASE_AUTH Calls (2 total)

| ID | Operation | Source File | Notes |
|---|---|---|---|
| VND-A-001 | `supabase.auth.signInWithPassword()` | Login flow (via BFF route) | Vendor login |
| VND-A-002 | `supabase.auth.signOut()` | Logout flow (via BFF route) | Vendor logout |

---

## SUPABASE_STORAGE Calls (1 total)

| ID | Bucket | Operation | Source File | Notes |
|---|---|---|---|---|
| VND-ST-001 | `product-media` | Upload (via productMediaService) | imageUploadService.js → productMediaService.js | Uses BeSmart R2 APIs, not direct Supabase storage |

> Note: The vendor-dashboard's image upload is already using the Django/R2 API pattern via `productMediaService`, not direct Supabase storage.

---

## NEXT_BFF Routes (12 total)

| Route | Methods | Calls Django? | Calls Supabase? | Notes |
|---|---|---|---|---|
| `/api/auth/validate-session` | GET | No | Yes (vendor_sessions) | Cookie session validation |
| `/api/auth/refresh-session` | POST | No | Yes (vendor_sessions) | Session token refresh |
| `/api/auth/logout` | POST | No | Yes (vendor_sessions + auth) | Session invalidation |
| `/api/products` | GET/POST | Maybe | Yes | Product CRUD |
| `/api/products/[id]` | GET/PUT/DELETE | Maybe | Yes | Product operations |
| `/api/orders` | GET/PUT | Yes (likely) | Maybe | Order management |
| `/api/orders/stats` | GET | Yes (likely) | Maybe | Order statistics |
| `/api/dashboard-stats` | GET | Yes (likely) | Maybe | Dashboard stats |
| `/api/recent-orders` | GET | Yes (likely) | Maybe | Recent orders |
| `/api/analytics/*` | GET | Yes (likely) | Maybe | Various analytics endpoints |
| `/api/reviews` | GET/PUT | Maybe | Yes | Review management |
| `/api/product-qa` | GET/PUT | Maybe | Yes | Q&A management |

---

## UNKNOWN (1 total)

| ID | Pattern | Source File | Notes |
|---|---|---|---|
| VND-U-001 | `productMediaService.js` full flow | Referenced by imageUploadService.js | Exact R2/Django API calls need tracing through productMediaService |
