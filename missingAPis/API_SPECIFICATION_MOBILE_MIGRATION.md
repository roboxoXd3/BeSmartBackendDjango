# API Specification: Mobile App Migration

> **For:** Backend Developer  
> **Purpose:** Implement missing APIs so the Flutter mobile app can switch from Supabase to the Django backend.  
> **Total Endpoints:** 48

**Conventions:**
- All dates: ISO 8601 strings (e.g. `"2026-02-12T10:30:00Z"`)
- IDs: UUID strings
- Auth: `Authorization: Bearer <access_token>` (JWT)
- Base path: `/api/` unless noted

---

## 1. Shipping Addresses (5 endpoints)

### 1.1 List Addresses
```
GET /api/shipping-addresses/
```
**Auth:** Required  
**Response 200:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "name": "John Doe",
    "phone": "+1234567890",
    "address_line1": "123 Main St",
    "address_line2": "Apt 4",
    "city": "Lagos",
    "state": "Lagos",
    "zip": "100001",
    "country": "Nigeria",
    "is_default": true,
    "created_at": "2026-02-12T10:00:00Z"
  }
]
```
**Logic:** Return addresses for current user, ordered by `is_default` DESC then `created_at` DESC.

---

### 1.2 Add Address
```
POST /api/shipping-addresses/
```
**Auth:** Required  
**Body:**
```json
{
  "name": "string, required",
  "phone": "string, required",
  "address_line1": "string, required",
  "address_line2": "string, optional",
  "city": "string, required",
  "state": "string, required",
  "zip": "string, required",
  "country": "string, required",
  "is_default": "boolean, default false"
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "...",
  "phone": "...",
  "address_line1": "...",
  "address_line2": null,
  "city": "...",
  "state": "...",
  "zip": "...",
  "country": "...",
  "is_default": false,
  "created_at": "2026-02-12T10:00:00Z"
}
```
**Logic:** If `is_default=true`, set all other user addresses to `is_default=false`. If first address, default to `is_default=true`.

---

### 1.3 Update Address
```
PATCH /api/shipping-addresses/{id}/
```
**Auth:** Required  
**Body:** Same as Add (all fields optional)  
**Response 200:** Updated address object  
**Logic:** User can only update own addresses. If setting `is_default=true`, clear others.

---

### 1.4 Delete Address
```
DELETE /api/shipping-addresses/{id}/
```
**Auth:** Required  
**Response 204:** No content  
**Logic:** User can only delete own addresses. If deleted address was default, set first remaining as default.

---

### 1.5 Set Default Address
```
POST /api/shipping-addresses/{id}/set-default/
```
**Auth:** Required  
**Response 200:**
```json
{
  "success": true,
  "message": "Default address updated"
}
```
**Logic:** Set `is_default=true` for this address, `false` for all other user addresses.

---

## 2. Orders (5 endpoints)

### 2.1 Create Order (implement full logic)
```
POST /api/orders/
```
**Auth:** Required  
**Body:**
```json
{
  "address_id": "uuid, required",
  "payment_method_id": "uuid or null (for cash_on_delivery)",
  "shipping_method": "string: cash_on_delivery | credit_card | debit_card | upi | net_banking",
  "loyalty_voucher_code": "string, optional",
  "notes": "string, optional"
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "address_id": "uuid",
  "payment_method_id": null,
  "shipping_method": "cash_on_delivery",
  "subtotal": 15000.00,
  "shipping_fee": 0.00,
  "total": 15000.00,
  "status": "pending",
  "created_at": "2026-02-12T10:00:00Z",
  "items": [
    {
      "id": "uuid",
      "order_id": "uuid",
      "product_id": "uuid",
      "quantity": 2,
      "price": 7500.00,
      "selected_size": "M",
      "selected_color": "Blue",
      "product_name": "Product Name",
      "vendor_id": "uuid",
      "vendor_name": "Vendor Business"
    }
  ],
  "squad_transaction_ref": null,
  "squad_gateway_ref": null,
  "payment_status": "pending",
  "escrow_status": null,
  "escrow_release_date": null
}
```
**Logic:** Create order from user's cart. Validate address belongs to user. Apply voucher if provided. Clear cart on success. Create order_items from cart_items. If Squad payment, return checkout_url etc. (existing initiate flow may handle that separately).

---

### 2.2 Cancel Order
```
POST /api/orders/{id}/cancel/
```
**Auth:** Required  
**Response 200:**
```json
{
  "success": true,
  "order": { /* full order object */ },
  "message": "Order cancelled successfully"
}
```
**Logic:** Only allow cancel if status is `pending` or `processing`. Set status to `cancelled`.

---

### 2.3 Track Order
```
GET /api/orders/{id}/track/
```
**Auth:** Required  
**Response 200:**
```json
{
  "order_id": "uuid",
  "status": "shipped",
  "status_display": "Shipped",
  "tracking_number": "TRK123456",
  "estimated_delivery": "2026-02-18T00:00:00Z",
  "timeline": [
    {
      "status": "pending",
      "timestamp": "2026-02-12T10:00:00Z",
      "description": "Order placed"
    },
    {
      "status": "processing",
      "timestamp": "2026-02-12T14:00:00Z",
      "description": "Order is being prepared"
    },
    {
      "status": "shipped",
      "timestamp": "2026-02-13T09:00:00Z",
      "description": "Order shipped"
    }
  ]
}
```

---

### 2.4 Reorder
```
POST /api/orders/{id}/reorder/
```
**Auth:** Required  
**Response 201:** New order object (same as Create)  
**Logic:** Create new order from order_items of given order. Add same items to cart or create order directly.

---

### 2.5 Get Invoice
```
GET /api/orders/{id}/invoice/
```
**Auth:** Required  
**Response 200:** PDF or JSON invoice data  
**Accept:** `application/pdf` or `application/json`  
**Logic:** Return invoice data (order, items, address, totals). PDF optional.

---

## 3. Vendors – Customer-facing (10 endpoints)

### 3.1 List Vendors
```
GET /api/vendors/
```
**Auth:** Optional (public)  
**Query:** `?search=<term>&featured=true&limit=20&offset=0`  
**Response 200:**
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "business_name": "string",
      "business_description": "string",
      "business_logo": "url",
      "business_email": "string",
      "business_phone": "string",
      "business_address": "string",
      "status": "approved",
      "is_featured": false,
      "average_rating": 4.5,
      "total_reviews": 120,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-02-12T00:00:00Z"
    }
  ]
}
```
**Logic:** Filter `status=approved`, `is_active=true`. Support search on `business_name` (ilike).

