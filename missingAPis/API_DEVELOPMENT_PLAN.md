# API Development Plan

> **Total estimate:** ~26–27 hours  
> **Reference:** CONSOLIDATED_API_MASTER.md  

**Approach:** Build in order of dependency. Each session = 2–3 hours. Update Postman after each batch.

---

## Session Overview

| Phase | Session | Focus | Hours | Endpoints |
|-------|---------|-------|-------|-----------|
| 0 | Setup | Models, Postman base, permissions | 1.5 | — |
| 1 | S1–S2 | Customer: Shipping, Orders, Cart/Wishlist extras | 3 | 12 |
| 2 | S3–S4 | Customer: Vendors, Content, Categories | 3 | 15 |
| 3 | S5–S6 | Customer: Reviews, Q&A, Loyalty, Account, Search | 3 | 18 |
| 4 | S7–S8 | Vendor: Orders, Products, Reviews/Q&A | 3.5 | 16 |
| 5 | S9–S10 | Vendor: Analytics, Payouts, Auth, Storage | 3 | 13 |
| 6 | S11–S13 | Admin: Auth, Dashboard, Users, Vendors | 4 | 20 |
| 7 | S14–S16 | Admin: Products, Orders, Loyalty, Content | 4 | 25 |
| 8 | S17–S18 | Admin: Analytics, Contact, Misc + Polish | 2 | 15 |
| — | Buffer | Fixes, testing, Postman sync | 2 | — |

**Total:** 27 hours

---

## Phase 0: Setup (1.5 hrs)

### Models to add (DB tables exist; Django models may not)

| Model | App | Table | Notes |
|-------|-----|-------|-------|
| ShippingAddress | orders | shipping_addresses | Required for checkout |
| Subcategory | categories | subcategories | FK to Category |
| ProductSpecification | products | product_specifications | FK to Product |
| ProductOffer | products | product_offers | FK to Product |
| ProductHighlight | products | product_highlights | FK to Product |
| HeroSection | content | hero_section | Single row |
| ContactInfo | content | contact_info | Main contact (if separate from branches) |
| SearchAnalytics | products or new `search` app | search_analytics | Log searches |
| UserBadge | loyalty | user_badges | If not exists |

### Postman

- Create collection: `BeSmart API`
- Add base var: `{{base_url}}` = `http://localhost:8000`
- Add auth: `{{token}}` for JWT
- Folders: Customer, Vendor, Admin

---

## Phase 1: Customer – Shipping, Orders, Cart (3 hrs)

### Session S1 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 1 | `GET /api/shipping-addresses/` | 10m | ShippingAddress |
| 2 | `POST /api/shipping-addresses/` | 10m | |
| 3 | `PATCH /api/shipping-addresses/{id}/` | 5m | |
| 4 | `DELETE /api/shipping-addresses/{id}/` | 5m | |
| 5 | `POST /api/shipping-addresses/{id}/set-default/` | 10m | |

**Postman:** Add 5 requests to Customer folder.

### Session S2 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 6 | `POST /api/orders/` | 45m | Cart, ShippingAddress, OrderService |
| 7 | `POST /api/orders/{id}/cancel/` | 15m | |
| 8 | `GET /api/orders/{id}/track/` | 15m | |
| 9 | `POST /api/orders/{id}/reorder/` | 15m | |
| 10 | `GET /api/orders/{id}/invoice/` | 15m | |
| 11 | `POST /api/cart/clear/` | 5m | |
| 12 | `GET /api/cart/summary/` | 10m | |
| 13 | `POST /api/wishlist/{id}/move-to-cart/` | 15m | |
| 14 | `DELETE /api/wishlist/clear/` | 5m | |

---

## Phase 2: Customer – Vendors, Content, Categories (3 hrs)

### Session S3 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 15 | `GET /api/vendors/` | 15m | Vendor |
| 16 | `GET /api/vendors/featured/` | 5m | |
| 17 | `GET /api/vendors/search/?q=` | 10m | |
| 18 | `GET /api/vendors/{id}/` | 5m | |
| 19 | `GET /api/vendors/{id}/products/` | 15m | |
| 20 | `GET /api/vendors/{id}/reviews/` | 15m | VendorReview |
| 21 | `POST /api/vendors/{id}/reviews/` | 15m | |
| 22 | `PATCH /api/vendors/reviews/{id}/` | 10m | |
| 23 | `DELETE /api/vendors/reviews/{id}/` | 5m | |
| 24 | `POST /api/vendors/{id}/follow/` | 15m | New model: VendorFollow |
| 25 | `DELETE /api/vendors/{id}/follow/` | 5m | |

### Session S4 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 26 | `GET /api/categories/{id}/subcategories/` | 15m | Subcategory |
| 27 | `GET /api/categories/{id}/products/` | 10m | |
| 28 | `GET /api/content/hero-section/` | 15m | HeroSection |
| 29 | `GET /api/content/contact-info/` | 10m | ContactInfo or ContactBranch |
| 30 | `GET /api/content/support-info/?type=` | 10m | SupportInfo filter |

