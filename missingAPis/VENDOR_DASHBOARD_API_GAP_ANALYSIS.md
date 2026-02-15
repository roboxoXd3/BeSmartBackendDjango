# Vendor Dashboard → Django Backend: API Gap Analysis

> **Purpose:** Identify missing APIs required for the vendor-dashboard (Next.js) to migrate from Supabase/Next.js API routes to BeSmartBackendDjango.  
> **No duplicates:** APIs already in `API_SPECIFICATION_MOBILE_MIGRATION.md` are excluded.

**Date:** February 12, 2026  
**Vendor Dashboard:** `vendor-dashboard` (Next.js + Supabase)  
**Backend:** `BeSmartBackendDjango`

---

## Shared vs Vendor-Only APIs

| API Area | Mobile Spec | Vendor Dashboard | Notes |
|----------|-------------|------------------|-------|
| Categories + subcategories | ✅ In Mobile spec | Same | Use `GET /api/categories/`, `GET /api/categories/{id}/subcategories/` |
| Currency | Django has | Same | Use existing `/api/currency/` |
| Auth | JWT login | **Vendor login** (different flow) | Vendor uses `vendor_sessions`; needs vendor-specific auth |
| Product reviews | Customer: list, create | **Vendor: list own, respond, hide** | Different scope – vendor dashboard needs vendor-scoped endpoints |
| Product Q&A | Customer: list, create | **Vendor: list own, answer, hide** | Different scope |

---

## Django Vendor APIs That Exist

| Endpoint | Django | Notes |
|----------|--------|------|
| `GET/PATCH /api/vendors/profile/` | ✅ | Current vendor profile |
| `GET /api/vendors/dashboard/stats/` | ✅ | Basic stats (total_sales, total_orders, etc.) |
| `GET/POST /api/vendors/payouts/` | ✅ | Payout list and create |
| `GET/POST/PATCH/DELETE /api/vendors/bank-accounts/` | ✅ | Bank accounts ViewSet |
| `GET/POST/PATCH/DELETE /api/vendors/size-charts/` | ✅ | Size chart templates |
| `GET /api/vendors/subscriptions/plans/` | ✅ | Subscription plans |
| `GET /api/vendors/subscriptions/current/` | ✅ | Current subscription |
| `POST /api/vendors/register/` | ✅ | Vendor registration |
| `GET/POST /api/support/tickets/` | ✅ | Support tickets (vendor-filtered) |
| `GET/POST /api/support/tickets/{id}/messages/` | ✅ | Ticket messages |

---

## Missing APIs for Vendor Dashboard

### 1. Dashboard Stats (Enhanced)

**Vendor dashboard expects:** `/api/dashboard-stats?vendorId=&period=30d&view=daily`

**Current Django:** `GET /api/vendors/dashboard/stats/` returns different shape.

**Missing/Enhancement:**
- `totalProducts`, `totalOrders`, `totalSales`, `pendingOrders`, `followerCount`, `currency`, `monthlyRevenue`
- Period filter: `7d`, `30d`, `90d`, `1y`
- **Action:** Extend `VendorDashboardStatsView` to return this structure and support `period` query param.

---

### 2. Recent Orders

**Vendor dashboard:** `GET /api/recent-orders?vendorId=&limit=5&period=30d`

**Django:** ❌ No equivalent

