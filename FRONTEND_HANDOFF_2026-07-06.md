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
