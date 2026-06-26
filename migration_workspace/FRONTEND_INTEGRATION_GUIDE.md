# Frontend Integration Guide for Admin APIs

This document outlines the required frontend integration changes for migrating away from the Supabase SDK to our new Django Admin API endpoints. **No business logic has been changed**; only the routing and HTTP methods for these operations.

## General Information
- Ensure all calls that previously used `supabase.from('...')` for these operations are updated to make standard REST HTTP requests (e.g., using `fetch` or `axios`) to the new endpoints.
- Base URL for Admin APIs is `/api/admin/`.
- Authentication to these endpoints requires the same mechanism as other Django endpoints (usually a JWT Bearer token).

---

## 1. Category Management (`ADM-S-012`, `ADM-S-013`)

### Previously (Supabase SDK)
The frontend fetched, created, updated, and deleted categories directly using `supabase.from('categories')`.

### New Django Endpoints
Replace the SDK calls with the following REST API endpoints:
- **List Categories:** `GET /api/admin/categories/`
- **Create Category:** `POST /api/admin/categories/` (Body: JSON with category data)
- **Get Single Category:** `GET /api/admin/categories/{id}/`
- **Update Category:** `PATCH /api/admin/categories/{id}/` (Body: JSON with updated fields)
- **Delete Category:** `DELETE /api/admin/categories/{id}/`

*Note: For subcategories, use the parallel endpoints at `/api/admin/subcategories/`.*

---

## 2. Loyalty Management (`ADM-S-019` to `ADM-S-024`)

### Previously (Supabase SDK)
The frontend managed user loyalty points manually via Supabase using operations on `loyalty_points` or `lib/loyalty-service.js`.

### New Django Endpoints
Replace manual points adjustments with the dedicated endpoint:
- **Add / Deduct Points:** `POST /api/admin/loyalty/{user_id}/points/`
  - **Payload:** 
    ```json
    {
      "points": 50,  // Positive to add, negative to deduct
      "description": "Admin manual adjustment"
    }
    ```
  - **Response:**
    ```json
    {
      "message": "50 points applied.",
      "points_balance": 150,
      "user": "<user_uuid>"
    }
    ```
The backend automatically handles creating the `LoyaltyTransaction` audit log and updating the total balance on the `LoyaltyPoints` model safely using a database transaction.

---

## 3. Session Management (Admin & Vendor)

### Previously (Supabase SDK)
The Next.js backend-for-frontend (BFF) layers for Admin and Vendor panels previously interacted directly with `admin_sessions` and `vendor_sessions` tables using the Supabase SDK for creating, validating, and deleting session tokens.

### New Django Endpoints
The logic remains unchanged. However, the direct SDK calls must be swapped for standard REST API requests to these internal endpoints. **Note: These endpoints have `AllowAny` permissions because they are used to validate sessions before Django's auth context is fully established.**

#### Admin Sessions
- **List Sessions:** `GET /api/admin/sessions/`
- **Get Session:** `GET /api/admin/sessions/{session_token}/`
- **Create Session:** `POST /api/admin/sessions/`
  ```json
  {
    "admin": "<admin_user_uuid>",
    "session_token": "<token>",
    "refresh_token": "<token>",
    "expires_at": "<timestamp>"
  }
  ```
- **Update Session:** `PATCH /api/admin/sessions/{session_token}/`
- **Delete Session:** `DELETE /api/admin/sessions/{session_token}/`

#### Vendor Sessions
- **List Sessions:** `GET /api/vendors/sessions/`
- **Get Session:** `GET /api/vendors/sessions/{session_token}/`
- **Create Session:** `POST /api/vendors/sessions/`
  ```json
  {
    "vendor_id": "<vendor_uuid>",
    "user_id": "<user_uuid>",
    "session_token": "<token>",
    "expires_at": "<timestamp>"
  }
  ```
- **Update Session:** `PATCH /api/vendors/sessions/{session_token}/`
- **Delete Session:** `DELETE /api/vendors/sessions/{session_token}/`
