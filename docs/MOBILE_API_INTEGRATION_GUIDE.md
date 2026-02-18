# BeSmart Mobile App — API Integration Guide

> **Base URL:** `https://web-production-7cd3c.up.railway.app`
> **Auth:** All authenticated endpoints require `Authorization: Bearer <supabase_access_token>`
> **Content-Type:** `application/json` (unless noted otherwise)
> **IDs:** All IDs are UUID strings
> **Dates:** ISO 8601 (`2026-02-15T10:30:00Z`)
> **Pagination:** Most list endpoints return `{ count, next, previous, results }` with 20 items/page. Pass `?page=2` for next page.

---

## Table of Contents

1. [Authentication Flow](#1-authentication-flow)
2. [Home Screen](#2-home-screen)
3. [Category & Browsing](#3-category--browsing)
4. [Product Search](#4-product-search)
5. [Product Detail Page (PDP)](#5-product-detail-page-pdp)
6. [Reviews & Q&A](#6-reviews--qa)
7. [Cart](#7-cart)
8. [Wishlist](#8-wishlist)
9. [Checkout & Orders](#9-checkout--orders)
10. [Payment](#10-payment)
11. [Order Management](#11-order-management)
12. [User Profile & Settings](#12-user-profile--settings)
13. [Shipping Addresses](#13-shipping-addresses)
14. [Vendor Pages](#14-vendor-pages)
15. [UJUNWA AI Chat](#15-ujunwa-ai-chat)
16. [Loyalty & Rewards](#16-loyalty--rewards)
17. [Currency](#17-currency)
18. [Support](#18-support)
19. [Content & CMS](#19-content--cms)
20. [Payment Methods](#20-payment-methods)
21. [Account Deletion](#21-account-deletion)

---

## 1. Authentication Flow

Authentication is handled by **Supabase** through the Django backend as a proxy. The backend validates tokens via Supabase on every authenticated request.

### 1.1 Register

```
POST /api/users/register/
```

**Auth:** None

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email |
| password | string | Yes | Password |
| first_name | string | No | User's first name |

**Response (201):**
```json
{
  "message": "Registration successful. Please check your email for verification.",
  "user": { "id": "uuid", "email": "user@example.com" },
  "session": null
}
```

> **Note:** `session` is `null` if Supabase email confirmation is enabled. User must verify email first.

---

### 1.2 Login

```
POST /api/users/login/
```

**Auth:** None

| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| password | string | Yes |

**Response (200):**
```json
{
  "message": "Login successful.",
  "user": { "id": "uuid", "email": "user@example.com" },
  "session": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "abc123...",
    "expires_in": 3600,
    "token_type": "bearer"
  }
}
```

> **Important:** Store `access_token` and use it as `Authorization: Bearer <access_token>` for all subsequent authenticated requests.

---

### 1.3 Logout

```
POST /api/users/logout/
```

**Auth:** Required

**Response (200):**
```json
{ "message": "Logged out successfully." }
```

---

### 1.4 Password Reset (Request Link)

```
POST /api/users/password/reset/
```

**Auth:** None

| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| redirect_to | string | No |

---

### 1.5 Change Password (Logged In)

```
POST /api/users/password/change/
```

**Auth:** Required

| Field | Type | Required |
|-------|------|----------|
| password | string | Yes (new password) |

---

## 2. Home Screen

Call these endpoints when the home screen loads:

| API | Purpose | When to Call |
|-----|---------|--------------|
| `GET /api/content/hero-section/` | Hero banner/slider | On screen load |
| `GET /api/content/banners/` | Promotional banners | On screen load |
| `GET /api/categories/` | Category grid/chips | On screen load |
| `GET /api/products/featured/` | Featured products section | On screen load |
| `GET /api/products/new-arrivals/` | New arrivals section | On screen load |
| `GET /api/products/on-sale/` | Deals/sale section | On screen load |
| `GET /api/vendors/featured/` | Featured vendors section | On screen load (if shown) |

### Example — Featured Products

```
GET /api/products/featured/
```

**Auth:** None

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "Premium Sneakers",
    "price": 15000.00,
    "images": "https://...",
    "rating": 4.5,
    "reviews": 23,
    "is_on_sale": true,
    "sale_price": 12000.00,
    "discount_percentage": 20,
    "vendor_name": "Nike Store"
  }
]
```

---

## 3. Category & Browsing

### 3.1 List All Categories

```
GET /api/categories/
```

**Auth:** None — **Query Params:** `?search=shoes&ordering=name`

### 3.2 Get Subcategories

```
GET /api/categories/{id}/subcategories/
```

### 3.3 Get Products in Category

```
GET /api/categories/{id}/products/
```

**Flow:** Home → Tap Category → Load subcategories + products

---

## 4. Product Search

### 4.1 Text Search

```
GET /api/products/search/?search=running+shoes
```

**Auth:** None

### 4.2 Full Product List with Filters

```
GET /api/products/?category_id=uuid&price__gte=1000&price__lte=5000&brand=Nike&ordering=-price
```

**Available filters:** `category_id`, `is_featured`, `is_new_arrival`, `is_on_sale`, `price__gte`, `price__lte`, `brand`, `vendor_id`, `search`, `ordering`

### 4.3 Image Search

```
POST /api/products/search-by-image/
Content-Type: multipart/form-data
```

**Auth:** Required

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | file | Yes | Image file (max 20MB, JPEG/PNG/WebP) |

**Response (200):**
```json
{
  "description": "The image shows white running sneakers...",
  "products": [ { ...product objects... } ],
  "count": 5
}
```

### 4.4 Log Search Analytics

```
POST /api/search/analytics/
```

| Field | Type |
|-------|------|
| query | string |
| result_count | int |
| filters | object |

---

## 5. Product Detail Page (PDP)

When user taps on a product, load the detail page by calling these endpoints. You can call them in parallel for speed.

| API | Purpose | Required |
|-----|---------|----------|
| `GET /api/products/{id}/` | Core product data | Yes |
| `GET /api/products/{id}/specifications/` | Specs table | Yes |
| `GET /api/products/{id}/highlights/` | Key highlights | Yes |
| `GET /api/products/{id}/delivery-info/` | Delivery/shipping info | Yes |
| `GET /api/products/{id}/warranty-info/` | Warranty details | Yes |
| `GET /api/products/{id}/offers/` | Active offers/coupons | Yes |
| `GET /api/products/{id}/feature-posters/` | Feature images | If applicable |
| `GET /api/products/{id}/reviews-summary/` | Rating bar & stats | Yes |
| `GET /api/products/{id}/recommendations/` | Similar/related products | Yes |
| `GET /api/products/{id}/size-chart/` | Size guide (if apparel) | If applicable |
| `POST /api/products/{id}/view/` | Track that user viewed this product | Fire-and-forget |

### 5.1 Product Detail

```
GET /api/products/{id}/
```

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Premium Running Shoes",
  "description": "...",
  "price": 15000.00,
  "sale_price": 12000.00,
  "images": "https://...",
  "sizes": ["S", "M", "L", "XL"],
  "colors": { "Black": "#000", "White": "#FFF" },
  "brand": "Nike",
  "in_stock": true,
  "vendor_id": "uuid",
  "vendor_name": "Nike Store",
  "category_id": "uuid",
  "rating": 4.5,
  "reviews": 23,
  "is_on_sale": true,
  "discount_percentage": 20,
  "sku": "NK-RS-001"
}
```

### 5.2 Recommendations

```
GET /api/products/{id}/recommendations/
```

**Response:**
```json
{
  "similar_products": [ ...products... ],
  "from_seller_products": [ ...products... ],
  "you_might_also_like": [ ...products... ]
}
```

### 5.3 Delivery Info

```
GET /api/products/{id}/delivery-info/
```

**Response:**
```json
{
  "return_window_days": 30,
  "cod_eligible": true,
  "free_shipping_eligible": true,
  "shipping_fee": 500.00,
  "estimated_delivery_days": 5,
  "delivery_info": { ...additional info... }
}
```

---

## 6. Reviews & Q&A

### 6.1 Check if User Can Review

```
GET /api/products/{id}/can-review/
```

**Auth:** Required

**Response:**
```json
{
  "can_review": true,
  "has_existing_review": false,
  "order_id": "uuid"
}
```

> **When to call:** Before showing "Write Review" button. Only allow if `can_review` is `true`.

### 6.2 Get Reviews (with Filters)

```
GET /api/products/{id}/reviews/?rating=5&has_media=true&sort_by=rating&sort_order=desc
```

**Auth:** None

**Query Params:**

| Param | Values | Description |
|-------|--------|-------------|
| rating | 1-5 | Filter by star rating |
| has_media | true | Only reviews with images |
| sort_by | created_at, rating, helpful_count | Sort field |
| sort_order | asc, desc | Sort direction |

**Response:**
```json
{
  "count": 23,
  "results": [
    {
      "id": "uuid",
      "user": { "id": "uuid", "email": "..." },
      "rating": 5,
      "title": "Amazing shoes!",
      "content": "Very comfortable...",
      "images": ["https://..."],
      "helpful_count": 12,
      "verified_purchase": true,
      "created_at": "2026-02-10T..."
    }
  ],
  "summary": {
    "average_rating": 4.5,
    "total_reviews": 23,
    "histogram": [1, 2, 3, 5, 12]
  }
}
```

### 6.3 Submit Review

```
POST /api/products/{id}/reviews/
```

**Auth:** Required

| Field | Type | Required |
|-------|------|----------|
| rating | int (1-5) | Yes |
| title | string | No |
| content | string | No |
| images | array of URLs | No |
| order_id | uuid | No |

### 6.4 Mark Review Helpful

```
POST /api/reviews/{review_id}/helpful/
```

**Auth:** Required

### 6.5 Report Review

```
POST /api/reviews/{review_id}/report/
```

**Auth:** Required — **Body:** `{ "reason": "Spam" }`

### 6.6 Get Q&A

```
GET /api/products/{id}/qa/?search=battery&has_answer=true
```

**Auth:** None

### 6.7 Ask Question

```
POST /api/products/{id}/qa/
```

**Auth:** Required — **Body:** `{ "question": "Is this waterproof?" }`

### 6.8 Mark Q&A Helpful

```
POST /api/products/{id}/qa/{qa_id}/helpful/
```

**Auth:** Required

---

## 7. Cart

### 7.1 Get Cart

```
GET /api/cart/
```

**Auth:** Required

**Response:**
```json
{
  "id": "uuid",
  "items": [
    {
      "id": "uuid",
      "product": { ...product data... },
      "quantity": 2,
      "selected_size": "L",
      "selected_color": "Black"
    }
  ],
  "total_items": 3,
  "total_price": 45000.00,
  "updated_at": "2026-02-15T..."
}
```

### 7.2 Add Item to Cart

```
POST /api/cart/items/
```

**Auth:** Required

| Field | Type | Required |
|-------|------|----------|
| product_id | uuid | Yes |
| quantity | int | Yes (default 1) |
| selected_size | string | No |
| selected_color | string | No |

### 7.3 Update Cart Item Quantity

```
PATCH /api/cart/items/{item_id}/
```

**Auth:** Required — **Body:** `{ "quantity": 3 }`

### 7.4 Remove Cart Item

```
DELETE /api/cart/items/{item_id}/
```

**Auth:** Required — **Response:** 204 No Content

### 7.5 Clear Cart

```
POST /api/cart/clear/
```

**Auth:** Required

### 7.6 Cart Summary (for badge/header count)

```
GET /api/cart/summary/
```

**Auth:** Required

**Response:**
```json
{
  "total_items": 3,
  "subtotal": 45000.00,
  "total": 45000.00
}
```

---

## 8. Wishlist

### 8.1 Get Wishlist

```
GET /api/wishlist/
```

**Auth:** Required

### 8.2 Add to Wishlist

```
POST /api/wishlist/
```

**Auth:** Required — **Body:** `{ "product_id": "uuid" }`

### 8.3 Remove from Wishlist

```
DELETE /api/wishlist/{wishlist_item_id}/
```

**Auth:** Required

### 8.4 Move to Cart

```
POST /api/wishlist/{wishlist_item_id}/move-to-cart/
```

**Auth:** Required

### 8.5 Clear Wishlist

```
DELETE /api/wishlist/clear/
```

**Auth:** Required

---

## 9. Checkout & Orders

### Checkout Flow

```
1. GET  /api/cart/                          → Show cart items
2. GET  /api/shipping-addresses/            → Show saved addresses
3. GET  /api/payments/methods/              → Show saved payment methods
4. POST /api/loyalty/validate-voucher/      → (Optional) Validate discount code
5. POST /api/orders/                        → Create order
6. POST /api/payments/initiate/             → Initiate payment (if not COD)
7. GET  /api/payments/verify/{ref}/         → Verify payment after redirect
8. PATCH /api/orders/{id}/payment-status/   → Update payment status
```

### 9.1 Create Order (from Cart)

```
POST /api/orders/
```

**Auth:** Required

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| address_id | uuid | Yes | Shipping address |
| payment_method_id | uuid | No | Saved payment method |
| shipping_method | string | Yes | `cash_on_delivery`, `credit_card`, `debit_card`, `upi`, `net_banking` |
| loyalty_voucher_code | string | No | Discount code |
| notes | string | No | Order notes |
| squad_transaction_ref | string | No | Squad payment reference (if pre-paid) |
| payment_status | string | No | `pending` or `paid` |

> Cart items are automatically converted to order items and the cart is cleared.

### 9.2 Create Order (Direct Items — No Cart)

```
POST /api/orders/
```

Same as above, but include `items` array instead of relying on cart:

```json
{
  "address_id": "uuid",
  "shipping_method": "credit_card",
  "items": [
    { "product_id": "uuid", "quantity": 2, "selected_size": "L", "selected_color": "Black" },
    { "product_id": "uuid", "quantity": 1 }
  ]
}
```

### 9.3 Validate Voucher

```
POST /api/loyalty/validate-voucher/
```

**Auth:** Required

| Field | Type |
|-------|------|
| voucher_code | string |
| order_subtotal | number |

**Response:**
```json
{
  "valid": true,
  "voucher_id": "uuid",
  "discount_amount": 500.00,
  "discount_type": "fixed",
  "minimum_order_amount": 2000.00
}
```

---

## 10. Payment

### 10.1 Initiate Payment (Squad Gateway)

```
POST /api/payments/initiate/
```

**Auth:** Required

| Field | Type | Required |
|-------|------|----------|
| order_id | uuid | Yes |
| amount | number | Yes |
| email | string | Yes |

**Response:**
```json
{
  "status": "success",
  "data": {
    "transaction_ref": "SQ-abc123...",
    "checkout_url": "https://sandbox.squadco.com/pay?ref=SQ-abc123"
  }
}
```

> **Flow:** Open `checkout_url` in a WebView. After payment completes, Squad redirects back. Then call verify.

### 10.2 Verify Payment

```
GET /api/payments/verify/{transaction_ref}/
```

**Auth:** Required

**Response:**
```json
{ "status": "success", "message": "Payment verified and order confirmed" }
```

### 10.3 Update Order Payment Status

```
PATCH /api/orders/{id}/payment-status/
```

**Auth:** Required

| Field | Type | Description |
|-------|------|-------------|
| payment_status | string | `paid`, `failed`, `refunded` |
| squad_gateway_ref | string | Gateway reference |
| escrow_status | string | Escrow status |

> **When to call:** After Squad webhook/redirect confirms payment. If `payment_status` = `paid`, order auto-confirms.

---

## 11. Order Management

### 11.1 List My Orders

```
GET /api/orders/
```

**Auth:** Required

### 11.2 Order Detail

```
GET /api/orders/{id}/
```

**Auth:** Required

### 11.3 Track Order

```
GET /api/orders/{id}/track/
```

**Auth:** Required

**Response:**
```json
{
  "order_id": "uuid",
  "status": "shipped",
  "tracking_number": "TRK123456",
  "tracking_url": "https://...",
  "estimated_delivery": "2026-02-20T...",
  "timeline": [
    { "status": "pending", "timestamp": "...", "description": "Order placed" },
    { "status": "confirmed", "timestamp": "...", "description": "Payment confirmed" },
    { "status": "shipped", "timestamp": "...", "description": "Shipped via DHL" }
  ]
}
```

### 11.4 Cancel Order

```
POST /api/orders/{id}/cancel/
```

**Auth:** Required

> Only works if order status is `pending`, `processing`, or `confirmed`.

### 11.5 Reorder

```
POST /api/orders/{id}/reorder/
```

**Auth:** Required — Creates a new order with the same items.

### 11.6 Get Invoice

```
GET /api/orders/{id}/invoice/
```

**Auth:** Required — Returns invoice JSON with all order, item, and total details.

---

## 12. User Profile & Settings

### 12.1 Get Profile

```
GET /api/users/me/
```

**Auth:** Required

### 12.2 Update Profile

```
PATCH /api/users/profile/
```

**Auth:** Required — **Body:** Profile fields (first_name, last_name, phone, etc.)

---

## 13. Shipping Addresses

### 13.1 List Addresses

```
GET /api/shipping-addresses/
```

**Auth:** Required

### 13.2 Add Address

```
POST /api/shipping-addresses/
```

**Auth:** Required

| Field | Type | Required |
|-------|------|----------|
| name | string | Yes |
| phone | string | Yes |
| address_line1 | string | Yes |
| address_line2 | string | No |
| city | string | Yes |
| state | string | Yes |
| zip | string | Yes |
| country | string | Yes |
| is_default | bool | No |
| type | string | No (`home`, `work`, `other`) |

### 13.3 Update Address

```
PATCH /api/shipping-addresses/{id}/
```

**Auth:** Required

### 13.4 Delete Address

```
DELETE /api/shipping-addresses/{id}/
```

**Auth:** Required

### 13.5 Set Default Address

```
POST /api/shipping-addresses/{id}/set-default/
```

**Auth:** Required

---

## 14. Vendor Pages

### 14.1 Browse Vendors

| API | Purpose |
|-----|---------|
| `GET /api/vendors/` | List all approved vendors |
| `GET /api/vendors/featured/` | Featured vendors |
| `GET /api/vendors/search/?q=nike` | Search vendors |

### 14.2 Vendor Detail Page

| API | Purpose |
|-----|---------|
| `GET /api/vendors/{id}/` | Vendor info + `follower_count` |
| `GET /api/vendors/{id}/products/` | Vendor's products |
| `GET /api/vendors/{id}/reviews/` | Vendor reviews |
| `GET /api/vendors/{id}/followers/` | Follower count + list |
| `GET /api/vendors/{id}/follow/` | Check if I follow this vendor |

### 14.3 Follow/Unfollow

```
POST /api/vendors/{id}/follow/    → Follow
DELETE /api/vendors/{id}/follow/  → Unfollow
GET /api/vendors/{id}/follow/     → Check status → { "is_following": true }
```

**Auth:** Required for all

### 14.4 My Followed Vendors

```
GET /api/vendors/following/
```

**Auth:** Required

### 14.5 Review Vendor

```
POST /api/vendors/{id}/reviews/
```

**Auth:** Required — **Body:** `{ "rating": 5, "review_text": "Great seller!" }`

### 14.6 Get My Review for Vendor

```
GET /api/vendors/{id}/my-review/
```

**Auth:** Required

---

## 15. UJUNWA AI Chat

### 15.1 Send Message

```
POST /api/support/chat/send/
```

**Auth:** Required

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | Yes | User's message |
| conversation_id | uuid | No | Existing conversation (omit to create new) |

**Response:**
```json
{
  "conversation_id": "uuid",
  "user_message": {
    "id": "uuid",
    "sender_type": "user",
    "message_text": "Show me running shoes under 10000",
    "message_type": "text",
    "created_at": "2026-02-15T..."
  },
  "bot_response": {
    "id": "uuid",
    "sender_type": "bot",
    "message_text": "Here are some great running shoes...",
    "message_type": "product",
    "metadata": {
      "intent_type": "product_search",
      "intent_confidence": 0.95,
      "products_count": 5,
      "product_ids": ["uuid1", "uuid2"],
      "suggestions": ["Try filtering by brand", "Check our sale section"]
    },
    "products": [ { ...full product objects... } ],
    "created_at": "2026-02-15T..."
  }
}
```

> **Important:** If `message_type` is `"product"`, render the products array as a product carousel in the chat.

### 15.2 List Conversations

```
GET /api/support/chat/
```

**Auth:** Required — Returns conversations ordered by `last_message_at` DESC.

### 15.3 Get Messages in Conversation

```
GET /api/support/chat/{conversation_id}/messages/
```

**Auth:** Required

### 15.4 Mark Messages as Read

```
POST /api/support/chat/{conversation_id}/messages/mark-read/
```

**Auth:** Required — **Body:** `{ "sender_type": "bot" }`

### 15.5 Unread Message Count (for badge)

```
GET /api/support/chat/unread-count/
```

**Auth:** Required

**Response:** `{ "unread_count": 3 }`

> **When to call:** On app launch and periodically to update chat badge.

### 15.6 Search Messages

```
GET /api/support/chat/messages/search/?q=shoes&limit=20
```

**Auth:** Required

### 15.7 Clear Chat History

```
POST /api/support/chat/clear-history/
```

**Auth:** Required — Deletes all conversations, messages, analytics, and context.

### 15.8 Track Analytics

```
POST /api/support/chat/analytics/
```

**Auth:** Required — **Body:** `{ "conversation_id": "uuid", "action_type": "message_sent", "action_data": {} }`

---

## 16. Loyalty & Rewards

### 16.1 Get Points Balance

```
GET /api/loyalty/points/
```

**Auth:** Required

### 16.2 Get Tier Info

```
GET /api/loyalty/tier-info/
```

**Auth:** Required

**Response:**
```json
{
  "tier": "Gold",
  "tier_multiplier": 1.5,
  "tier_progress": 75,
  "next_tier": "Platinum",
  "points_to_next_tier": 500,
  "lifetime_points": 3500,
  "points_balance": 1200
}
```

### 16.3 Transaction History

```
GET /api/loyalty/transactions/
```

### 16.4 Available Rewards

```
GET /api/loyalty/rewards/
```

### 16.5 Redeem Reward

```
POST /api/loyalty/redeem/
```

**Auth:** Required — **Body:** `{ "reward_id": "uuid" }`

### 16.6 My Vouchers

```
GET /api/loyalty/vouchers/
```

### 16.7 Badges

| API | Purpose |
|-----|---------|
| `GET /api/loyalty/badges/` | All available badges |
| `GET /api/loyalty/user-badges/` | My badges with progress |
| `GET /api/loyalty/badge-progress/` | Badge progress details |

---

## 17. Currency

### 17.1 Get All Rates

```
GET /api/currency/rates/
```

**Auth:** None

### 17.2 Get Specific Exchange Rate

```
GET /api/currency/rate/?from=USD&to=NGN
```

**Auth:** None

**Response:** `{ "from_currency": "USD", "to_currency": "NGN", "rate": 1500.00 }`

### 17.3 Convert Amount

```
POST /api/currency/convert/
```

**Auth:** None — **Body:** `{ "amount": 100, "from_currency": "USD", "to_currency": "NGN" }`

### 17.4 User Currency Preference

```
GET /api/currency/preference/           → Get preference
PATCH /api/currency/preference/         → Update → { "currency_code": "USD" }
```

**Auth:** Required

---

## 18. Support

### Contact Branches

```
GET /api/support/branches/
```

**Auth:** None — Returns list of active contact/support branches.

---

## 19. Content & CMS

| API | Purpose | Auth |
|-----|---------|------|
| `GET /api/content/hero-section/` | Homepage hero slider | None |
| `GET /api/content/banners/` | Promotional banners | None |
| `GET /api/content/faqs/` | FAQ list | None |
| `GET /api/content/support-info/?type=faq` | Support info filtered by type | None |
| `GET /api/content/contact-info/` | Contact information | None |

---

## 20. Payment Methods

### 20.1 List Saved Cards

```
GET /api/payments/methods/
```

**Auth:** Required

### 20.2 Add Payment Method

```
POST /api/payments/methods/
```

**Auth:** Required

### 20.3 Update Payment Method

```
PATCH /api/payments/methods/{id}/
```

**Auth:** Required

### 20.4 Delete Payment Method

```
DELETE /api/payments/methods/{id}/
```

**Auth:** Required

> If the deleted card was the default, the next remaining card is automatically promoted to default.

### 20.5 Set Default Payment Method

```
POST /api/payments/methods/{id}/set-default/
```

**Auth:** Required

---

## 21. Account Deletion

### 21.1 Check Eligibility

```
GET /api/users/account/deletion-eligibility/
```

**Auth:** Required

**Response:**
```json
{ "eligible": true, "message": "Your account is eligible for deletion.", "is_vendor": false }
```

> If `eligible` is `false` (active vendor account), show the error message and don't allow deletion.

### 21.2 Delete Account

```
POST /api/users/account/delete/
```

**Auth:** Required — **Body:** `{ "password": "current_password" }`

---

## Size Charts

### Category-Level Size Chart

```
GET /api/categories/{id}/size-chart/        → Get size chart for category
GET /api/categories/{id}/has-size-chart/     → Boolean check → { "has_size_chart": true }
```

### Product-Level Size Chart

```
GET /api/products/{id}/size-chart/           → Get size chart for specific product
```

---

## Error Handling

All error responses follow this format:

```json
{ "error": "Description of what went wrong" }
```

Or for validation errors:

```json
{ "field_name": ["Error message 1", "Error message 2"] }
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (not allowed) |
| 404 | Not Found |
| 500 | Server Error |

---

## API Documentation (Interactive)

For interactive testing and a full OpenAPI schema:

| URL | Description |
|-----|-------------|
| `GET /api/docs/` | Swagger UI (interactive) |
| `GET /api/redoc/` | ReDoc (readable) |
| `GET /api/schema/` | Raw OpenAPI JSON schema |

---

*Last updated: February 15, 2026*
*Total endpoints: 123+*
*Backend: Django REST Framework on Railway*
*Auth: Supabase (Bearer token)*
*Payment: Squad Gateway*