---

### 3.2 Get Featured Vendors
```
GET /api/vendors/featured/
```
**Auth:** Optional  
**Response 200:** Same list structure, filter `is_featured=true`.

---

### 3.3 Search Vendors
```
GET /api/vendors/search/?q=<query>
```
**Auth:** Optional  
**Response 200:** Same list structure.

---

### 3.4 Get Vendor Detail
```
GET /api/vendors/{id}/
```
**Auth:** Optional  
**Response 200:** Single vendor object (same fields as list item).

---

### 3.5 Get Vendor Products
```
GET /api/vendors/{id}/products/
```
**Auth:** Optional  
**Query:** `?limit=20&offset=0`  
**Response 200:** Product list (use existing product serializer). Filter by `vendor_id`, `approval_status=approved`, `in_stock=true`.

---

### 3.6 Get Vendor Reviews
```
GET /api/vendors/{id}/reviews/
```
**Auth:** Optional  
**Query:** `?limit=20&offset=0`  
**Response 200:**
```json
[
  {
    "id": "uuid",
    "vendor_id": "uuid",
    "user_id": "uuid",
    "user_name": "John Doe",
    "user_avatar": "url",
    "rating": 4.5,
    "review_text": "string",
    "created_at": "2026-02-10T00:00:00Z",
    "updated_at": "2026-02-10T00:00:00Z"
  }
]
```

---

### 3.7 Follow Vendor
```
POST /api/vendors/{id}/follow/
```
**Auth:** Required  
**Response 201:**
```json
{
  "success": true,
  "message": "You are now following this vendor"
}
```
**Logic:** Insert into `vendor_follows` (user_id, vendor_id). Idempotent if already following.

---

### 3.8 Unfollow Vendor
```
DELETE /api/vendors/{id}/follow/
```
**Auth:** Required  
**Response 204:** No content  
**Logic:** Delete from `vendor_follows`.

---

### 3.9 Add Vendor Review
```
POST /api/vendors/{id}/reviews/
```
**Auth:** Required  
**Body:**
```json
{
  "rating": 4.5,
  "review_text": "string, optional"
}
```
**Response 201:** Created review object  
**Logic:** Get user name/avatar from profile. One review per user per vendor. Upsert or reject duplicate.

---

