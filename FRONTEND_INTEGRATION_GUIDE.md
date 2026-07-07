# Frontend Integration Guide: Vendor Analytics & Payment Tokenization

This guide provides instructions for the frontend team (or their AI agents) to integrate the newly added backend capabilities for **Vendor Analytics** and **Squad Payment Tokenization**.

---

## 1. Vendor Analytics Tracking & Dashboard

We have added robust, backend-driven analytics to track product impressions and conversions.

### 1.1 Tracking Product Events (New Endpoint)
You need to call this endpoint whenever a user interacts with a product on the platform.

**Endpoint:** `POST /api/vendors/analytics/track/`
**Auth:** None required (`AllowAny`)

**Payload:**
```json
{
  "product_id": "uuid-of-the-product",
  "event_type": "view" // Can be "view", "cart", or "purchase"
}
```
**Integration Instructions:**
- **Views:** Fire this event when a user navigates to the Product Detail Page. You may want to debounce this to prevent spamming.
- **Cart:** Fire this event when a user adds the product to their cart.
- **Purchase:** Fire this event when a checkout completes successfully.

### 1.2 Fetching Vendor Funnel Metrics
This endpoint aggregates overall vendor analytics across all their products.

**Endpoint:** `GET /api/vendors/analytics/funnel/`
**Auth:** Required (Vendor specific)

**Response Format:**
```json
{
  "views": 1500,
  "cart": 300,
  "checkout": 150,
  "purchases": 50
}
```
**Integration Instructions:**
- Use this on the Vendor Dashboard to show conversion funnels or top-level metrics.

### 1.3 Fetching Per-Product Performance
This returns analytics and conversion rates broken down by each of the vendor's products, sorted by most views.

**Endpoint:** `GET /api/vendors/analytics/performance/`
**Auth:** Required (Vendor specific)

**Response Format:**
```json
{
  "data": [
    {
      "product_id": "uuid...",
      "name": "Product Name",
      "views": 100,
      "cart": 20,
      "purchases": 5,
      "conversion_rate": 5.0,
      "price": 25000.0
    }
  ]
}
```
**Integration Instructions:**
- Use this to populate a "Top Performing Products" table on the Vendor Dashboard.

---

## 2. Squad Payment Tokenization

We have updated the payment flow to fully support card tokenization, enabling one-click or recurring checkout flows for future purchases.

### 2.1 Initial Payment (Token Generation)
When you call the existing `POST /api/payments/initiate/` endpoint, the backend now automatically passes `is_recurring: true` to the Squad API.

**Integration Instructions:**
- The frontend **does not** need to change anything regarding the `initiate` endpoint.
- Once the user completes the payment on the Squad checkout page, Squad sends a webhook to our backend.
- **Backend Behavior:** The backend webhook listener validates the signature, fulfills the order, and automatically extracts `payment_information.token_id`. The token is saved to the user's account (`PaymentMethod` model).

### 2.2 Retrieving Saved Cards
Use the existing endpoint to list saved payment methods for the authenticated user.

**Endpoint:** `GET /api/payments/methods/`
**Auth:** Required

**Response Details:**
- The list will now contain payment methods where `provider` is `squad` and `payment_type` is `card`.

### 2.3 Charging a Saved Card (New Endpoint)
When a user selects a saved card during checkout instead of entering a new one, use this endpoint.

**Endpoint:** `POST /api/payments/charge-token/`
**Auth:** Required

**Payload:**
```json
{
  "order_id": "uuid-of-the-order",
  "payment_method_id": "uuid-of-the-saved-payment-method"
}
```
**Response Format:**
- **Success (200):**
```json
{
  "status": "success",
  "message": "Charge successful"
}
```
- **Error (400 or 502):**
```json
{
  "error": "Charge failed",
  "details": { ... }
}
```
**Integration Instructions:**
- On the checkout page, present the user's saved cards.
- If they select one, submit the order to `charge-token` instead of `initiate`.
- Handle potential errors (e.g., token expired, insufficient funds) by prompting the user to use a different card or initiate a new standard payment.
