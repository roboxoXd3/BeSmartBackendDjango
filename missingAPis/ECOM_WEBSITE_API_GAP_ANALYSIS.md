# E-commerce Website → Django Backend: API Gap Analysis

> **Purpose:** Identify APIs required by the ecomWebsite (Next.js) to migrate from Supabase to BeSmartBackendDjango.  
> **Overlap:** Same marketplace as mobile app – most APIs align with `API_SPECIFICATION_MOBILE_MIGRATION.md`.  
> **Related:** `VENDOR_DASHBOARD_API_GAP_ANALYSIS.md`, `ADMIN_PANEL_API_GAP_ANALYSIS.md`

**Date:** February 12, 2026  
**EcomWebsite:** `ecomWebsite` (Next.js + Supabase)  
**Backend:** `BeSmartBackendDjango`

---

## How the Website Uses Data

The ecomWebsite uses two patterns:
1. **Direct Supabase client** – `.from(table)` and `.rpc()` in components/hooks
2. **Local API routes** – `fetch('/api/...')` for payments, loyalty, currency, account deletion

All of these must be replaced with Django REST API calls.

---

## Shared APIs with Mobile App

The website and mobile app share most customer-facing flows. The Mobile API spec (`API_SPECIFICATION_MOBILE_MIGRATION.md`) already defines many of these.

| Area | Mobile Spec | Website | Use Same Endpoints |
|------|-------------|---------|--------------------|
| Shipping addresses | ✅ 5 endpoints | Same | `GET/POST/PATCH/DELETE /api/shipping-addresses/` |
| Orders | ✅ Create, cancel, track, reorder, invoice | Same | `/api/orders/` |
| Vendors | ✅ List, detail, products, reviews, follow | Same | `/api/vendors/` |
| Product reviews & Q&A | ✅ List, create, helpful | Same | `/api/products/{id}/reviews/`, `qa/` |
| Loyalty | ✅ Points, rewards, redeem, vouchers, badges | Same | `/api/loyalty/` |
| Categories | ✅ List, detail, subcategories | Same | `/api/categories/` |
| Cart & Wishlist | ✅ Full CRUD | Same | `/api/cart/`, `/api/wishlist/` |
| Account deletion | ✅ | Same | `POST /api/users/account/delete/` |
| Search analytics | ✅ | Same | `POST /api/search/analytics/` |

**Implementation note:** Build these once per the Mobile spec. The website can use the same base URL and JWT auth.

---

## EcomWebsite Data Usage Inventory

### 1. Direct Supabase Table Usage

| Table | Where Used | Purpose |
|-------|------------|---------|
| `products` | Product detail, search, featured, new arrivals, cart | List/detail with category, subcategory, vendor |
| `product_specifications` | Product detail page | Specs for a product |
| `product_offers` | Product detail page | Active offers |
| `product_highlights` | Product detail page | Highlight bullets |
| `categories` | Browse, search filters | List categories |
| `subcategories` | Product query | Nested under categories |
| `vendors` | Vendor list, vendor detail, search | Approved vendors + product count |
| `carts` | Cart, ProductCard | Create if missing |
| `cart_items` | Cart, checkout, ProductCard | Add, update, delete, list |
| `wishlist` | Wishlist, ProductCard | Add, remove, list |
| `orders` | My orders, order detail | List user orders, create after payment |
| `order_items` | Order detail | Order line items |
| `shipping_addresses` | Checkout, profile | List, create, update, delete |
| `profiles` | Profile, edit profile | User profile data |
| `avatars` | Profile image | Upload/fetch avatar |
| `contact_info` | Contact page, Footer | Main contact info |
| `contact_branches` | Contact page | Branch locations |
| `hero_section` | HeroSection | Homepage hero (single row) |
| `promotional_banners` | PromotionalBanner | Homepage banners |
| `faqs` | Help & Support | FAQ list (SupportInfo type=faq) |
| `loyalty_points` | Loyalty page | User points balance |
| `loyalty_transactions` | Loyalty history | Transaction list |
| `loyalty_rewards` | Loyalty rewards page | Rewards catalog |
| `loyalty_vouchers` | Checkout coupon, vouchers page | Apply voucher, list user vouchers |
| `loyalty_badges` | Badges page | Badges catalog |
| `user_badges` | Badge progress | User earned badges |
| `payments` | Payment history, tokenize | Payment records, saved cards |
| `search_analytics` | Search results | Log search (user_id, query, result_count) |

