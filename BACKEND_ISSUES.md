# Backend changes needed (BeSmart storefront)

Frontend is already updated. Please do these backend changes.

---

## 1. Filter products by subcategory

**File:** `products/views.py` → `ProductListView`

**Do this:** In `filterset_fields`, add:

```python
'subcategory_id': ['exact'],
```

**We will call:**

```
GET /api/products/?paginate=true&category_id=<uuid>&subcategory_id=<uuid>
```

**Need:** Only products matching that `subcategory_id`.

---

## 2. Fix order price + shipping

**File:** `orders/views.py` (create order)

**Do this:**

1. Use sale price when product is on sale:
   - if `discount_percentage > 0` and `sale_price` exists → use `sale_price`
   - else → use `price`
2. Stop hardcoding `shipping_fee = 0`. Add real shipping (from settings or validated client value).
3. `order.total` must match what the customer sees / what Squad charges.

---

## 3. Fix payment return URL

**File:** `besmart_backend/settings.py`  
(or env `PAYMENT_CALLBACK_URL`)

**Do this:** Change default callback from `/payment/callback` to:

```
{FRONTEND_URL}/verify-payment
```

Example:

```
PAYMENT_CALLBACK_URL=https://your-frontend-domain/verify-payment
```

Squad should redirect with `transaction_ref` in the query string.

---

## 4. Filter products by rating

**File:** `products/views.py` → `ProductListView`

**Do this:** In `filterset_fields`, add:

```python
'rating': ['gte'],
```

**We will call:**

```
GET /api/products/?paginate=true&rating__gte=4
```

**Need:** Only products with rating ≥ that value.

---

## 5. Hide inactive products on detail page

**File:** `products/views.py` → `ProductDetailView`

**Do this:** Only return products with `status='active'` and `approval_status='approved'`.  
Return 404 otherwise (same rules as product list).

---

## 6. HTTPS pagination links

**Do this:** Make sure `next` / `previous` links in paginated responses use `https://` in production (proxy must send `X-Forwarded-Proto`, Django SSL proxy settings correct).

---

## 7. Don’t list unpaid online orders

Online checkout creates an order before Squad payment. If the user cancels payment, that order stays as `pending` / unpaid.

**Frontend already hides these.** Optional backend cleanup:

- Exclude from `GET /api/orders/` when `shipping_method` is online (`credit_card`, etc.) and `payment_status` is not `paid`
- Or auto-cancel unpaid online orders after payment is abandoned

---

## Priority

1 → 2 → 3 → 4 → 5 → 6 → 7 