---

## Phase 3: Customer – Reviews, Q&A, Loyalty, Account (3 hrs)

### Session S5 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 31 | `GET /api/products/{id}/reviews/` | 20m | ProductReview model (if needed) |
| 32 | `POST /api/products/{id}/reviews/` | 15m | |
| 33 | `POST /api/reviews/{id}/helpful/` | 10m | |
| 34 | `POST /api/reviews/{id}/report/` | 10m | |
| 35 | `GET /api/products/{id}/qa/` | 20m | ProductQuestion model |
| 36 | `POST /api/products/{id}/qa/` | 15m | |
| 37 | `POST /api/products/{id}/qa/{qa_id}/helpful/` | 10m | |
| 38 | `GET /api/products/{id}/specifications/` | 15m | ProductSpecification |
| 39 | `GET /api/products/{id}/offers/` | 10m | ProductOffer |
| 40 | `GET /api/products/{id}/highlights/` | 10m | ProductHighlight |

### Session S6 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 41 | `POST /api/loyalty/validate-voucher/` | 20m | LoyaltyVoucher |
| 42 | `GET /api/loyalty/user-badges/` | 15m | UserBadge |
| 43 | `GET /api/loyalty/badge-progress/` | 20m | UserBadge, LoyaltyBadge |
| 44 | `GET /api/loyalty/tier-info/` | 15m | |
| 45 | `GET /api/users/account/deletion-eligibility/` | 15m | |
| 46 | `POST /api/users/account/delete/` | 25m | Cascade/soft delete |
| 47 | `POST /api/search/analytics/` | 10m | SearchAnalytics |
| 48 | `GET /api/search/analytics/` | 10m | |
| 49 | `GET /api/products/{id}/size-chart/` | 15m | VendorSizeChartTemplate |
| 50 | `POST /api/products/{id}/view/` | 5m | |

---

## Phase 4: Vendor – Orders, Products, Reviews (3.5 hrs)

### Session S7 (2 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 51 | `GET /api/vendors/orders/recent/` | 20m | |
| 52 | `GET /api/vendors/orders/` | 25m | Filter by vendor products |
| 53 | `PUT /api/vendors/orders/{id}/status/` | 20m | |
| 54 | `GET /api/vendors/orders/stats/` | 15m | |
| 55 | `GET /api/vendors/orders/export/` | 20m | CSV |
| 56 | `GET /api/vendors/products/` | 20m | |
| 57 | `POST /api/vendors/products/` | 25m | |
| 58 | `GET /api/vendors/products/{id}/` | 5m | |

### Session S8 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 59 | `PATCH /api/vendors/products/{id}/` | 15m | |
| 60 | `DELETE /api/vendors/products/{id}/` | 5m | |
| 61 | `POST /api/vendors/products/bulk-upload/` | 25m | |
| 62 | `PATCH /api/vendors/products/{id}/stock/` | 10m | |
| 63 | `PATCH /api/vendors/products/{id}/size-chart-visibility/` | 10m | |
| 64 | `GET /api/vendors/reviews/` | 20m | Product reviews for vendor |
| 65 | `PUT /api/vendors/reviews/{id}/` | 15m | Respond/hide/show |
| 66 | `GET /api/vendors/product-qa/` | 15m | |
| 67 | `PUT /api/vendors/product-qa/{id}/` | 15m | |

---

## Phase 5: Vendor – Analytics, Payouts, Auth (3 hrs)

### Session S9 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 68 | `GET /api/vendors/payouts/summary/` | 15m | |
| 69 | `GET /api/vendors/escrow/` | 20m | EscrowTransaction |
| 70 | `GET /api/vendors/transactions/` | 15m | |
| 71 | `GET /api/vendors/analytics/sales/` | 25m | |
| 72 | `GET /api/vendors/analytics/metrics/` | 20m | |
| 73 | `GET /api/vendors/analytics/funnel/` | 20m | |
| 74 | `GET /api/vendors/analytics/performance/` | 15m | |

### Session S10 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 75 | `GET /api/vendors/dashboard/sales-trend/` | 20m | |
| 76 | `GET /api/vendors/stats/customer-locations/` | 20m | |
| 77 | `GET /api/vendors/products/best-selling/` | 15m | |
| 78 | `GET /api/vendors/products/inventory-status/` | 10m | |
| 79 | Vendor auth (JWT + vendor check) | 30m | Extend auth |
| 80 | `POST /api/vendors/kyc/upload/` | 25m | File upload |
| 81 | `POST /api/storage/upload/` or product image | 20m | |

---

## Phase 6: Admin – Auth, Dashboard, Users, Vendors (4 hrs)