### 2. Local API Routes (fetch)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/currency` | GET | Get default currency + rates |
| `/api/currency/convert` | GET | Convert amount between currencies |
| `/api/squad/initiate-payment` | POST | Initiate Squad checkout (email, amount, currency) |
| `/api/squad/verify-payment` | GET | Verify Squad transaction, create order |
| `/api/squad/charge-token` | POST | Charge saved card (subscriptions) |
| `/api/squad/tokenize` | POST | Save card for reuse |
| `/api/squad/webhook` | POST | Squad webhook |
| `/api/loyalty/award-points` | POST | Award points after order |
| `/api/loyalty/check-badges` | POST | Check and award badges after order |
| `/api/loyalty/redeem-points` | POST | Redeem points for voucher |
| `/api/loyalty/validate-voucher` | POST | Validate voucher at checkout |
| `/api/loyalty/badge-progress` | GET | User badge progress |
| `/api/account/delete` | POST | Delete user account (password required) |

### 3. Supabase RPCs Used

| RPC | Where | Purpose |
|-----|-------|---------|
| `delete_user_account` | Account delete | Cascade delete user data |
| `is_active_vendor` | Account delete | Block delete if vendor |
| `redeem_loyalty_points` | Loyalty redeem | Redeem logic |
| `check_and_award_badges` | Post-order | Award badges |
| `get_user_order_stats` | Badge progress | Order counts for badge rules |
| `create_loyalty_account` | Loyalty page | Create loyalty_points row |

---

## Django vs Website: What Exists, What's Missing

### Products

| Website Need | Django | Status |
|--------------|--------|--------|
| List products (filters, search, sort) | `GET /api/products/` | ✅ Exists |
| Product detail | `GET /api/products/{id}/` | ✅ Exists |
| Featured | `GET /api/products/featured/` | ✅ Exists |
| New arrivals | `GET /api/products/new-arrivals/` | ✅ Exists |
| On sale | `GET /api/products/on-sale/` | ✅ Exists |
| Search | `GET /api/products/search/` | ✅ Exists |
| Product specifications | — | ❌ Missing |
| Product offers | — | ❌ Missing |
| Product highlights | — | ❌ Missing |

**Product specs/offers/highlights:** Website expects `product_specifications`, `product_offers`, `product_highlights`. Either extend product serializer with nested data or add:

- `GET /api/products/{id}/specifications/`
- `GET /api/products/{id}/offers/`
- `GET /api/products/{id}/highlights/`

---

### Categories & Subcategories

| Website Need | Django | Status |
|--------------|--------|--------|
| List categories | `GET /api/categories/` | ✅ Exists |
| Category detail | `GET /api/categories/{id}/` | ✅ Exists |
| Subcategories | — | ❌ Missing |

**Action:** Add subcategories per Mobile spec: `GET /api/categories/{id}/subcategories/` or embed in category response.

---

### Vendors (Customer-Facing)

| Website Need | Django | Status |
|--------------|--------|--------|
| List vendors | — | ❌ Missing |
| Vendor detail | — | ❌ Missing |
| Vendor products | — | ❌ Missing |

**Note:** Django vendors app is vendor-facing (profile, dashboard). Mobile spec defines customer-facing vendor APIs. Implement per Mobile spec.

---

### Cart & Wishlist

| Website Need | Django | Status |
|--------------|--------|--------|
| Get cart | `GET /api/cart/` | ✅ Exists |
| Add to cart | `POST /api/cart/items/` | ✅ Exists |
| Update/remove cart item | `PATCH/DELETE /api/cart/items/{id}/` | ✅ Exists |
| Wishlist list | `GET /api/wishlist/` | ✅ Exists |
| Add to wishlist | `POST /api/wishlist/` | ✅ Exists |
| Remove from wishlist | `DELETE /api/wishlist/{id}/` | ✅ Exists |

