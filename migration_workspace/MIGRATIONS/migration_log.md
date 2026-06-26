# Migration Log

> This file tracks every Supabase → Django migration performed.
> Updated during Phase 3.

---

## Format

```markdown
### MIG-XXX: [API-ID] → [Django Endpoint]
- **Date:** YYYY-MM-DD
- **Agent:** [identifier]
- **Type:** [SUPABASE_SDK | SUPABASE_AUTH | SUPABASE_STORAGE]
- **Frontend(s):** [affected frontends]
- **Supabase Pattern:** [original Supabase call]
- **Django Endpoint:** [new endpoint]
- **Django Files Created/Modified:**
  - `path/to/views.py`
  - `path/to/serializers.py`
  - `path/to/urls.py`
- **Test Status:** [✅ Passing | ❌ Failing | ⏳ Pending]
- **Notes:** [any special considerations]
```

---

## Completed Migrations

### MIG-001: WEB-S-001 → WEB-D-001
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT * FROM products` with filters
- **Django Endpoint:** `GET /api/products/`
- **Django Files Created/Modified:**
  - `products/views.py`
  - `products/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Fixed schema mismatch by adding sizes, base_currency, cod_allowed, and category to serializer. Added ratings alias and updated ordering_fields.

### MIG-002: WEB-S-002 → WEB-D-002
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT * FROM products WHERE id=...`
- **Django Endpoint:** `GET /api/products/{id}/`
- **Django Files Created/Modified:** None (Verified matching)
- **Test Status:** ✅ Passing
- **Notes:** Endpoint was already compatible.

### MIG-003: WEB-S-003 → WEB-D-050
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT * FROM categories`
- **Django Endpoint:** `GET /api/categories/`
- **Django Files Created/Modified:** None (Verified matching)
- **Test Status:** ✅ Passing
- **Notes:** Endpoint was already perfectly compatible.

### MIG-004: WEB-S-004 → WEB-D-007, WEB-D-008
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT/INSERT on reviews`
- **Django Endpoint:** `GET/POST /api/products/{id}/reviews/`
- **Django Files Created/Modified:** None (Verified matching)
- **Test Status:** ✅ Passing
- **Notes:** Endpoint was already completely compatible.

### MIG-005: WEB-S-005 → WEB-D-009, WEB-D-010
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT/INSERT on product_questions`
- **Django Endpoint:** `GET/POST /api/products/{id}/qa/`
- **Django Files Created/Modified:** None (Verified matching)
- **Test Status:** ✅ Passing
- **Notes:** Endpoint was already completely compatible.

### MIG-006: WEB-S-006 → WEB-D-035, WEB-D-036
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK
- **Frontend(s):** ecomWebsite
- **Supabase Pattern:** `SELECT/UPDATE profiles`
- **Django Endpoint:** `GET/PATCH /api/users/profile/`
- **Django Files Created/Modified:** None (Verified matching)
- **Test Status:** ✅ Passing
- **Notes:** Endpoint was perfectly compatible out-of-the-box.

### MIG-007: Fix WEB-D-029, WEB-D-030 (Orders mismatches)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecomWebsite
- **Django Endpoint:** `GET /api/orders/`, `GET /api/orders/{id}/`
- **Django Files Created/Modified:** `orders/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Fixed missing plural fields `order_items` and `products`. Included `shipping_address` and `payment_method` nesting via SerializerMethodField.

### MIG-008: Fix WEB-D-032, WEB-D-033, WEB-D-034 (Loyalty mismatches)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecomWebsite
- **Django Endpoint:** `/api/loyalty/...`
- **Django Files Created/Modified:** `loyalty/views.py`, `loyalty/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Added GET support for ValidateVoucherView, POST stub for LoyaltyPointsView, added `reward_type` alias, and `can_redeem_more` logic for rewards.

