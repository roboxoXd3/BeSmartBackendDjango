# Frontend Integration Updates - July 7, 2026

This document details the latest backend changes requested during the frontend handoff review.

## 1. Loyalty Admin CRUD & Analytics
The backend now fully supports the Loyalty Program admin section with dedicated CRUD endpoints and analytics.

**New Endpoints:**
- `GET/POST /api/admin/loyalty/badges/`
- `GET/POST /api/admin/loyalty/rewards/`
- `GET/POST /api/admin/loyalty/rules/`
- `GET /api/admin/loyalty/analytics/`
  - Returns aggregate data: `{"total_points_issued": X, "total_points_redeemed": Y, "total_active_users": Z}`
- `GET /api/admin/loyalty/users/`
  - Returns a paginated list of users and their current loyalty points balance.

## 2. Squad `callback_url` Pass-through
The `InitiatePaymentView` now accepts a `callback_url` directly from the frontend.
- **Endpoint:** `POST /api/payments/initiate/`
- **Payload update:** You can now optionally pass `"callback_url": "https://..."` in the JSON body. This URL will override the default Squad dashboard redirect URL for that specific transaction.

## 3. Payments Tokenize Endpoint Clarification
During the handoff review, it was requested to add a standalone `/api/payments/tokenize/` endpoint. 

**Note for Frontend Developers:**
Cards are already tokenized automatically when a user successfully completes a payment, because the backend explicitly passes `is_recurring=True` to Squad during `POST /api/payments/initiate/`. As a result, no standalone `/tokenize/` endpoint has been added. If a separate tokenization flow is absolutely required in the future (e.g., zero-auth tokenization), this will need to be re-evaluated alongside Squad's zero-auth capabilities.

## 4. Vendor Logo JSON Key Correction
The JSON output keys for the vendor's logo have been corrected to literally match `business_logo` in the Admin APIs.

- **Admin Payouts** (`GET /api/admin/payouts/`): `vendor_logo` has been renamed to `business_logo`.
- **Admin Orders** (`GET /api/admin/orders/`): Inside the `vendors` array, `logo_url` has been renamed to `business_logo`.