### 3.10 Update / Delete Vendor Review
```
PATCH /api/vendors/reviews/{id}/
DELETE /api/vendors/reviews/{id}/
```
**Auth:** Required  
**Body (PATCH):** `{ "rating": 4, "review_text": "..." }`  
**Logic:** User can only update/delete own review.

---

## 4. Product Reviews & Q&A (7 endpoints)

### 4.1 Get Product Reviews
```
GET /api/products/{id}/reviews/
```
**Auth:** Optional  
**Query:** `?page=1&limit=20&rating=5&sort_by=created_at&sort_order=desc`  
**Response 200:**
```json
{
  "count": 45,
  "results": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "user_id": "uuid",
      "order_id": "uuid",
      "rating": 5,
      "title": "string",
      "content": "string",
      "images": ["url1", "url2"],
      "verified_purchase": true,
      "helpful_count": 12,
      "reported_count": 0,
      "status": "published",
      "vendor_response": null,
      "vendor_response_date": null,
      "created_at": "2026-02-10T00:00:00Z",
      "updated_at": "2026-02-10T00:00:00Z"
    }
  ],
  "summary": {
    "average_rating": 4.3,
    "total_reviews": 45,
    "histogram": [2, 5, 10, 15, 13]
  }
}
```
**Note:** `histogram` = [1-star, 2-star, 3-star, 4-star, 5-star] counts.

---

### 4.2 Submit Product Review
```
POST /api/products/{id}/reviews/
```
**Auth:** Required  
**Body:**
```json
{
  "order_id": "uuid, required (must be delivered/completed order containing this product)",
  "rating": 1-5,
  "title": "string, required",
  "content": "string, required",
  "images": ["url1", "url2"]
}
```
**Response 201:** Created review object  
**Logic:** Verify user has purchased product (order_items with product_id, order status delivered/completed). One review per user per product.

---

### 4.3 Mark Review Helpful
```
POST /api/reviews/{id}/helpful/
```
**Auth:** Required  
**Response 200:** `{ "success": true, "helpful_count": 13 }`  
**Logic:** Increment `helpful_count`. Consider user id for "one vote per user" if needed.

---

### 4.4 Report Review
```
POST /api/reviews/{id}/report/
```
**Auth:** Required  
**Body:** `{ "reason": "string, optional" }`  
**Response 200:** `{ "success": true }`  
**Logic:** Increment `reported_count` or store in reports table.

---

### 4.5 Get Product Q&A
```
GET /api/products/{id}/qa/
```
**Auth:** Optional  
**Query:** `?page=1&limit=20&status=all&has_answer=answered|unanswered&sort_by=created_at&sort_order=desc`  
**Response 200:**
```json
{
  "count": 30,
  "results": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "user_id": "uuid",
      "question": "string",
      "answer": "string or null",
      "answered_by": "uuid",
      "answered_at": "datetime or null",
      "vendor_response": "string or null",
      "vendor_response_date": "datetime or null",
      "is_helpful_count": 5,
      "is_verified": false,
      "status": "published|pending|answered",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "stats": {
    "total": 30,
    "answered": 25,
    "unanswered": 5
  }
}
```

---

### 4.6 Submit Question
```
POST /api/products/{id}/qa/
```
**Auth:** Required  
**Body:**
```json
{
  "question": "string, required"
}
```
**Response 201:** Created Q&A object (status=published or pending).

---

### 4.7 Mark Q&A Helpful
```
POST /api/products/{id}/qa/{qa_id}/helpful/
```
**Auth:** Required  
**Response 200:** `{ "success": true, "is_helpful_count": 6 }`  
**Logic:** Increment `is_helpful_count`.

---

## 5. Loyalty (4 endpoints)

### 5.1 Validate Voucher
```
POST /api/loyalty/validate-voucher/
```
**Auth:** Required  
**Body:** (App may send camelCase – accept `voucher_code` or `voucherCode`, `order_subtotal` or `orderAmount`)
```json
{
  "voucher_code": "string, required (uppercase, e.g. ABC123XYZ)",
  "order_subtotal": 15000.00
}
```
**Response 200 (valid):**
```json
{
  "valid": true,
  "voucher_id": "uuid",
  "voucher_code": "ABC123XYZ",
  "discount_type": "discount_percentage",
  "discount_amount": 1500.00,
  "discount_value": 10,
  "apply_to_shipping": false,
  "minimum_order_amount": 5000.00
}
```
**Response 200 (invalid):**
```json
{
  "valid": false,
  "error": "Invalid voucher"
}
```
**Logic:** Check voucher exists, belongs to user, not expired, not used. Check `order_subtotal >= minimum_order_amount`. Compute `discount_amount` from type (% or fixed).