**Required:** `GET /api/vendors/orders/recent/?limit=5&period=30d`

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "order_number": "ORD-XXX",
      "total": "15000.00",
      "currency": "NGN",
      "status": "pending",
      "created_at": "2026-02-12T10:00:00Z",
      "user_id": "uuid",
      "profiles": { "full_name": "John", "email": "j@example.com" },
      "product_name": "Product A"
    }
  ]
}
```

---

### 3. Vendor Orders (List + Update Status)

**Vendor dashboard:**  
- `GET /api/orders?vendorId=&page=&limit=&status=&dateFrom=&dateTo=&sortBy=&sortOrder=`  
- `PUT /api/orders` (body: orderId, status, vendorId, trackingNumber, notes)

**Django:** ❌ Orders app serves customer orders only.

**Required:**
- `GET /api/vendors/orders/?page=1&limit=20&status=&date_from=&date_to&sort_by=created_at&sort_order=desc`
- `PUT /api/vendors/orders/{id}/status/` — Body: `{ "status", "tracking_number", "notes" }`

**Logic:** Filter orders where `order_items` contain products with `vendor_id` = current vendor. Return vendor-specific subtotal per order. Support status/date filters.

---

### 4. Order Stats

**Vendor dashboard:** `GET /api/orders/stats?vendorId=&dateRange=30d`  
*(Called by ordersService but route may not exist in vendor-dashboard)*

**Required:** `GET /api/vendors/orders/stats/?date_range=30d`  
**Response:** `{ total_orders, total_revenue, by_status: {...} }`

---

### 5. Order Export

**Vendor dashboard:** `GET /api/orders/export?vendorId=&format=csv&status=&dateFrom=&dateTo=`

**Required:** `GET /api/vendors/orders/export/?format=csv&status=&date_from=&date_to=`  
**Response:** CSV file (or JSON)

---

### 6. Vendor Products (Full CRUD)

**Vendor dashboard:**  
- `GET /api/products?vendorId=&page=&limit=&search=&category=&status=&sortBy=&sortOrder=`  
- `GET /api/products/{id}`  
- `POST /api/products` (body: vendorId, productData)  
- `PUT /api/products/{id}` (body: updates)  
- `DELETE /api/products/{id}`

**Django:** Products app is customer-facing. No vendor product management.

**Required:**
- `GET /api/vendors/products/?page=1&limit=20&search=&category=&status=&sort_by=&sort_order=`
- `GET /api/vendors/products/{id}/`
- `POST /api/vendors/products/`
- `PATCH /api/vendors/products/{id}/`
- `DELETE /api/vendors/products/{id}/`

**Body (POST/PATCH):** Match product schema (name, price, description, images, sizes, colors, category_id, etc. – see vendor-dashboard products route.js).

---

### 7. Product Bulk Upload

**Vendor dashboard:** `POST /api/products/bulk-upload`

**Required:** `POST /api/vendors/products/bulk-upload/`  
**Body:** CSV or JSON array of products

---

### 8. Product Size Chart Visibility

**Vendor dashboard:** `PATCH /api/products/{id}/size-chart-visibility` (assumed)

**Required:** `PATCH /api/vendors/products/{id}/size-chart-visibility/`  
**Body:** `{ "size_chart_override": "show"|"hide"|"auto" }`

---

### 9. Product Stock Update

**Vendor dashboard:** productsService.updateStock() — direct Supabase update.

**Required:** `PATCH /api/vendors/products/{id}/stock/`  
**Body:** `{ "stock_quantity": 50 }`  
**Logic:** Update `stock_quantity`, set `in_stock` = quantity > 0.

---

### 10. Vendor Product Reviews (Vendor-Scoped)

**Vendor dashboard:**  
- `GET /api/reviews?vendorId=&productId=&page=&limit=&rating=&status=&hasResponse=`  
- `PUT /api/reviews` (action: respond, hide, show)

**Note:** Not in Mobile spec (that’s customer submit). Vendor needs to list and manage reviews on their products.

**Required:**
- `GET /api/vendors/reviews/?product_id=&page=1&limit=20&rating=&status=&has_response=`
- `PUT /api/vendors/reviews/{id}/` — Body: `{ "action": "respond"|"hide"|"show", "vendor_response" }`

**Response (GET):** `{ reviews, pagination, stats: { total, by_rating, needing_response, average_rating } }`

---

### 11. Vendor Product Q&A (Vendor-Scoped)

**Vendor dashboard:**  
- `GET /api/product-qa?vendorId=&productId=&page=&limit=&status=&hasAnswer=`  
- `PUT /api/product-qa` (action: answer, hide, show)

**Required:**
- `GET /api/vendors/product-qa/?product_id=&page=1&limit=20&status=&has_answer=`
- `PUT /api/vendors/product-qa/{id}/` — Body: `{ "action": "answer"|"hide"|"show", "answer" }`

**Response (GET):** `{ questions, pagination, stats: { total, needing_answer, answer_rate } }`

---

### 12. Payouts (Summary)

**Vendor dashboard:** `GET /api/payouts` returns `availableBalance`, `pendingBalance`, `lifetimeEarnings`, `thisMonthEarnings`, `lastMonthEarnings`, `currency`.

**Django:** Has `VendorPayoutListView` — verify response structure matches.  
**Gap:** Payout summary endpoint (available balance, etc.) may need separate `GET /api/vendors/payouts/summary/` or ensured in list response.

---

### 13. Escrow

**Vendor dashboard:** `GET /api/escrow?status=all|held|released|pending`

**Django:** Has EscrowTransaction model.  
**Required:** `GET /api/vendors/escrow/?status=held|released|pending`

**Response:** List of orders with escrow status, vendor amount, customer info, release date.

---

### 14. Transactions

**Vendor dashboard:** `GET /api/transactions`

**Required:** `GET /api/vendors/transactions/`  
**Response:** Payout/escrow transaction history for vendor.

---

### 15. Analytics

**Vendor dashboard:**  
- `GET /api/analytics/sales?vendorId=&period=30d&view=daily`  
- `GET /api/analytics/metrics?vendorId=`  
- `GET /api/analytics/funnel?vendorId=`  
- `GET /api/analytics/performance?vendorId=`

**Required:**
- `GET /api/vendors/analytics/sales/?period=30d`
- `GET /api/vendors/analytics/metrics/`
- `GET /api/vendors/analytics/funnel/`
- `GET /api/vendors/analytics/performance/`

**Response (sales):** `{ dailySales, statusCounts, totalRevenue, totalOrders, period }`

---

### 16. Sales Trend

**Vendor dashboard:** `GET /api/dashboard-stats/sales-trend?vendorId=&period=`

**Required:** `GET /api/vendors/dashboard/sales-trend/?period=30d`  
**Response:** Time-series data for revenue chart.

---

### 17. Customer Locations

**Vendor dashboard:** `GET /api/vendor-stats/customer-locations?vendorId=`

**Required:** `GET /api/vendors/stats/customer-locations/`  
**Response:** Customer locations/regions for vendor’s orders.

---

### 18. Best Selling Products / Inventory Status

**Vendor dashboard:** vendorService uses:
- `getBestSellingProducts` — `product_performance_summary`
- `getInventoryStatus` — counts by stock level

**Required:**
- `GET /api/vendors/products/best-selling/?limit=5`
- `GET /api/vendors/products/inventory-status/` — `{ totalProducts, inStock, lowStock, outOfStock }`

---

### 19. Vendor Auth

**Vendor dashboard:** Uses `vendor_sessions` + `vendor_session_token` cookie (vendor-login, validate-session, refresh-session, logout).

**Django:** Uses JWT (customer auth).

**Required:** Either:
- **Option A:** Use same JWT auth, add `vendor` role — vendor dashboard calls `POST /api/auth/login/` with vendor credentials, backend returns JWT; vendor endpoints check `request.user` is linked to a Vendor.
- **Option B:** Implement vendor-specific session endpoint compatible with existing cookie flow (e.g. `POST /api/auth/vendor-login/` → set cookie).

---

### 20. Vendor Application & KYC

**Vendor dashboard:**  
- `POST /api/vendor-application`  
- `POST /api/vendor-application/resubmit`  
- `GET/POST /api/vendor-kyc`  
- `POST /api/storage/kyc-upload`

**Django:** Has `VendorRegisterView`. KYC/model may differ.

**Required:**
- Vendor application (create/resubmit) — may be covered by register or need separate endpoint
- KYC upload — `POST /api/vendors/kyc/upload/`  
- Storage for KYC — ensure file upload works (local/S3)

---

### 21. Categories with Subcategories (Product Form)

**Vendor dashboard:** productsService.getCategories() — categories with nested subcategories.

**Mobile spec:** `GET /api/categories/`, `GET /api/categories/{id}/subcategories/`

**Action:** Implement subcategories in Django (see Mobile spec). Vendor dashboard can use same endpoints.

---

### 22. Storage / File Upload

**Vendor dashboard:**  
- `POST /api/storage/upload` — product images  
- `POST /api/storage/kyc-upload` — KYC docs

**Required:**
- `POST /api/vendors/products/{id}/upload-image/` or generic `POST /api/storage/upload/`
- KYC upload — see #20

---

## Summary: New Endpoints to Create

| # | Endpoint | Priority |
|---|----------|----------|
| 1 | Extend `GET /api/vendors/dashboard/stats/` | High |
| 2 | `GET /api/vendors/orders/recent/` | High |
| 3 | `GET /api/vendors/orders/` | High |
| 4 | `PUT /api/vendors/orders/{id}/status/` | High |
| 5 | `GET /api/vendors/orders/stats/` | Medium |
| 6 | `GET /api/vendors/orders/export/` | Medium |
| 7 | `GET/POST/PATCH/DELETE /api/vendors/products/` | High |
| 8 | `GET /api/vendors/products/{id}/` | High |
| 9 | `POST /api/vendors/products/bulk-upload/` | Medium |
| 10 | `PATCH /api/vendors/products/{id}/stock/` | High |
| 11 | `PATCH /api/vendors/products/{id}/size-chart-visibility/` | Low |
| 12 | `GET /api/vendors/reviews/` | High |
| 13 | `PUT /api/vendors/reviews/{id}/` | High |
| 14 | `GET /api/vendors/product-qa/` | High |
| 15 | `PUT /api/vendors/product-qa/{id}/` | High |
| 16 | `GET /api/vendors/payouts/summary/` or enhance existing | Medium |
| 17 | `GET /api/vendors/escrow/` | High |
| 18 | `GET /api/vendors/transactions/` | Medium |
| 19 | `GET /api/vendors/analytics/sales/` | High |
| 20 | `GET /api/vendors/analytics/metrics/` | Medium |
| 21 | `GET /api/vendors/analytics/funnel/` | Medium |
| 22 | `GET /api/vendors/analytics/performance/` | Medium |
| 23 | `GET /api/vendors/dashboard/sales-trend/` | High |
| 24 | `GET /api/vendors/stats/customer-locations/` | Medium |
| 25 | `GET /api/vendors/products/best-selling/` | Medium |
| 26 | `GET /api/vendors/products/inventory-status/` | Medium |
| 27 | Vendor auth (login/session or JWT + vendor check) | High |
| 28 | `POST /api/vendors/kyc/upload/` | High |
| 29 | `POST /api/storage/upload/` or product image upload | High |

**Total new vendor-specific:** ~29 endpoints/features (some are enhancements to existing).

---

## Overlap with Mobile Spec – No Duplication

| Mobile Spec API | Vendor Dashboard | Use Same? |
|-----------------|------------------|-----------|
| `GET /api/categories/` | Categories for product form | ✅ Yes |
| `GET /api/categories/{id}/subcategories/` | Categories for product form | ✅ Yes |
| Product reviews (customer) | Vendor reviews (vendor list/respond) | ❌ Different – vendor needs `/api/vendors/reviews/` |
| Product Q&A (customer) | Vendor Q&A (vendor list/answer) | ❌ Different – vendor needs `/api/vendors/product-qa/` |

Implement Mobile spec for customer-facing APIs. Implement vendor-scoped endpoints above for vendor dashboard. No duplicate work.
