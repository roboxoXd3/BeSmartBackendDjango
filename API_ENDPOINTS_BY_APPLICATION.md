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

| Method | Endpoint | Description | Used By |
|--------|----------|-------------|---------|
| POST | `/api/auth/register/` | User registration | All |
| POST | `/api/auth/login/` | User login (JWT) | All |
| POST | `/api/auth/logout/` | User logout | All |
| POST | `/api/auth/refresh/` | Refresh JWT token | All |
| POST | `/api/auth/verify-email/` | Verify email address | All |
| POST | `/api/auth/resend-verification/` | Resend verification email | All |
| POST | `/api/auth/password-reset/` | Request password reset | All |
| POST | `/api/auth/password-reset-confirm/` | Confirm password reset | All |
| POST | `/api/auth/change-password/` | Change password | All |
| GET | `/api/auth/me/` | Get current user | All |
| PATCH | `/api/users/profile/` | Update user profile | All |
| POST | `/api/users/profile/upload-avatar/` | Upload profile picture | All |

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