### Session S11 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 82 | Admin login | 30m | AdminSession, AdminUser |
| 83 | Admin validate-session | 15m | |
| 84 | Admin refresh-session | 10m | |
| 85 | Admin logout | 5m | |
| 86 | Admin reset-password | 20m | |

### Session S12 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 87 | `GET /api/admin/dashboard/stats/` (enhanced) | 20m | |
| 88 | `GET /api/admin/dashboard/recent-orders/` | 15m | |
| 89 | `GET /api/admin/dashboard/revenue-chart/` | 20m | |
| 90 | `GET /api/admin/dashboard/top-vendors/` | 15m | |
| 91 | `GET /api/admin/dashboard/recent-activity/` | 15m | |
| 92 | `GET /api/admin/dashboard/export/` | 15m | |
| 93 | Customer users: list | 25m | |
| 94 | Customer users: create | 15m | |

### Session S13 (1 hr)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 95 | Customer users: get, update, delete | 15m | |
| 96 | Customer users: status, role, export | 20m | |
| 97 | `GET /api/admin/vendors/` | 15m | |
| 98 | `GET /api/admin/vendors/{id}/` | 5m | |
| 99 | Vendors: status, verification | 20m | |
| 100 | Vendors: stats, export | 15m | |

---

## Phase 7: Admin – Products, Orders, Loyalty, Content (4 hrs)

### Session S14 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 101 | `GET /api/admin/products/` | 15m | |
| 102 | `GET /api/admin/products/pending/` | 10m | |
| 103 | `GET /api/admin/products/{id}/` | 5m | |
| 104 | Products: approve, reject | 20m | |
| 105 | `GET /api/admin/orders/` | 20m | |
| 106 | `GET /api/admin/orders/{id}/` | 5m | |
| 107 | Orders: update status | 15m | |
| 108 | Orders: cancel | 10m | |
| 109 | Orders: create | 15m | |

### Session S15 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 110 | Orders: stats, bulk, export | 30m | |
| 111 | Payouts, escrow, bank (admin) | 30m | |
| 112 | Categories admin CRUD | 25m | |
| 113 | Subcategories admin CRUD | 20m | |
| 114 | Categories: upload-image, delete-image | 15m | |

### Session S16 (1 hr)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 115 | Contact + branches admin CRUD | 25m | |
| 116 | Hero section admin get/update/upload | 20m | |
| 117 | Promotional banners path + upload | 15m | |
| 118 | Size charts: list, approve, reject | 20m | |
| 119 | Admin profile + image upload | 15m | |
| 120 | Support: admin sees all tickets | 10m | Permission |
| 121 | Loyalty admin: rewards CRUD | 20m | |
| 122 | Loyalty admin: badges CRUD | 15m | |
| 123 | Loyalty admin: earning rules | 15m | |
| 124 | Loyalty admin: user adjustments | 15m | |

---

## Phase 8: Admin – Analytics, Polish (2 hrs)

### Session S17 (1.5 hrs)

| # | Endpoint | Est | Deps |
|---|----------|-----|------|
| 125 | Analytics: dashboard | 20m | |
| 126 | Analytics: revenue | 15m | |
| 127 | Analytics: users, products, conversion, vendors | 30m | |
| 128 | Analytics: export | 15m | |
| 129 | Payment: charge-token (if missing) | 20m | |
| 130 | Payment: initiate-from-cart (if needed) | 25m | |

### Session S18 (0.5 hr)

| # | Task | Est |
|---|------|-----|
| — | Postman: full collection review | 15m |
| — | Fix any broken endpoints | 15m |

---

## Postman Maintenance

After each session:

1. Add new requests to the correct folder (Customer/Vendor/Admin).
2. Set method, URL, headers (`Authorization: Bearer {{token}}` where needed).
3. Add sample bodies for POST/PATCH.
4. Optional: add tests (e.g. `pm.test("Status 200", () => pm.response.to.have.status(200));`).

---

## Checklist Summary

- [ ] Phase 0: Models + Postman base
- [ ] Phase 1: Shipping, Orders, Cart extras (14 endpoints)
- [ ] Phase 2: Vendors, Content, Categories (16 endpoints)
- [ ] Phase 3: Reviews, Q&A, Loyalty, Account (20 endpoints)
- [ ] Phase 4: Vendor Orders, Products, Reviews (17 endpoints)
- [ ] Phase 5: Vendor Analytics, Payouts, Auth (14 endpoints)
- [ ] Phase 6: Admin Auth, Dashboard, Users, Vendors (19 endpoints)
- [ ] Phase 7: Admin Products, Orders, Loyalty, Content (24 endpoints)
- [ ] Phase 8: Admin Analytics, Payment extras, Polish (6+ endpoints)

---

## Quick Start

When ready to begin:

1. Start with Phase 0 (models + Postman).
2. Then Phase 1, Session S1 (shipping addresses).
3. After each endpoint: add to Postman, run once, move on.
