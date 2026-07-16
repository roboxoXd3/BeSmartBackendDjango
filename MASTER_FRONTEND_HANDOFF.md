# Django Backend API Endpoints - By Application

> **Total APIs:** 154+  
> **Applications:** 5 (Mobile App, Website, Admin Panel, Vendor Dashboard, Common)  
> **Date:** February 4, 2026

---

## 📋 Quick Navigation

- [Common APIs (All Apps)](#common-apis-all-apps) - 25 endpoints
- [Mobile Application APIs](#mobile-application-apis) - 45 endpoints
- [E-commerce Website APIs](#e-commerce-website-apis) - 38 endpoints
- [Vendor Dashboard APIs](#vendor-dashboard-apis) - 35 endpoints
- [Admin Panel APIs](#admin-panel-apis) - 65 endpoints

**Total Unique Endpoints:** 154+  
(Some endpoints are shared across applications)

---

## 🌐 Common APIs (All Apps)

These APIs are used across **all applications** (Mobile, Website, Vendor Dashboard, Admin Panel)

### 1. Authentication & User Management (12 endpoints)

> **⚠️ CRITICAL UPDATE: NATIVE DJANGO AUTH IS DEPRECATED**
> All native Django login/registration endpoints are now deprecated. The frontend must use **Supabase Authentication** for all login and registration flows.
> **Workflow:**
> 1. Authenticate user directly against Supabase via the Supabase JS client.
> 2. Pass the resulting `access_token` as an `Authorization: Bearer <token>` header to the Django backend.
> 3. Django automatically validates the token and syncs the user profile.

| Method | Endpoint | Description | Used By | Status |
|--------|----------|-------------|---------|--------|
| POST | `/api/users/register/` | User registration | All | **DEPRECATED** |
| POST | `/api/users/login/` | User login | All | **DEPRECATED** |
| POST | `/api/users/logout/` | User logout | All | **DEPRECATED** |
| POST | `/api/users/verify-email/` | Verify email address | All | **DEPRECATED** |
| GET | `/api/users/me/` | Get current user | All | Active |
| PATCH | `/api/users/profile/` | Update user profile | All | Active |
| POST | `/api/users/profile/upload-avatar/` | Upload profile picture | All | Active |

### 2. Categories (4 endpoints)

| Method | Endpoint | Description | Used By |
|--------|----------|-------------|---------|
| GET | `/api/categories/` | List all categories | All |
| GET | `/api/categories/{id}/` | Get category details | All |
| GET | `/api/categories/{id}/subcategories/` | Get subcategories | All |
| GET | `/api/categories/{id}/products/` | Products in category | All |

### 3. Currency (4 endpoints)

| Method | Endpoint | Description | Used By |
|--------|----------|-------------|---------|
| GET | `/api/currency/rates/` | Get all exchange rates | All |
| POST | `/api/currency/convert/` | Convert amount between currencies | All |
| GET | `/api/currency/supported/` | List supported currencies | All |
| GET | `/api/currency/user-preference/` | Get user's preferred currency | All |

### 4. Content (5 endpoints)

| Method | Endpoint | Description | Used By |
|--------|----------|-------------|---------|
| GET | `/api/content/hero-section/` | Get hero section data | Website, Mobile |
| GET | `/api/content/banners/` | Get promotional banners | Website, Mobile |
| GET | `/api/content/faqs/` | Get FAQs | Website, Mobile |
| GET | `/api/content/contact-info/` | Get contact information | All |
| GET | `/api/content/support-info/` | Get support options | All |

---

## 📱 Mobile Application APIs (45 endpoints)

APIs specifically for the **Flutter mobile app** (iOS & Android)

### 1. Product Discovery (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products (with filters) |
| GET | `/api/products/{id}/` | Product details |
| GET | `/api/products/featured/` | Featured products |
| GET | `/api/products/new-arrivals/` | New arrival products |
| GET | `/api/products/on-sale/` | Sale products |
| GET | `/api/products/search/` | Search products (AI-powered) |
| GET | `/api/products/{id}/reviews/` | Product reviews |
| POST | `/api/products/{id}/reviews/` | Submit review |
| GET | `/api/products/{id}/qa/` | Product Q&A |
| POST | `/api/products/{id}/qa/` | Ask question |

### 2. Shopping Cart (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cart/` | Get user's cart | Critical |
| POST | `/api/cart/items/` | Add item to cart | Critical |
| PATCH | `/api/cart/items/{id}/` | Update cart item quantity | Critical |
| DELETE | `/api/cart/items/{id}/` | Remove item from cart | Critical |
| POST | `/api/cart/clear/` | Clear entire cart | Medium |
| GET | `/api/cart/summary/` | Cart totals & summary | Critical |

### 3. Wishlist (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wishlist/` | Get wishlist items | High |
| POST | `/api/wishlist/` | Add to wishlist | High |
| DELETE | `/api/wishlist/{id}/` | Remove from wishlist | High |
| POST | `/api/wishlist/{id}/move-to-cart/` | Move to cart | Medium |
| DELETE | `/api/wishlist/clear/` | Clear wishlist | Low |

### 4. Orders (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders/` | Create order | Critical |
| GET | `/api/orders/` | List user orders | Critical |
| GET | `/api/orders/{id}/` | Order details | Critical |
| POST | `/api/orders/{id}/cancel/` | Cancel order | High |
| GET | `/api/orders/{id}/track/` | Track order status | High |
| POST | `/api/orders/{id}/reorder/` | Reorder same items | Medium |
| GET | `/api/orders/{id}/invoice/` | Download invoice | Medium |
| POST | `/api/orders/{id}/review-request/` | Request to review | Low |

### 5. Payments (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/initiate/` | Initiate Squad payment | Critical |
| GET | `/api/payments/verify/{ref}/` | Verify payment status | Critical |
| POST | `/api/payments/tokenize/` | Tokenize card for recurring | High |
| POST | `/api/payments/charge-token/` | Charge saved card | High |
| GET | `/api/payments/history/` | Payment history | Medium |
| GET | `/api/payments/methods/` | Saved payment methods | Medium |

### 6. Loyalty Program (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/loyalty/points/` | Get user points balance | High |
| GET | `/api/loyalty/transactions/` | Points transaction history | Medium |
| GET | `/api/loyalty/rewards/` | Available rewards catalog | High |
| POST | `/api/loyalty/redeem/` | Redeem points for voucher | High |
| GET | `/api/loyalty/vouchers/` | User's vouchers | High |
| GET | `/api/loyalty/badges/` | Available badges | Medium |
| GET | `/api/loyalty/user-badges/` | User's earned badges | Medium |
| GET | `/api/loyalty/badge-progress/` | Progress toward badges | Medium |
| GET | `/api/loyalty/tier-info/` | Current tier info | High |
| POST | `/api/loyalty/validate-voucher/` | Validate voucher code | Critical |

---

## 🌍 E-commerce Website APIs (38 endpoints)

APIs for the **Next.js e-commerce website**

### 1. Product Browsing (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products (with filters) | Critical |
| GET | `/api/products/{id}/` | Product details | Critical |
| GET | `/api/products/featured/` | Featured products | Critical |
| GET | `/api/products/new-arrivals/` | New arrivals | High |
| GET | `/api/products/on-sale/` | Sale products | High |
| GET | `/api/products/recommendations/` | Recommended products | Medium |
| GET | `/api/products/{id}/related/` | Related products | Medium |
| GET | `/api/products/{id}/vendor-products/` | More from vendor | Low |

### 2. Shopping Experience (11 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cart/` | Get cart | Critical |
| POST | `/api/cart/items/` | Add to cart | Critical |
| PATCH | `/api/cart/items/{id}/` | Update quantity | Critical |
| DELETE | `/api/cart/items/{id}/` | Remove from cart | Critical |
| GET | `/api/wishlist/` | Get wishlist | High |
| POST | `/api/wishlist/` | Add to wishlist | High |
| DELETE | `/api/wishlist/{id}/` | Remove from wishlist | High |
| GET | `/api/search/` | Search products | Critical |
| GET | `/api/search/suggestions/` | Search autocomplete | Medium |
| GET | `/api/search/history/` | User search history | Low |
| POST | `/api/search/analytics/` | Track search | Low |

### 3. Checkout & Orders (9 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders/` | Create order | Critical |
| GET | `/api/orders/` | List orders | Critical |
| GET | `/api/orders/{id}/` | Order details | Critical |
| POST | `/api/orders/{id}/cancel/` | Cancel order | High |
| GET | `/api/orders/{id}/track/` | Track order | High |
| GET | `/api/shipping-addresses/` | List addresses | Critical |
| POST | `/api/shipping-addresses/` | Add address | Critical |
| PATCH | `/api/shipping-addresses/{id}/` | Update address | High |
| DELETE | `/api/shipping-addresses/{id}/` | Delete address | Medium |

### 4. User Account (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile/` | Get profile | Critical |
| PATCH | `/api/users/profile/` | Update profile | Critical |
| DELETE | `/api/users/account/` | Delete account (GDPR) | High |
| POST | `/api/users/profile/upload-avatar/` | Upload avatar | Medium |
| GET | `/api/users/addresses/` | List addresses | High |
| GET | `/api/users/payment-methods/` | Saved cards | Medium |

### 5. Reviews & Ratings (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/products/{id}/reviews/` | Submit review | High |
| PATCH | `/api/reviews/{id}/` | Update review | Medium |
| DELETE | `/api/reviews/{id}/` | Delete review | Low |
| POST | `/api/reviews/{id}/helpful/` | Mark review helpful | Low |

---

## 🏪 Vendor Dashboard APIs (35 endpoints)

APIs for the **vendor dashboard** (Next.js)

### 1. Vendor Profile (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/profile/` | Get vendor profile | Critical |
| PATCH | `/api/vendors/profile/` | Update vendor profile | Critical |
| POST | `/api/vendors/profile/upload-logo/` | Upload business logo | High |
| GET | `/api/vendors/kyc-status/` | Get KYC status | Critical |
| POST | `/api/vendors/kyc/upload-document/` | Upload KYC document | Critical |
| GET | `/api/vendors/analytics/` | Vendor analytics | High |
| GET | `/api/vendors/dashboard-stats/` | Dashboard statistics | Critical |
| GET | `/api/vendors/performance/` | Performance metrics | Medium |

### 2. Product Management (11 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/products/` | List vendor products | Critical |
| POST | `/api/vendors/products/` | Create product | Critical |
| GET | `/api/vendors/products/{id}/` | Product details | Critical |
| PATCH | `/api/vendors/products/{id}/` | Update product | Critical |
| DELETE | `/api/vendors/products/{id}/` | Delete product | High |
| POST | `/api/vendors/products/{id}/upload-image/` | Upload product image | Critical |
| DELETE | `/api/vendors/products/{id}/images/{index}/` | Delete image | Medium |
| POST | `/api/vendors/products/{id}/upload-video/` | Upload video | Medium |
| POST | `/api/vendors/products/bulk-upload/` | Bulk product upload (CSV) | High |
| GET | `/api/vendors/products/pending-approval/` | Pending products | High |
| GET | `/api/vendors/products/statistics/` | Product stats | Medium |

### 3. Order Management (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/orders/` | List vendor orders | Critical |
| GET | `/api/vendors/orders/{id}/` | Order details | Critical |
| PATCH | `/api/vendors/orders/{id}/status/` | Update order status | Critical |
| POST | `/api/vendors/orders/{id}/confirm/` | Confirm order | Critical |
| POST | `/api/vendors/orders/{id}/ship/` | Mark as shipped | Critical |
| POST | `/api/vendors/orders/{id}/add-tracking/` | Add tracking number | High |
| GET | `/api/vendors/orders/statistics/` | Order statistics | Medium |

### 4. Earnings & Payouts (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/earnings/` | Earnings summary | Critical |
| GET | `/api/vendors/escrow/` | Escrow transactions | High |
| POST | `/api/vendors/payout-request/` | Request payout | Critical |
| GET | `/api/vendors/payouts/` | Payout history | High |
| GET | `/api/vendors/bank-accounts/` | List bank accounts | High |
| POST | `/api/vendors/bank-accounts/` | Add bank account | Critical |

### 5. Support & Communication (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/support/tickets/` | List tickets | High |
| POST | `/api/vendors/support/tickets/` | Create ticket | High |
| POST | `/api/vendors/support/tickets/{id}/messages/` | Send message | High |

---

## 👨‍💼 Admin Panel APIs (65 endpoints)

APIs for the **admin panel** (Next.js)

### 1. Dashboard & Analytics (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard/stats/` | Overall statistics | Critical |
| GET | `/api/admin/dashboard/revenue-chart/` | Revenue chart data | Critical |
| GET | `/api/admin/dashboard/recent-orders/` | Recent orders | High |
| GET | `/api/admin/dashboard/top-products/` | Best selling products | High |
| GET | `/api/admin/dashboard/top-vendors/` | Top vendors | Medium |
| GET | `/api/admin/dashboard/recent-activity/` | Recent activity log | Medium |
| GET | `/api/admin/analytics/revenue/` | Revenue analytics | High |
| POST | `/api/admin/analytics/export/` | Export analytics data | Medium |

### 2. User Management (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users/` | List all users | Critical |
| GET | `/api/admin/users/{id}/` | User details | Critical |
| PATCH | `/api/admin/users/{id}/` | Update user | High |
| DELETE | `/api/admin/users/{id}/` | Delete user | High |
| POST | `/api/admin/users/{id}/activate/` | Activate user | Medium |
| POST | `/api/admin/users/{id}/deactivate/` | Deactivate user | Medium |
| PATCH | `/api/admin/users/{id}/role/` | Change user role | High |
| GET | `/api/admin/users/export/` | Export users (CSV) | Low |

### 3. Vendor Management (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/vendors/` | List all vendors | Critical |
| GET | `/api/admin/vendors/{id}/` | Vendor details | Critical |
| PATCH | `/api/admin/vendors/{id}/` | Update vendor | High |
| POST | `/api/admin/vendors/{id}/approve/` | Approve vendor | Critical |
| POST | `/api/admin/vendors/{id}/reject/` | Reject vendor | High |
| POST | `/api/admin/vendors/{id}/suspend/` | Suspend vendor | High |
| POST | `/api/admin/vendors/{id}/activate/` | Activate vendor | High |
| GET | `/api/admin/vendors/{id}/kyc-documents/` | View KYC docs | Critical |
| POST | `/api/admin/vendors/{id}/verify-kyc/` | Verify KYC | Critical |
| GET | `/api/admin/vendors/{id}/products/` | Vendor's products | High |
| GET | `/api/admin/vendors/{id}/orders/` | Vendor's orders | High |
| GET | `/api/admin/vendors/statistics/` | Vendor statistics | Medium |

### 4. Product Management (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/products/` | List all products | Critical |
| GET | `/api/admin/products/pending/` | Pending approval | Critical |
| GET | `/api/admin/products/{id}/` | Product details | Critical |
| PATCH | `/api/admin/products/{id}/` | Update product | High |
| DELETE | `/api/admin/products/{id}/` | Delete product | High |
| POST | `/api/admin/products/{id}/approve/` | Approve product | Critical |
| POST | `/api/admin/products/{id}/reject/` | Reject product | High |
| POST | `/api/admin/products/{id}/feature/` | Mark as featured | Medium |
| POST | `/api/admin/products/bulk-update/` | Bulk update | Medium |
| GET | `/api/admin/products/statistics/` | Product stats | Medium |

### 5. Order Management (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/orders/` | List all orders | Critical |
| GET | `/api/admin/orders/{id}/` | Order details | Critical |
| PATCH | `/api/admin/orders/{id}/status/` | Update order status | Critical |
| POST | `/api/admin/orders/{id}/refund/` | Process refund | High |
| POST | `/api/admin/orders/{id}/cancel/` | Cancel order | High |
| GET | `/api/admin/orders/statistics/` | Order statistics | High |
| POST | `/api/admin/orders/{id}/send-notification/` | Notify customer | Medium |
| GET | `/api/admin/orders/export/` | Export orders (CSV) | Low |

### 6. Loyalty Program Management (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/loyalty/users/` | List loyalty members | High |
| GET | `/api/admin/loyalty/users/{id}/` | User loyalty details | High |
| POST | `/api/admin/loyalty/award-points/` | Manually award points | High |
| POST | `/api/admin/loyalty/deduct-points/` | Deduct points | Medium |
| GET | `/api/admin/loyalty/rewards/` | List rewards | Critical |
| POST | `/api/admin/loyalty/rewards/` | Create reward | Critical |
| PATCH | `/api/admin/loyalty/rewards/{id}/` | Update reward | High |
| DELETE | `/api/admin/loyalty/rewards/{id}/` | Delete reward | Medium |
| GET | `/api/admin/loyalty/badges/` | List badges | High |
| POST | `/api/admin/loyalty/badges/` | Create badge | High |
| PATCH | `/api/admin/loyalty/badges/{id}/` | Update badge | Medium |
| GET | `/api/admin/loyalty/analytics/` | Loyalty analytics | Medium |

### 7. Content Management (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/content/hero-section/` | Get hero section | Critical |
| PATCH | `/api/admin/content/hero-section/` | Update hero section | Critical |
| GET | `/api/admin/content/banners/` | List banners | High |
| POST | `/api/admin/content/banners/` | Create banner | High |
| PATCH | `/api/admin/content/banners/{id}/` | Update banner | High |
| DELETE | `/api/admin/content/banners/{id}/` | Delete banner | Medium |
| POST | `/api/admin/content/banners/{id}/upload-image/` | Upload banner image | High |

### 8. Support Management (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/support/tickets/` | List all tickets | Critical |
| GET | `/api/admin/support/tickets/{id}/` | Ticket details | Critical |
| PATCH | `/api/admin/support/tickets/{id}/` | Update ticket | High |
| POST | `/api/admin/support/tickets/{id}/assign/` | Assign to admin | High |
| POST | `/api/admin/support/tickets/{id}/resolve/` | Resolve ticket | High |
| POST | `/api/admin/support/tickets/{id}/messages/` | Send message | Critical |

### 9. Settings & Configuration (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/settings/platform/` | Platform settings | High |
| PATCH | `/api/admin/settings/platform/` | Update settings | High |
| GET | `/api/admin/settings/currency-rates/` | Currency rates | Medium |
| POST | `/api/admin/settings/update-rates/` | Update exchange rates | Medium |
| GET | `/api/admin/settings/app-settings/` | App configuration | Medium |
| PATCH | `/api/admin/settings/app-settings/` | Update app config | Medium |

---

## 🛍️ E-commerce Website-Specific APIs (Additional)

### 1. Checkout Process (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/checkout/validate/` | Validate checkout data | Critical |
| POST | `/api/checkout/calculate-shipping/` | Calculate shipping cost | Critical |
| POST | `/api/checkout/apply-voucher/` | Apply loyalty voucher | High |
| POST | `/api/checkout/remove-voucher/` | Remove voucher | Medium |
| GET | `/api/checkout/summary/` | Order summary | Critical |
| POST | `/api/checkout/complete/` | Complete checkout | Critical |

### 2. Vendor Discovery (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors/` | List vendors | High |
| GET | `/api/vendors/{id}/` | Vendor details | High |
| GET | `/api/vendors/{id}/products/` | Vendor products | High |
| GET | `/api/vendors/{id}/reviews/` | Vendor reviews | Medium |

---

## 🔄 WebSocket Endpoints (Real-time)

### 1. Chat & Support (3 WebSocket connections)

| Type | Endpoint | Description | Used By |
|------|----------|-------------|---------|
| WS | `/ws/chat/{conversation_id}/` | Chat conversation | Mobile, Website |
| WS | `/ws/support/tickets/{ticket_id}/` | Support ticket updates | Vendor, Admin |
| WS | `/ws/orders/{order_id}/` | Order status updates | Mobile, Website |

**Usage Example:**
```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://backend.com/ws/orders/order-123/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'status_update') {
    updateOrderStatus(data.new_status);
  }
};
```

---

## 📊 Complete API Summary by Application

### Mobile Application (45 endpoints)
```
Authentication:          12 (shared with all)
Product Discovery:       10
Shopping Cart:            6
Wishlist:                 5
Orders:                   8
Payments:                 6
Loyalty:                 10
Categories:               4 (shared)
Currency:                 4 (shared)
Content:                  5 (shared)
────────────────────────────
Subtotal:                45 endpoints
```

### E-commerce Website (38 endpoints)
```
Authentication:          12 (shared)
Product Browsing:         8
Shopping Experience:     11
Checkout & Orders:        9
User Account:             6
Reviews:                  4
Checkout Process:         6
Vendor Discovery:         4
Categories:               4 (shared)
Currency:                 4 (shared)
────────────────────────────
Subtotal:                38 endpoints
```

### Vendor Dashboard (35 endpoints)
```
Authentication:          12 (shared)
Vendor Profile:           8
Product Management:      11
Order Management:         7
Earnings & Payouts:       6
Support:                  3
Categories:               4 (shared)
Currency:                 4 (shared)
────────────────────────────
Subtotal:                35 endpoints
```

### Admin Panel (65 endpoints)
```
Authentication:          12 (shared)
Dashboard & Analytics:    8
User Management:          8
Vendor Management:       12
Product Management:      10
Order Management:         8
Loyalty Management:      12
Content Management:       7
Support Management:       6
Settings:                 6
Categories:               4 (shared)
Currency:                 4 (shared)
────────────────────────────
Subtotal:                65 endpoints
```

---

## 📦 API Organization Structure

### Recommended Django App Structure

```
besmart_backend/
├── users/
│   └── urls.py (12 endpoints)
│       ├── Authentication
│       ├── Profile management
│       └── Account operations
│
├── products/
│   └── urls.py (25 endpoints)
│       ├── Product CRUD
│       ├── Reviews & ratings
│       ├── Q&A
│       ├── Search
│       └── Recommendations
│
├── orders/
│   └── urls.py (18 endpoints)
│       ├── Order CRUD
│       ├── Cart management
│       ├── Wishlist
│       └── Checkout
│
├── payments/
│   └── urls.py (12 endpoints)
│       ├── Squad integration
│       ├── Webhooks
│       ├── Refunds
│       └── Payment methods
│
├── loyalty/
│   └── urls.py (15 endpoints)
│       ├── Points management
│       ├── Rewards catalog
│       ├── Vouchers
│       └── Badges
│
├── vendors/
│   └── urls.py (24 endpoints)
│       ├── Vendor profile
│       ├── Products
│       ├── Orders
│       ├── Payouts
│       └── Analytics
│
├── admin_api/
│   └── urls.py (60+ endpoints)
│       ├── Dashboard
│       ├── User management
│       ├── Vendor management
│       ├── Product approval
│       ├── Order management
│       ├── Loyalty config
│       ├── Content management
│       └── Settings
│
├── support/
│   └── urls.py (12 endpoints)
│       ├── Tickets
│       ├── Messages
│       └── Chat
│
├── categories/
│   └── urls.py (10 endpoints)
│       ├── Categories CRUD
│       └── Subcategories
│
├── currency/
│   └── urls.py (4 endpoints)
│       ├── Exchange rates
│       └── Conversion
│
└── content/
    └── urls.py (10 endpoints)
        ├── Hero section
        ├── Banners
        ├── FAQs
        └── Contact info
```

---

## 🔐 Permission Requirements by Endpoint

### Public Endpoints (No Authentication) - 15 endpoints
```
✓ GET /api/products/ (approved only)
✓ GET /api/products/{id}/ (approved only)
✓ GET /api/categories/
✓ GET /api/vendors/ (approved only)
✓ GET /api/content/hero-section/
✓ GET /api/content/banners/
✓ GET /api/content/faqs/
✓ GET /api/currency/rates/
✓ POST /api/currency/convert/
✓ GET /api/search/
... (6 more public endpoints)
```

### Customer Endpoints (Authenticated) - 55 endpoints
```
✓ Cart management (6 endpoints)
✓ Wishlist (5 endpoints)
✓ Orders (8 endpoints)
✓ Payments (6 endpoints)
✓ Loyalty (10 endpoints)
✓ Profile (6 endpoints)
✓ Reviews (4 endpoints)
... (10 more customer endpoints)
```

### Vendor Endpoints (Vendor Role) - 35 endpoints
```
✓ Product management (11 endpoints)
✓ Order management (7 endpoints)
✓ Vendor profile (8 endpoints)
✓ Earnings/payouts (6 endpoints)
✓ Support (3 endpoints)
```

### Admin Endpoints (Admin/Super Admin Role) - 65 endpoints
```
✓ All admin panel endpoints
✓ Vendor approval (12 endpoints)
✓ Product approval (10 endpoints)
✓ User management (8 endpoints)
✓ Loyalty config (12 endpoints)
✓ Content management (7 endpoints)
... (16 more admin endpoints)
```

---

## 📱 Mobile App Required APIs (Complete List)

### Must-Have for iOS/Android App (30 endpoints)

```
1. Authentication (6)
   POST /api/auth/register/
   POST /api/auth/login/
   POST /api/auth/logout/
   POST /api/auth/refresh/
   POST /api/auth/password-reset/
   GET  /api/auth/me/

2. Products (4)
   GET /api/products/
   GET /api/products/{id}/
   GET /api/products/search/
   GET /api/products/featured/

3. Cart (4)
   GET    /api/cart/
   POST   /api/cart/items/
   PATCH  /api/cart/items/{id}/
   DELETE /api/cart/items/{id}/

4. Orders (4)
   POST /api/orders/
   GET  /api/orders/
   GET  /api/orders/{id}/
   GET  /api/orders/{id}/track/

5. Payments (3)
   POST /api/payments/initiate/
   GET  /api/payments/verify/{ref}/
   GET  /api/payments/history/

6. Loyalty (5)
   GET  /api/loyalty/points/
   GET  /api/loyalty/rewards/
   POST /api/loyalty/redeem/
   GET  /api/loyalty/vouchers/
   GET  /api/loyalty/badges/

7. Profile (4)
   GET    /api/users/profile/
   PATCH  /api/users/profile/
   GET    /api/users/addresses/
   POST   /api/users/addresses/
```

### Nice-to-Have for Mobile (15 endpoints)
```
- Wishlist (5 endpoints)
- Reviews (4 endpoints)
- Q&A (2 endpoints)
- Notifications (2 endpoints)
- Search history (2 endpoints)
```

---

## 🌐 Website Required APIs (Complete List)

### Must-Have for E-commerce Website (25 endpoints)

```
1. Authentication (6) - Same as mobile
   
2. Product Browsing (5)
   GET /api/products/
   GET /api/products/{id}/
   GET /api/products/search/
   GET /api/products/featured/
   GET /api/categories/

3. Shopping Cart (5)
   GET    /api/cart/
   POST   /api/cart/items/
   PATCH  /api/cart/items/{id}/
   DELETE /api/cart/items/{id}/
   GET    /api/cart/summary/

4. Checkout (4)
   POST /api/checkout/validate/
   POST /api/checkout/calculate-shipping/
   POST /api/checkout/apply-voucher/
   POST /api/checkout/complete/

5. Orders (3)
   POST /api/orders/
   GET  /api/orders/
   GET  /api/orders/{id}/

6. Payments (2)
   POST /api/payments/initiate/
   GET  /api/payments/verify/{ref}/
```

---

## 📋 Quick Reference Cheat Sheet

### For Backend Developer: Suggested API Implementation Sequence

**Phase 1: Core APIs**
```
✓ Authentication (12 endpoints)
✓ Products (10 core endpoints)
✓ Cart & Wishlist (11 endpoints)
✓ Orders (8 core endpoints)
```

**Phase 2: Payments & Critical Features**
```
✓ Payments (6 endpoints)
✓ Checkout flow (6 endpoints)
✓ Test payment integration
```

**Phase 3: Loyalty & Vendors**
```
✓ Loyalty (10 endpoints)
✓ Vendor profile & products (8 endpoints)
```

**Phase 4: Admin APIs**
```
✓ Admin dashboard (8 endpoints)
✓ Admin management (52 endpoints)
```

---

## 🎯 Testing Checklist by Application

### Mobile App Testing
- [ ] User can register/login
- [ ] User can browse products
- [ ] User can add to cart
- [ ] User can place order
- [ ] User can make payment
- [ ] User can track order
- [ ] User can redeem loyalty points
- [ ] Push notifications work
- [ ] App works offline (cached data)

### Website Testing
- [ ] Public can browse products
- [ ] User can checkout
- [ ] Payments process correctly
- [ ] Order confirmation sent
- [ ] User dashboard functional
- [ ] Wishlist saves correctly
- [ ] Search works properly

### Vendor Dashboard Testing
- [ ] Vendor can login
- [ ] Vendor can add products
- [ ] Vendor can see orders
- [ ] Vendor can update order status
- [ ] Vendor can request payout
- [ ] Analytics display correctly
- [ ] Upload images works

### Admin Panel Testing
- [ ] Admin can login
- [ ] Dashboard loads stats
- [ ] Can approve vendors
- [ ] Can approve products
- [ ] Can manage orders
- [ ] Can configure loyalty
- [ ] Analytics export works

---

## 📊 API Response Time Targets

### Performance SLAs

```
Fast Response (P95 < 200ms):
  ✓ GET /api/products/
  ✓ GET /api/cart/
  ✓ POST /api/orders/
  ✓ POST /api/payments/initiate/
  ✓ GET /api/auth/me/

Standard Response (P95 < 500ms):
  ✓ GET /api/products/{id}/
  ✓ GET /api/orders/
  ✓ POST /api/loyalty/redeem/
  ✓ GET /api/vendors/dashboard-stats/

Moderate Response (P95 < 1s):
  ✓ GET /api/admin/analytics/
  ✓ POST /api/products/bulk-upload/
  ✓ GET /api/admin/users/export/

Heavy Operations (P95 < 2s):
  ✓ Complex analytics
  ✓ Large exports
  ✓ Heavy reports
```

---

## 🚀 Deployment Checklist by Application

### Mobile App Updates
- [ ] Update API base URL in Flutter app
- [ ] Update authentication flow (JWT instead of Supabase)
- [ ] Test all API calls
- [ ] Update error handling
- [ ] Test push notifications
- [ ] Release new app version

### Website Updates
- [ ] Update API endpoints in Next.js
- [ ] Update authentication (remove Supabase client)
- [ ] Test checkout flow
- [ ] Test payment integration
- [ ] Deploy to Vercel/Railway

### Vendor Dashboard Updates
- [ ] Update API calls
- [ ] Update authentication
- [ ] Test product upload
- [ ] Test payout requests
- [ ] Deploy to hosting

### Admin Panel Updates
- [ ] Update all admin API calls
- [ ] Update authentication
- [ ] Test approval workflows
- [ ] Test analytics
- [ ] Deploy to hosting

---

## 📞 Developer Quick Reference

### API Base URLs

```bash
# Development
LOCAL_BACKEND=http://localhost:8000
LOCAL_WS=ws://localhost:8000

# Staging
STAGING_BACKEND=https://staging-api.besmart.com
STAGING_WS=wss://staging-api.besmart.com

# Production
PROD_BACKEND=https://api.besmart.com
PROD_WS=wss://api.besmart.com
```

### Common Headers

```javascript
// All authenticated requests
headers: {
  'Authorization': 'Bearer ' + accessToken,
  'Content-Type': 'application/json',
  'X-Client-Version': '1.0.0',
  'X-Platform': 'ios|android|web'
}
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "price": ["Price must be greater than 0"],
      "images": ["At least one image is required"]
    }
  }
}
```

---

## 🎯 Summary for Backend Developer

### Your Task: Build 154+ API Endpoints

**Organized as:**
- ✅ 12 Authentication endpoints (shared by all)
- ✅ 25 Product endpoints
- ✅ 18 Order endpoints
- ✅ 12 Payment endpoints
- ✅ 15 Loyalty endpoints
- ✅ 24 Vendor endpoints
- ✅ 65 Admin endpoints
- ✅ 10 Category endpoints
- ✅ 12 Support endpoints
- ✅ 10 Content endpoints
- ✅ 4 Currency endpoints

**Used by:**
- 📱 Mobile App: 45 endpoints
- 🌐 Website: 38 endpoints
- 🏪 Vendor Dashboard: 35 endpoints
- 👨‍💼 Admin Panel: 65 endpoints
- 🔄 WebSocket: 3 connections

**Implementation Approach:**
- Start with Common APIs (authentication, categories, currency)
- Then Mobile App critical features
- Then Website e-commerce features
- Then Vendor Dashboard features
- Then Admin Panel features
- Finally Support & Miscellaneous features

---

**Document Version:** 1.0  
**Created:** February 4, 2026  
**Status:** Ready for Implementation  
**Next:** Start with Common APIs, then Mobile, then Website, then Vendor, then Admin


================================================================================

# RECENT FEATURE UPDATES

The following sections detail specific changes, new features, and breaking changes introduced in the recent sprints.

## --- VENDOR & PRODUCT UPDATES (JULY 6) ---

# Backend API Changes — Frontend Handoff Document

**Date:** 2026-07-06  
**For:** Frontend developers (vendor-dashboard, ecomWebsite, admin panel)  
**Context:** This document lists every backend API change made in this sprint. It covers changed response shapes, new capabilities, fields that became read-only, and new endpoints. Use this as a migration checklist.

---

## ⚠️ Breaking Changes

These require immediate frontend updates — old request/response formats will no longer work as expected.

---

### 1. KYC Documents — Response shape changed from array `[]` to dict `{}`

**Affected endpoints:**
- `GET /api/vendors/kyc-status/`
- `POST /api/vendors/kyc/upload/`

**Before (old shape):**
```json
{
  "verification_status": "pending",
  "verification_documents": [
    {"name": "id.jpg", "url": "...", "type": "id_proof", "uploaded_at": "..."},
    {"name": "license.pdf", "url": "...", "type": "business_license", "uploaded_at": "..."}
  ]
}
```

**After (new shape):**
```json
{
  "verification_status": "pending",
  "verification_documents": {
    "id_proof": {"name": "id.jpg", "url": "...", "uploaded_at": "..."},
    "business_license": {"name": "license.pdf", "url": "...", "uploaded_at": "..."}
  }
}
```

**Upload request change:** `document_type` is now **required** in the upload request. The backend will return `400` if it's missing.

```
POST /api/vendors/kyc/upload/
Content-Type: multipart/form-data

document: <file>
document_type: "id_proof"   ← REQUIRED (was optional before)
```

Valid values: `id_proof`, `business_license`, `address_proof` (or any string — stored as the key).

**Frontend action needed:**
- Update any code that reads `verification_documents` as an array. It is now an object keyed by document type.
- The workaround of uploading then immediately re-PATCHing the shape is no longer needed — the backend now stores it in the correct shape natively.
- Always send `document_type` in upload requests.

> **Note:** Legacy array data in the database is automatically migrated to dict format on read. No data migration needed.

---

### 2. `approval_status` is now read-only on products

**Affected endpoints:**
- `POST /api/vendors/own-products/` (create product)
- `PUT/PATCH /api/vendors/own-products/{id}/` (update product)

**What changed:** The `approval_status` and `vendor_id` fields are now **read-only** in the `ProductDetailSerializer`. If you send them in a request body, they will be silently ignored (not an error — just ignored).

- All newly created products are automatically set to `approval_status: "pending"` regardless of what the client sends.
- A vendor cannot change `vendor_id` on their own products.

**Frontend action needed:**
- If the frontend was sending `approval_status: "pending"` explicitly, it still works (it's just ignored) — no breakage.
- Remove any client-side `approval_status` setting if present (it's unnecessary now).

---

## 🔧 Changed Behavior (Non-Breaking)

These are improvements to existing endpoints. No frontend changes required unless you want to use the new capabilities.

---

### 3. Analytics Metrics — `conversion_rate` is now real data

**Endpoint:** `GET /api/vendors/analytics/metrics/`

**Before:**
```json
{
  "average_rating": 4.5,
  "total_reviews": 12,
  "conversion_rate": 0.05,   ← was hardcoded
  "return_rate": 0.02
}
```

**After:**
```json
{
  "average_rating": 4.5,
  "total_reviews": 12,
  "conversion_rate": 0.0312,  ← now computed from real view→purchase events
  "return_rate": 0.02
}
```

The `conversion_rate` is now dynamically computed as `purchases / views` from `ProductAnalyticsEvent` data. It returns `0.0` when there are no view events.

**Frontend action needed:** None — same field name, same type. The value is just accurate now. If you were displaying this with a "data is approximate" disclaimer, you can remove it.

---

### 4. Customer Locations — no longer returns fake data

**Endpoint:** `GET /api/vendors/stats/customer-locations/`

**Before:** Returned hardcoded `[{"region": "Lagos", "customers": 45}, {"region": "Abuja", "customers": 12}]` when there were no orders.

**After:** Returns an empty array `[]` when there are no orders with shipping addresses. Returns real state-level aggregations when data exists.

**Frontend action needed:** Handle the empty-array case gracefully (show an "N/A" or "No data yet" message instead of fake data).

---

### 5. Bulk Upload — now supports CSV files

**Endpoint:** `POST /api/vendors/own-products/bulk-upload/`

**Before:** Only accepted `application/json` with a `{"products": [...]}` body.

**After:** Accepts **two formats**:

**Option A — JSON (unchanged):**
```
POST /api/vendors/own-products/bulk-upload/
Content-Type: application/json

{"products": [{"name": "...", "price": 100, ...}, ...]}
```

**Option B — CSV file (new):**
```
POST /api/vendors/own-products/bulk-upload/
Content-Type: multipart/form-data

file: <products.csv>
```

**CSV column names** map directly to Product model fields:
`name`, `description`, `price`, `sku`, `category_id`, `subcategory_id`, `stock_quantity`, `brand`, `sizes`, `colors`, `status`, `discount_percentage`, `sale_price`, `mrp`, `in_stock`, `is_on_sale`, `is_featured`, `is_new_arrival`, `cod_allowed`

**Response change** — new `errors` field:
```json
{
  "message": "Bulk upsert completed",
  "updated_count": 5,
  "created_count": 10,
  "errors": [
    {"row": 3, "errors": {"name": ["This field is required."]}},
    {"row": 7, "id": "uuid-here", "error": "Product not found or not owned by this vendor"}
  ]
}
```

The `errors` array is always present (empty if no errors). Each entry includes the row number and the validation error(s) for that row.

**Frontend action needed:**
- If you want to support CSV upload, build a file input that sends `multipart/form-data` with a `file` field.
- Update the bulk-upload results UI to display per-row errors from the `errors` array.
- All bulk-created products now automatically get `approval_status: "pending"`.

---

## 📋 Summary of All Changed Files

| File | What Changed |
|:---|:---|
| [products/serializers.py](file:///home/unthinkable/Projects/BeSmartBackend/products/serializers.py#L33-L37) | Added `read_only_fields = ['approval_status', 'vendor_id']` to `ProductDetailSerializer` |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L303-L316) | `VendorKYCStatusView` — returns dict instead of list |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L338-L397) | `VendorKYCUploadView` — stores docs as dict keyed by type, `document_type` now required |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L534-L559) | `VendorAnalyticsMetricsView` — real `conversion_rate` computed from analytics events |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L568-L592) | `VendorCustomerLocationsView` — fixed broken query, removed fake fallback data |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L736-L739) | `VendorOwnProductViewSet.perform_create` — forces `approval_status='pending'` |
| [vendors/views.py](file:///home/unthinkable/Projects/BeSmartBackend/vendors/views.py#L810-L903) | `VendorOwnProductViewSet.bulk_upload` — CSV support, per-row error reporting |

---

## 🔮 Upcoming — Admin Panel Changes (Not Yet Implemented)

The following items from the admin panel audit doc have been identified but **not yet built**. Listed here so the frontend team is aware they're coming:

1. **Fix vendor `logo_url` → `business_logo`** — admin serializer references wrong field name
2. **Expand `ProductListSerializer`** for admin — needs `vendor_id`, `vendor_name`, `mrp`, `currency`, `created_at`
3. **Expand admin user serializer** — needs profile fields (`full_name`, `phone_number`, `role`)
4. **Per-user order history** — filter `OrderAdminViewSet` by customer
5. **Admin-wide escrow endpoint** — currently only vendor-scoped
6. **Loyalty program admin CRUD** — rewards, badges, earning rules, loyalty user list
7. **Payout approval → actual Squad transfer** — currently only flips status
8. **Site content write endpoints** — hero section, contact info, banners
9. **Admin bank accounts + support tickets** — currently vendor-scoped only
10. **Category image upload** — no endpoint exists
11. **Richer admin analytics** — date ranges, per-vendor breakdowns


## --- ANALYTICS & PAYMENT TOKENIZATION ---

# Frontend Integration Guide: Vendor Analytics & Payment Tokenization

This guide provides instructions for the frontend team (or their AI agents) to integrate the newly added backend capabilities for **Vendor Analytics** and **Squad Payment Tokenization**.

---

## 1. Vendor Analytics Tracking & Dashboard

We have added robust, backend-driven analytics to track product impressions and conversions.

### 1.1 Tracking Product Events (New Endpoint)
You need to call this endpoint whenever a user interacts with a product on the platform.

**Endpoint:** `POST /api/vendors/analytics/track/`
**Auth:** None required (`AllowAny`)

**Payload:**
```json
{
  "product_id": "uuid-of-the-product",
  "event_type": "view" // Can be "view", "cart", or "purchase"
}
```
**Integration Instructions:**
- **Views:** Fire this event when a user navigates to the Product Detail Page. You may want to debounce this to prevent spamming.
- **Cart:** Fire this event when a user adds the product to their cart.
- **Purchase:** Fire this event when a checkout completes successfully.

### 1.2 Fetching Vendor Funnel Metrics
This endpoint aggregates overall vendor analytics across all their products.

**Endpoint:** `GET /api/vendors/analytics/funnel/`
**Auth:** Required (Vendor specific)

**Response Format:**
```json
{
  "views": 1500,
  "cart": 300,
  "checkout": 150,
  "purchases": 50
}
```
**Integration Instructions:**
- Use this on the Vendor Dashboard to show conversion funnels or top-level metrics.

### 1.3 Fetching Per-Product Performance
This returns analytics and conversion rates broken down by each of the vendor's products, sorted by most views.

**Endpoint:** `GET /api/vendors/analytics/performance/`
**Auth:** Required (Vendor specific)

**Response Format:**
```json
{
  "data": [
    {
      "product_id": "uuid...",
      "name": "Product Name",
      "views": 100,
      "cart": 20,
      "purchases": 5,
      "conversion_rate": 5.0,
      "price": 25000.0
    }
  ]
}
```
**Integration Instructions:**
- Use this to populate a "Top Performing Products" table on the Vendor Dashboard.

---

## 2. Squad Payment Tokenization

We have updated the payment flow to fully support card tokenization, enabling one-click or recurring checkout flows for future purchases.

### 2.1 Initial Payment (Token Generation)
When you call the existing `POST /api/payments/initiate/` endpoint, the backend now automatically passes `is_recurring: true` to the Squad API.

**Integration Instructions:**
- The frontend **does not** need to change anything regarding the `initiate` endpoint.
- Once the user completes the payment on the Squad checkout page, Squad sends a webhook to our backend.
- **Backend Behavior:** The backend webhook listener validates the signature, fulfills the order, and automatically extracts `payment_information.token_id`. The token is saved to the user's account (`PaymentMethod` model).

### 2.2 Retrieving Saved Cards
Use the existing endpoint to list saved payment methods for the authenticated user.

**Endpoint:** `GET /api/payments/methods/`
**Auth:** Required

**Response Details:**
- The list will now contain payment methods where `provider` is `squad` and `payment_type` is `card`.

### 2.3 Charging a Saved Card (New Endpoint)
When a user selects a saved card during checkout instead of entering a new one, use this endpoint.

**Endpoint:** `POST /api/payments/charge-token/`
**Auth:** Required

**Payload:**
```json
{
  "order_id": "uuid-of-the-order",
  "payment_method_id": "uuid-of-the-saved-payment-method"
}
```
**Response Format:**
- **Success (200):**
```json
{
  "status": "success",
  "message": "Charge successful"
}
```
- **Error (400 or 502):**
```json
{
  "error": "Charge failed",
  "details": { ... }
}
```
**Integration Instructions:**
- On the checkout page, present the user's saved cards.
- If they select one, submit the order to `charge-token` instead of `initiate`.
- Handle potential errors (e.g., token expired, insufficient funds) by prompting the user to use a different card or initiate a new standard payment.


## --- ADMIN PANEL & DASHBOARD UPDATES (JULY 7) ---

# Frontend Handoff: Admin Panel API Additions

This document outlines the new and updated REST API endpoints available for the frontend team to build out the Admin Panel. All endpoints below require an `IsAdminUser` authentication token.

---

## 0. Authentication Updates (CRITICAL)

**Native Django Auth Deprecated**
- **Changes**: The native Django login/registration endpoints (`/api/users/login/`, `/api/users/register/`, etc.) have been marked as deprecated. 
- **Action Required**: The frontend must use **Supabase Authentication** for all login and registration flows (Customer, Vendor, and Admin). 
- **Workflow**:
  1. Authenticate the user directly against Supabase via the Supabase JS client.
  2. Take the `access_token` returned by Supabase and pass it as the `Authorization: Bearer <token>` header to the Django backend.
  3. The Django backend will automatically validate the token and sync the user profile internally.

---
## 1. Dashboard & Analytics Updates

**`GET /api/admin/dashboard/revenue-chart/`**
- **Changes**: Added robust query parameters to filter data, and added a category-level breakdown of revenue.
- **New Query Params**:
  - `period`: '7d', '30d', '90d', '1y'
  - `start_date`: Custom start date (e.g., `2026-07-01`)
  - `end_date`: Custom end date (e.g., `2026-07-31`)
  - `vendor_id`: Filter analytics to a specific vendor
- **New Response Fields**:
  - `category_breakdown`: List of `{"category": "Shoes", "revenue": 150.0}`
  - `start_date` / `end_date`: Evaluated date ranges
  - `total_revenue` / `total_orders`: Summary metrics for the filtered period

---

## 2. Order Management Updates

**`GET /api/admin/orders/`**
- **Changes**: You can now filter orders by a specific user.
- **New Query Params**: `user_id` (UUID)

**`GET /api/admin/orders/user-summary/?user_id={uuid}`**
- **Description**: Fetch high-level summary metrics about the user who placed orders (useful for showing customer lifetime value).
- **Response**: `{"orders_count": 5, "total_spent": 1250.50}`

---

## 3. Financials: Escrow, Payouts & Bank Accounts

**`GET /api/admin/escrow/`**
- **Description**: View all vendor escrow transactions across the platform.
- **Support**: Pagination, Search, Ordering

**`GET /api/admin/vendor-bank-accounts/`**
- **Description**: View all vendor bank accounts.
- **Support**: Pagination, Search, Ordering

**`POST /api/admin/payouts/{id}/process-transfer/`**
- **Description**: Explicitly trigger a real Squad payout transfer to the vendor's bank account.
- **Body**: `{"admin_notes": "Optional transfer description"}`
- **Response**: `{"status": "processing", "message": "Transfer initiated successfully"}`

---

## 4. Support & Tickets

**`GET /api/admin/support-tickets/`**
- **Description**: List all support tickets from vendors/users. Includes standard read/update methods.

**`POST /api/admin/support-tickets/{id}/reply/`**
- **Description**: Allow the admin to reply to a support ticket.
- **Body**: `{"message": "Your reply here"}`
- **Response**: Serialized `SupportMessage`

---

## 5. Site Content Management (CMS)

New viewsets have been added to allow admins to manage the static content on the site:

**`GET / PUT / PATCH /api/admin/hero-sections/`**
- Manage the Hero section text/content.

**`GET / PUT / PATCH /api/admin/contact-info/`**
- Manage global contact information.

**`GET / PUT / PATCH /api/admin/support-info/`**
- Manage support/FAQ information.

**`GET / POST / PATCH / DELETE /api/admin/promotional-banners/`**
- CRUD for promotional banners.
- **Image Upload Flow**: First `POST /api/admin/promotional-banners/` to create the banner record, then use `POST /api/admin/content/banners/{id}/images/` with multipart form data (`image`) to upload the banner image.

---

## 6. Category Image Management

**`POST /api/admin/categories/{id}/images/`**
**`DELETE /api/admin/categories/{id}/images/`**
- **Description**: Upload or delete images for categories (mirrors the product image upload flow).
- **Body for POST**: Multipart form data with the key `image`.
- **Body for DELETE**: JSON `{"image_url": "url_to_delete"}`.

---

## 7. Loyalty Points Management

**`POST /api/admin/loyalty/{user_id}/points/`**
- **Description**: Manually deduct or add loyalty points to a specific user's balance.
- **Body**: 
  ```json
  {
    "points": 50, // Positive to add, negative to deduct
    "description": "Customer service appeasement"
  }
  ```

---

## Serializer Enhancements

1. **`UserManagementSerializer`**: The admin user endpoint now returns nested `profile` data (`full_name`, `phone_number`, `role`, `image_path`).
2. **`ProductListSerializer`**: Product lists now include `approval_status`, `rejection_reason`, `vendor_id`, `vendor_name`, `mrp`, `brand`, and `colors`.
3. **`PayoutAdminSerializer`**: Payouts now include `vendor_email`, `vendor_logo`, and detailed `bank_details`.
4. **`OrderAdminSerializer`**: Admin order lists now pull the vendor's actual `business_logo`.