---

### Shipping Addresses

| Website Need | Django | Status |
|--------------|--------|--------|
| List addresses | — | ❌ Missing |
| Create address | — | ❌ Missing |
| Update address | — | ❌ Missing |
| Delete address | — | ❌ Missing |

**Action:** Per Mobile spec, implement `GET/POST/PATCH/DELETE /api/shipping-addresses/`.

---

### Orders

| Website Need | Django | Status |
|--------------|--------|--------|
| List user orders | `GET /api/orders/` | ✅ Exists |
| Order detail | `GET /api/orders/{id}/` | ✅ Exists |
| Create order | `POST /api/orders/` | ⚠️ Placeholder only |
| Cancel order | — | ❌ Missing |

**Flow difference:** Website uses two flows:
- **COD:** Create order directly from cart, then clear cart.
- **Online:** Initiate Squad payment → redirect → verify → create order + clear cart + award points.

Django `OrderListCreateView.create()` returns a placeholder. Implement full order creation logic (from cart, voucher, address validation) per Mobile spec.

---

### Payments (Squad)

| Website Need | Django | Status |
|--------------|--------|--------|
| Initiate payment | `POST /api/payments/initiate/` | ⚠️ Different contract |
| Verify payment | `GET /api/payments/verify/` | ✅ Exists (query: transaction_ref) |
| Tokenize card | — | ❌ Check PaymentMethodViewSet |
| Charge saved card | — | ❌ Missing |
| Webhook | `POST /api/payments/webhook/` | ✅ Exists |

**Initiate difference:** Website `/api/squad/initiate-payment` expects `{ email, amount, currency, payment_type }` and creates a checkout from cart total. Django `initiate` expects `{ order_id }`.

**Options:**
1. Add `POST /api/payments/initiate-from-cart/` that accepts cart-based payload and creates a pending order or session, then returns checkout_url.
2. Or change website flow: create order first (status=pending), then call existing initiate with order_id.

**Charge-token:** For subscriptions/saved cards. Add `POST /api/payments/charge-token/` per payment gateway spec.

---

### Loyalty

| Website Need | Django | Status |
|--------------|--------|--------|
| Points balance | `GET /api/loyalty/points/` | ✅ Exists |
| Transactions | `GET /api/loyalty/transactions/` | ✅ Exists |
| Rewards list | `GET /api/loyalty/rewards/` | ✅ Exists |
| Redeem | `POST /api/loyalty/redeem/` | ✅ Exists |
| Vouchers list | `GET /api/loyalty/vouchers/` | ✅ Exists |
| Badges list | `GET /api/loyalty/badges/` | ✅ Exists |
| Validate voucher | — | ❌ Missing |
| Award points (post-order) | — | ❌ Missing |
| Check/award badges | — | ❌ Missing |
| Badge progress | — | ❌ Missing |
| Create loyalty account | — | ⚠️ Auto-create on first access |

**Action:** Add per Mobile spec:
- `POST /api/loyalty/validate-voucher/` – validate at checkout
- Award points and check badges are typically internal (order service), not separate public endpoints. Ensure order creation triggers these.

**Badge progress:** Add `GET /api/loyalty/badge-progress/` returning user stats and progress toward badges.

---

### Content

| Website Need | Django | Status |
|--------------|--------|--------|
| Hero section | — | ❌ Missing |
| Promotional banners | `GET /api/content/banners/` | ✅ Exists |
| Contact info | — | ❌ Missing |
| Contact branches | `GET /api/support/branches/` | ✅ Exists |
| FAQs | `GET /api/content/faqs/` | ✅ Exists (SupportInfo) |

**Hero section:** Website uses `hero_section` (single row: headline, image_url, video_url, buttons, etc.). Django has schema/model in db_schema. Add `GET /api/content/hero-section/` returning the active hero config.