---

### 5.2 User Badges
```
GET /api/loyalty/user-badges/
```
**Auth:** Required  
**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "icon_url": "url",
    "badge_type": "order_count|spending_amount|streak|special",
    "requirement_value": 10,
    "bonus_points": 50,
    "display_order": 0,
    "is_active": true,
    "is_earned": true,
    "earned_at": "2026-02-01T00:00:00Z",
    "progress": 100.0,
    "current_value": 12
  }
]
```
**Logic:** All badges + user_badges join. For each badge: is_earned, earned_at, progress (0–100), current_value (orders or spending).

---

### 5.3 Badge Progress
```
GET /api/loyalty/badge-progress/
```
**Auth:** Required  
**Response 200:**
```json
{
  "badges": [
    {
      "badge_id": "uuid",
      "badge_name": "string",
      "progress": 75.0,
      "current_value": 8,
      "requirement_value": 10,
      "is_earned": false
    }
  ]
}
```

---

### 5.4 Tier Info
```
GET /api/loyalty/tier-info/
```
**Auth:** Required  
**Response 200:**
```json
{
  "tier": "silver",
  "tier_multiplier": 1.25,
  "tier_progress": 65.0,
  "next_tier": "gold",
  "points_to_next_tier": 350,
  "lifetime_points": 650,
  "points_balance": 120
}
```
**Logic:** Derive from loyalty_points. Tiers: bronze (0), silver (500), gold (2000), platinum (5000).

---

## 6. Categories (2 endpoints)

### 6.1 Get Subcategories
```
GET /api/categories/{id}/subcategories/
```
**Auth:** Optional  
**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "category_id": "uuid",
    "is_active": true,
    "created_at": "...",
    "updated_at": "..."
  }
]
```
**Logic:** Filter by `category_id`, `is_active=true`, order by name.

---

### 6.2 Get Category Products
```
GET /api/categories/{id}/products/
```
**Auth:** Optional  
**Query:** `?limit=20&offset=0&sort=price|created_at|rating`  
**Response 200:** Product list (existing product serializer). Filter by `category_id`.

---

## 7. Content (3 endpoints)

### 7.1 Hero Section
```
GET /api/content/hero-section/
```
**Auth:** Optional  
**Response 200:**
```json
{
  "id": "uuid",
  "title": "string",
  "subtitle": "string",
  "image_url": "url",
  "video_url": "url",
  "cta_text": "string",
  "cta_link": "url",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```
**Logic:** Return single active hero section (or first).

---

### 7.2 Contact Info
```
GET /api/content/contact-info/
```
**Auth:** Optional  
**Response 200:**
```json
[
  {
    "id": "uuid",
    "title": "string",
    "subtitle": "string",
    "type": "contact",
    "icon": "string",
    "action_type": "string",
    "action_value": "string",
    "availability": "string",
    "order_index": 0
  }
]
```
**Logic:** Filter support_info by `type=contact`, order by `order_index`.

---

### 7.3 Support Info
```
GET /api/content/support-info/?type=quick_help|contact
```
**Auth:** Optional  
**Response 200:** Same structure as contact-info, filter by `type` if provided.

---

## 8. Cart & Wishlist (4 endpoints)

### 8.1 Clear Cart
```
POST /api/cart/clear/
```
**Auth:** Required  
**Response 200:** `{ "success": true, "message": "Cart cleared" }`  
**Logic:** Delete all cart_items for user's cart.

---

### 8.2 Cart Summary
```
GET /api/cart/summary/
```
**Auth:** Required  
**Response 200:**
```json
{
  "item_count": 5,
  "subtotal": 45000.00,
  "shipping_fee": 0,
  "total": 45000.00,
  "currency": "NGN"
}
```
**Logic:** Aggregate from cart items.

---

### 8.3 Move Wishlist Item to Cart
```
POST /api/wishlist/{id}/move-to-cart/
```
**Auth:** Required  
**Response 200:**
```json
{
  "success": true,
  "message": "Item moved to cart",
  "cart_item": { /* cart item object */ }
}
```
**Logic:** `{id}` is wishlist item id (product_id). Add product to cart, optionally remove from wishlist.

---

