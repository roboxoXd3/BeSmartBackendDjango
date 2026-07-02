# API Inventory — ecomWebsite (Customer Frontend)

> **Repository:** `/home/unthinkable/Projects/ecomWebsite`
> **Framework:** Next.js (App Router)
> **API Client:** `lib/api.js` → `apiFetch` (public) / `apiAuthFetch` (authenticated)
> **Base URL:** `process.env.NEXT_PUBLIC_API_URL` (resolves to `api.xbesmart.com`)
> **Auth Strategy:** Supabase session → Bearer token via `apiAuthFetch`

---

## Authentication Pattern

```javascript
// lib/api.js
apiAuthFetch(endpoint, options) {
  const session = supabase.auth.getSession()
  headers['Authorization'] = `Bearer ${session.access_token}`
  return fetch(`${API_BASE}${endpoint}`, { ...options, headers })
}
```

---

## DJANGO_API Calls (52 total)

### Products & Discovery

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-001 | GET | `/api/products/` | lib/api.js → various pages | No | HIGH | Product listing with filters (page, limit, category, search, sort) |
| WEB-D-002 | GET | `/api/products/{id}/` | lib/api.js → product detail | No | HIGH | Single product details |
| WEB-D-003 | GET | `/api/products/featured/` | lib/api.js → homepage | No | HIGH | Featured products list |
| WEB-D-004 | GET | `/api/products/new-arrivals/` | lib/api.js → homepage | No | HIGH | New arrival products |
| WEB-D-005 | GET | `/api/products/on-sale/` | lib/api.js → sale page | No | HIGH | Products on sale |
| WEB-D-006 | GET | `/api/products/search/?q=` | lib/api.js → search | No | HIGH | Product search with query |
| WEB-D-007 | GET | `/api/products/{id}/reviews/` | lib/api.js → product detail | No | HIGH | Product reviews list |
| WEB-D-008 | POST | `/api/products/{id}/reviews/` | lib/api.js → review form | Yes | HIGH | Submit product review |
| WEB-D-009 | GET | `/api/products/{id}/qa/` | lib/api.js → product detail | No | HIGH | Product Q&A list |
| WEB-D-010 | POST | `/api/products/{id}/qa/` | lib/api.js → Q&A form | Yes | HIGH | Ask product question |
| WEB-D-011 | GET | `/api/products/recommendations/` | lib/api.js → product detail | No | MEDIUM | Recommended products |
| WEB-D-012 | GET | `/api/products/{id}/related/` | lib/api.js → product detail | No | MEDIUM | Related products |

### Cart & Wishlist

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-013 | GET | `/api/cart/` | lib/api.js → cart page | Yes | HIGH | Get user's cart |
| WEB-D-014 | POST | `/api/cart/items/` | lib/api.js → add to cart | Yes | HIGH | Add item to cart. Body: {product_id, quantity, variant_id?} |
| WEB-D-015 | PATCH | `/api/cart/items/{id}/` | lib/api.js → cart page | Yes | HIGH | Update cart item quantity |
| WEB-D-016 | DELETE | `/api/cart/items/{id}/` | lib/api.js → cart page | Yes | HIGH | Remove item from cart |
| WEB-D-017 | GET | `/api/cart/summary/` | lib/api.js → checkout | Yes | HIGH | Cart totals & summary |
| WEB-D-018 | POST | `/api/cart/clear/` | lib/api.js → cart page | Yes | MEDIUM | Clear entire cart |
| WEB-D-019 | GET | `/api/wishlist/` | lib/api.js → wishlist | Yes | HIGH | Get wishlist items |
| WEB-D-020 | POST | `/api/wishlist/` | lib/api.js → product pages | Yes | HIGH | Add to wishlist. Body: {product_id} |
| WEB-D-021 | DELETE | `/api/wishlist/{id}/` | lib/api.js → wishlist | Yes | HIGH | Remove from wishlist |

### Checkout & Orders

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-022 | POST | `/api/checkout/validate/` | lib/api.js → checkout | Yes | HIGH | Validate checkout data |
| WEB-D-023 | POST | `/api/checkout/calculate-shipping/` | lib/api.js → checkout | Yes | HIGH | Calculate shipping cost |
| WEB-D-024 | POST | `/api/checkout/apply-voucher/` | lib/api.js → checkout | Yes | HIGH | Apply loyalty voucher |
| WEB-D-025 | POST | `/api/checkout/remove-voucher/` | lib/api.js → checkout | Yes | MEDIUM | Remove applied voucher |
| WEB-D-026 | GET | `/api/checkout/summary/` | lib/api.js → checkout | Yes | HIGH | Full order summary |
| WEB-D-027 | POST | `/api/checkout/complete/` | lib/api.js → checkout | Yes | HIGH | Complete checkout (creates order) |
| WEB-D-028 | POST | `/api/orders/` | lib/api.js → checkout | Yes | HIGH | Create order |
| WEB-D-029 | GET | `/api/orders/` | lib/api.js → orders page | Yes | HIGH | List user orders |
| WEB-D-030 | GET | `/api/orders/{id}/` | lib/api.js → order detail | Yes | HIGH | Order details |
| WEB-D-031 | POST | `/api/orders/{id}/cancel/` | lib/api.js → order detail | Yes | HIGH | Cancel order |
| WEB-D-032 | GET | `/api/orders/{id}/track/` | lib/api.js → order tracking | Yes | HIGH | Track order status |

