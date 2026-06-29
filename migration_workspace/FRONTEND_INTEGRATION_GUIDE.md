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

---

## 4. User and Admin Creation & Updates

### Previously (Supabase SDK)
User creation involved using `supabase.auth.admin.createUser` to create the auth identity, followed by direct database inserts/updates to the `users` table via `supabase.from('users')`.

### New Django Endpoints
Replace the Supabase Admin Auth calls and database inserts with the following dedicated endpoints. The backend will automatically handle hashing the password and securely storing the user data.

- **Create User (Admin context):** `POST /api/admin/users/`
  - **Payload:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePassword123!",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true
    }
    ```
- **Update User (Admin context):** `PATCH /api/admin/users/{user_id}/`
  - **Payload:** JSON containing updated user fields.

---

## 5. Storage / Image Uploads (Admin Context)

### Previously (Supabase SDK)
The frontend uploaded files directly to Supabase Storage using `supabase.storage.from('bucket').upload(...)` and then manually updated the database column using `supabase.from('table').update({ image: ... })`.

### New Django Endpoints
Send the image via `multipart/form-data` to the backend. The backend handles securely storing the file (e.g. to R2) and automatically updating the relevant database entity.

#### Product Image Uploads
- **Upload Image:** `POST /api/admin/products/{product_id}/images/`
  - **Payload:** `multipart/form-data` containing the file in the `image` field.
  - **Response:**
    ```json
    {
      "status": "Image uploaded successfully",
      "image_url": "https://..."
    }
    ```
- **Delete Image:** `DELETE /api/admin/products/{product_id}/images/`
  - **Payload:**
    ```json
    {
      "image_url": "https://..."
    }
    ```

#### Banner Image Uploads
- **Upload Image:** `POST /api/admin/content/banners/{banner_id}/images/`
  - **Payload:** `multipart/form-data` containing the file in the `image` field.
  - **Response:**
    ```json
    {
      "status": "Image uploaded successfully",
      "image_url": "https://..."
    }
    ```
- **Delete Image:** `DELETE /api/admin/content/banners/{banner_id}/images/`
  - **Payload:**
    ```json
    {
      "image_url": "https://..."
    }
    ```

---

## 6. Authentication (Native Django JWT)

### Previously (Supabase SDK)
The frontend used `supabase.auth.signInWithPassword`, `signUp`, and `signOut` which returned a Supabase session containing an `access_token` and `refresh_token` wrapped in a `session` object.

### New Django Endpoints
The authentication endpoints have been rewritten to use native Django and SimpleJWT, completely removing the Supabase proxy layer. The URLs remain exactly the same to minimize disruption, but the JSON response format has been flattened.

#### Login & Registration
- **Login:** `POST /api/users/login/`
- **Register:** `POST /api/users/register/`
- **Vendor Login:** `POST /api/users/vendor-login/`
- **Admin Login:** `POST /api/users/admin-login/`

**New Response Format:**
```json
{
  "message": "Login successful.",
  "user": {
    "id": "<user_uuid>",
    "email": "user@example.com"
  },
  "access_token": "eyJhbGciOiJIUz...",
  "refresh_token": "eyJhbGciOiJIUz..."
}
```
*(Notice that `access_token` and `refresh_token` are now at the root level instead of inside a `session` object).*

#### Token Refresh
- **Refresh Token:** `POST /api/users/token/refresh/`
  - **Payload:** `{"refresh": "<refresh_token>"}`
  - **Response:**
    ```json
    {
      "access": "eyJhbGciOiJIUz...",
      "refresh": "eyJhbGciOiJIUz..."
    }
    ```
*(Note: SimpleJWT uses the keys `access` and `refresh` for the token refresh response).*

## 7. Bulk Upload (Vendor Context)

### Previously (Supabase SDK)
The vendor dashboard uploaded CSVs and processed product creations directly on the frontend using Supabase SDK calls to insert multiple rows into the `products` table.

### New Django Endpoints
Replace the manual loop of inserts with a single backend endpoint that handles batch creation and partial updates.

- **Bulk Upload:** `POST /api/vendors/own-products/bulk-upload/`
  - **Payload:** JSON containing a list of products under the `products` key.
    ```json
    {
      "products": [
        {
          "name": "Product 1",
          "description": "Desc 1",
          "price": 100.0,
          "stock_quantity": 10,
          "category_id": "<category_uuid>",
          "brand": "Brand X"
        },
        {
          "id": "<existing_product_uuid>",
          "stock_quantity": 50
        }
      ]
    }
    ```
  - **Response:**
    ```json
    {
      "message": "Bulk upload processed",
      "created": 1,
      "updated": 1
    }
    ```
*(Note: Omitting the `id` field will create a new product, providing an `id` will update the existing product.)*