### MIG-009: Admin Dashboard Stats (ADM-D-001)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET /api/admin/dashboard/stats/`
- **Django Files Created/Modified:** `admin_api/views.py`
- **Test Status:** ✅ Passing
- **Notes:** Wrapped response in success/data envelope to match frontend expectations. Refactored hardcoded statistics to query from Models, implemented correct serialization format with camelCase fallback.

### MIG-010: Admin Orders List (ADM-D-002)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET /api/admin/orders/`
- **Django Files Created/Modified:** `admin_api/views.py`, `admin_api/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Fixed N+1 performance bottleneck with prefetch_related, added complex OrderAdminSerializer to include detailed customer, vendor, and order item information exactly as Supabase returned it. Fixed error handling for missing relations.

### MIG-011: Admin Products List (ADM-D-003)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET /api/admin/products/`
- **Django Files Created/Modified:** `admin_api/views.py`
- **Test Status:** ✅ Passing
- **Notes:** Implemented proper DjangoFilterBackend logic. Mapped category and vendor UUID queries using custom ProductAdminFilter to avoid TypeError on non-ForeignKey UUID fields.

### MIG-012: Admin Vendors List (ADM-D-007)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET /api/admin/vendors/`
- **Django Files Created/Modified:** `admin_api/views.py`, `admin_api/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Fixed missing `products` reverse-relation lookup by directly querying `Product.objects.filter(vendor_id=obj.id)` inside VendorAdminSerializer methods.

### MIG-013: Admin Currency Rates (ADM-D-008)
- **Date:** 2026-06-20
- **Agent:** Antigravity
- **Type:** DJANGO_API_FIX
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET /api/currency/rates/`
- **Django Files Created/Modified:** `currency/views.py`
- **Test Status:** ✅ Passing
- **Notes:** Adjusted CurrencyRateView to wrap its data in a success/data envelope so the frontend BFF handles it correctly without failing the schema verification.
### MIG-014: Admin Category CRUD (ADM-S-012, ADM-S-013)
- **Date:** 2026-06-22
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK_MIGRATION
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `GET, POST, PATCH, DELETE /api/admin/categories/` and `/api/admin/subcategories/`
- **Django Files Created/Modified:** `admin_api/views.py`, `admin_api/serializers.py`, `admin_api/urls.py`
- **Test Status:** ✅ Passing
- **Notes:** Created missing Django ViewSets for Admin full CRUD access to Categories and Subcategories, replacing the need for Supabase SDK calls on the frontend.

### MIG-015: Admin Loyalty Management (ADM-S-019 to ADM-S-024)
- **Date:** 2026-06-22
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK_MIGRATION
- **Frontend(s):** ecom_admin
- **Django Endpoint:** `POST /api/admin/loyalty/{id}/points/`
- **Django Files Created/Modified:** `admin_api/views.py`, `admin_api/serializers.py`
- **Test Status:** ✅ Passing
- **Notes:** Rewrote the loyalty adjustment endpoint to properly initialize the `LoyaltyPoints` model, handle positive/negative adjustments wrapped in an atomic transaction, and create `LoyaltyTransaction` audit logs.

### MIG-016: Session Management CRUD (Admin & Vendor)
- **Date:** 2026-06-26
- **Agent:** Antigravity
- **Type:** SUPABASE_SDK_MIGRATION
- **Frontend(s):** ecom_admin, vendor-dashboard
- **Django Endpoint:** `GET, POST, PATCH, DELETE /api/admin/sessions/` and `/api/vendors/sessions/`
- **Django Files Created/Modified:**
  - `admin_api/views.py`
  - `admin_api/serializers.py`
  - `admin_api/urls.py`
  - `vendors/views.py`
  - `vendors/serializers.py`
  - `vendors/urls.py`
- **Test Status:** ✅ Passing
- **Notes:** Replaced direct Supabase SDK calls to `admin_sessions` and `vendor_sessions` tables with fully functional Django viewsets. Endpoints are internally used by the Next.js BFF layers to manage login states before full Django auth context is established, thus they have `AllowAny` permissions.