### Payments

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-033 | POST | `/api/payments/initiate/` | lib/api.js → payment | Yes | HIGH | Initiate Squad payment |
| WEB-D-034 | GET | `/api/payments/verify/{ref}/` | lib/api.js → payment verify | Yes | HIGH | Verify payment status |

### User Account

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-035 | GET | `/api/users/profile/` | lib/api.js → profile | Yes | HIGH | Get user profile |
| WEB-D-036 | PATCH | `/api/users/profile/` | lib/api.js → profile edit | Yes | HIGH | Update profile |
| WEB-D-037 | POST | `/api/users/profile/upload-avatar/` | lib/api.js → profile | Yes | HIGH | Upload avatar (multipart) |
| WEB-D-038 | GET | `/api/shipping-addresses/` | lib/api.js → addresses | Yes | HIGH | List shipping addresses |
| WEB-D-039 | POST | `/api/shipping-addresses/` | lib/api.js → add address | Yes | HIGH | Add shipping address |
| WEB-D-040 | PATCH | `/api/shipping-addresses/{id}/` | lib/api.js → edit address | Yes | HIGH | Update address |
| WEB-D-041 | DELETE | `/api/shipping-addresses/{id}/` | lib/api.js → addresses | Yes | MEDIUM | Delete address |

### Loyalty Program

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-042 | GET | `/api/loyalty/points/` | lib/api.js → loyalty page | Yes | HIGH | Get points balance |
| WEB-D-043 | GET | `/api/loyalty/transactions/` | lib/api.js → loyalty page | Yes | MEDIUM | Points transaction history |
| WEB-D-044 | GET | `/api/loyalty/rewards/` | lib/api.js → rewards | Yes | HIGH | Available rewards catalog |
| WEB-D-045 | POST | `/api/loyalty/redeem/` | lib/api.js → redeem | Yes | HIGH | Redeem points for voucher |
| WEB-D-046 | GET | `/api/loyalty/vouchers/` | lib/api.js → vouchers | Yes | HIGH | User's vouchers |
| WEB-D-047 | GET | `/api/loyalty/badges/` | lib/api.js → badges | Yes | MEDIUM | Available badges |
| WEB-D-048 | GET | `/api/loyalty/user-badges/` | lib/api.js → badges | Yes | MEDIUM | User's earned badges |
| WEB-D-049 | POST | `/api/loyalty/validate-voucher/` | lib/api.js → checkout | Yes | HIGH | Validate voucher code at checkout |

### Categories & Content

| ID | Method | Endpoint | Source File | Auth | Confidence | Notes |
|---|---|---|---|---|---|---|
| WEB-D-050 | GET | `/api/categories/` | lib/api.js → navigation | No | HIGH | All categories with subcategories |
| WEB-D-051 | GET | `/api/content/hero-section/` | lib/api.js → homepage | No | HIGH | Hero section data |
| WEB-D-052 | GET | `/api/content/banners/` | lib/api.js → homepage | No | HIGH | Promotional banners |

---

## SUPABASE_SDK Calls (6 total)

| ID | Table/View | Operation | Source File | Notes |
|---|---|---|---|---|
| WEB-S-001 | `products` | SELECT (with complex filters) | app/api/products/route.js (BFF) | Product listing with category joins |
| WEB-S-002 | `products` | SELECT single | app/api/products/[id]/route.js (BFF) | Product detail with vendor join |
| WEB-S-003 | `categories` | SELECT | app/api/categories/route.js (BFF) | Categories with subcategories |
| WEB-S-004 | `reviews` | SELECT/INSERT | app/api/reviews/route.js (BFF) | Product reviews CRUD |
| WEB-S-005 | `product_questions` | SELECT/INSERT | app/api/qa/route.js (BFF) | Product Q&A |
| WEB-S-006 | `profiles` | SELECT/UPDATE | app/api/profile/route.js (BFF) | User profile management |

---

## SUPABASE_AUTH Calls (4 total)

| ID | Operation | Source File | Notes |
|---|---|---|---|
| WEB-A-001 | `supabase.auth.signUp()` | app/auth/signup/ | User registration |
| WEB-A-002 | `supabase.auth.signInWithPassword()` | app/auth/login/ | User login |
| WEB-A-003 | `supabase.auth.signOut()` | app/auth/logout/ | User logout |
| WEB-A-004 | `supabase.auth.getSession()` | lib/api.js (apiAuthFetch) | Token retrieval for API calls |

---

## UNKNOWN (1 total)

| ID | Pattern | Source File | Notes |
|---|---|---|---|
| WEB-U-001 | `supabase.auth.resetPasswordForEmail()` | Suspected in auth flow | Password reset — needs manual verification of exact location |