### 8.4 Clear Wishlist
```
DELETE /api/wishlist/clear/
```
**Auth:** Required  
**Response 204:** No content  
**Logic:** Delete all wishlist items for user.

---

## 9. Account Deletion (2 endpoints)

### 9.1 Check Deletion Eligibility
```
GET /api/users/account/deletion-eligibility/
```
**Auth:** Required  
**Response 200:**
```json
{
  "eligible": true,
  "message": "Your account is eligible for deletion.",
  "is_vendor": false
}
```
**Response 200 (not eligible):**
```json
{
  "eligible": false,
  "message": "Cannot delete account while you have an active vendor account...",
  "is_vendor": true,
  "error_code": "vendor_active"
}
```
**Logic:** If user has active vendor (status=approved), return eligible=false. Equivalent to RPC `is_active_vendor`.

---

### 9.2 Delete Account
```
POST /api/users/account/delete/
```
**Auth:** Required  
**Body:**
```json
{
  "password": "string, required"
}
```
**Response 200:**
```json
{
  "success": true,
  "message": "Your account has been successfully deleted."
}
```
**Response 400:**
```json
{
  "success": false,
  "error": "invalid_password|vendor_active|...",
  "message": "Error message"
}
```
**Logic:** Verify password. Check eligibility. Delete/anonymize user data. Remove auth user. GDPR compliant.

---

## 10. Search Analytics (2 endpoints)

### 10.1 Track Search
```
POST /api/search/analytics/
```
**Auth:** Required (or accept anonymous with user_id="anonymous")  
**Body:**
```json
{
  "query": "string, required",
  "result_count": 15,
  "filters": { "category_id": "uuid" }
}
```
**Response 201:** `{ "success": true }`  
**Logic:** Insert into search_analytics (query, result_count, user_id, filters, timestamp).

---

### 10.2 Get Search Analytics
```
GET /api/search/analytics/?start_date=2026-02-01&end_date=2026-02-12&limit=5
```
**Auth:** Optional (for popular searches, can be public)  
**Response 200:**
```json
{
  "popular_searches": ["shoes", "bags", "watches"],
  "total_searches": 150,
  "recent_searches": [
    {
      "query": "shoes",
      "result_count": 25,
      "timestamp": "..."
    }
  ]
}
```
**Logic:** Aggregate by query, sort by count. Optionally filter by date.

---

## 11. Products (2 endpoints)

### 11.1 Get Product Size Chart
```
GET /api/products/{id}/size-chart/
```
**Auth:** Optional  
**Response 200:**
```json
{
  "id": "uuid",
  "name": "string",
  "category_id": "uuid",
  "category_name": "string",
  "subcategory": "string",
  "measurement_types": ["chest", "waist", "hip"],
  "measurement_instructions": "string",
  "entries": [
    {
      "size_name": "S",
      "measurements": {
        "chest": "86-90 cm",
        "waist": "70-74 cm",
        "hip": "90-94 cm"
      },
      "sort_order": 0
    }
  ],
  "size_recommendations": {}
}
```
**Response 404:** If no size chart for product/category.  
**Logic:** Product custom chart > product template > category template > legacy fallback.

---

### 11.2 Track Product View
```
POST /api/products/{id}/view/
```
**Auth:** Optional (user_id if logged in)  
**Response 200:** `{ "success": true }`  
**Logic:** Increment product view count. Used for analytics/recommendations.

---

## 12. Error Response Format

All errors:
```json
{
  "error": {
    "code": "VALIDATION_ERROR|NOT_FOUND|FORBIDDEN|UNAUTHORIZED",
    "message": "Human-readable message",
    "details": {
      "field_name": ["Error for this field"]
    }
  }
}
```
**Status codes:** 400 (validation), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error).

---

## 13. Implementation Checklist

| # | Endpoint | Priority |
|---|----------|----------|
| 1 | Shipping addresses (5) | High |
| 2 | Order create + cancel/track/reorder/invoice (5) | High |
| 3 | Vendors customer-facing (10) | High |
| 4 | Product reviews & Q&A (7) | Medium |
| 5 | Loyalty validate/user-badges/badge-progress/tier (4) | High |
| 6 | Categories subcategories + products (2) | High |
| 7 | Content hero/contact/support (3) | Medium |
| 8 | Cart clear/summary, wishlist move/clear (4) | Medium |
| 9 | Account deletion (2) | High |
| 10 | Search analytics (2) | Low |
| 11 | Product size-chart, view (2) | Medium |

**Total: 48 endpoints**