**Contact info:** Website uses `contact_info` (main company contact). Django has `ContactBranch`. Add `GET /api/content/contact-info/` if different from branches.

---

### Currency

| Website Need | Django | Status |
|--------------|--------|--------|
| Get currency/rates | `GET /api/currency/rates/` | ✅ Exists |
| Convert | `POST /api/currency/convert/` | ✅ Exists |

**Path:** Website calls `/api/currency` and `/api/currency/convert`. Django uses `/api/currency/rates/` and `/api/currency/convert/`. Align paths or add thin proxy.

---

### User Profile & Account

| Website Need | Django | Status |
|--------------|--------|--------|
| Profile | `GET/PATCH /api/users/profile/` or `me/` | ✅ Exists |
| Avatar upload | — | Check users app |
| Account delete | — | ❌ Missing |

**Account delete:** Add `POST /api/users/account/delete/` with password confirmation per Mobile spec. Implement cascade delete (or soft delete) and block if user is active vendor.

---

### Search Analytics

| Website Need | Django | Status |
|--------------|--------|--------|
| Log search | — | ❌ Missing |

**Action:** Add `POST /api/search/analytics/` to log query, filters, result_count, user_id (optional). Per Mobile spec.

---

## Payment Flow Comparison

### Website (Current)

1. User fills checkout (address, payment method).
2. **COD:** Create order in Supabase, clear cart, award points, check badges.
3. **Online:** Call `/api/squad/initiate-payment` with `{ email, amount, currency }` → redirect to Squad → callback to `/verify-payment` → verify → create order in Supabase, clear cart, award points, check badges.

### Django (Current)

1. Create order via `POST /api/orders/` (not fully implemented).
2. Call `POST /api/payments/initiate/` with `{ order_id }` → get checkout_url.
3. After payment, call verify with `transaction_ref`.

**Recommendation:** Implement order creation from cart (with address, voucher) so both flows work. For website, either:
- Create order with status=pending before initiate, or
- Add `initiate-from-cart` that creates pending order server-side and returns checkout_url.

---

## Summary: Missing or Incomplete for Website

| # | Item | Priority |
|---|------|----------|
| 1 | Shipping addresses CRUD | Critical |
| 2 | Order creation from cart (COD + online) | Critical |
| 3 | Order cancel | High |
| 4 | Product specifications, offers, highlights | High |
| 5 | Subcategories | High |
| 6 | Customer-facing vendor APIs (list, detail, products) | High |
| 7 | Hero section API | High |
| 8 | Validate voucher | High |
| 9 | Badge progress | Medium |
| 10 | Account delete | High |
| 11 | Search analytics | Medium |
| 12 | Payment: initiate-from-cart or align flow | Critical |
| 13 | Payment: charge-token (saved cards) | Medium |
| 14 | Contact info (if separate from branches) | Low |

---

## Overlap with Mobile Spec

The following are defined in `API_SPECIFICATION_MOBILE_MIGRATION.md`. Implement them once; website and mobile both use them:

- Shipping addresses (5 endpoints)
- Orders: create, cancel, track, reorder, invoice
- Vendors: list, detail, products, reviews, follow
- Product reviews & Q&A
- Loyalty: validate-voucher, redeem, etc.
- Categories + subcategories
- Cart & wishlist (Django already has)
- Account deletion
- Search analytics

---

## Implementation Checklist for Website Migration

- [ ] Auth: Website uses Supabase auth → migrate to JWT (Django `/api/auth/login/`, etc.)
- [ ] Shipping addresses: Implement full CRUD
- [ ] Orders: Full create-from-cart logic, cancel
- [ ] Payments: Align initiate flow; add charge-token if needed
- [ ] Product specs/offers/highlights: Extend product or add sub-resources
- [ ] Subcategories: Add to categories API
- [ ] Vendors: Add customer-facing endpoints
- [ ] Hero section: Add `GET /api/content/hero-section/`
- [ ] Loyalty: Validate voucher, badge progress, award-on-order
- [ ] Account delete: Add endpoint
- [ ] Search analytics: Add logging endpoint
- [ ] Currency: Align paths with website expectations
