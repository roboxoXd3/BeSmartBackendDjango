# Backend Action Items — ecomWebsite Integration

**Date:** 2026-07-04
**Scope:** ecomWebsite (Next.js) against BeSmartBackendDjango
**Author:** Audit performed via Claude Code

This doc only lists things that need action on the **backend** side. Every
frontend-only bug found during this audit (product pagination, the online
payment flow bypassing Django, the currency selector, cart/checkout showing
unconverted prices) was fixed directly in the frontend and isn't listed here
— nothing to do on your end for those.

---

## 1. Pagination `next`/`previous` links are `http://`, not `https://`

```
GET https://api.xbesmart.com/api/products/featured/?paginate=true
→ "next": "http://api.xbesmart.com/api/products/featured/?cursor=...&paginate=true"
```

The site is served over HTTPS, so browsers block the follow-up fetch as
mixed content (surfaces as `TypeError: Failed to fetch` on "Load More").

**Cause:** Django is behind a reverse proxy that terminates TLS, but Django
isn't told the original request was HTTPS, so `request.build_absolute_uri()`
(used by DRF pagination) defaults to `http://`.

**Fix needed:**
```python
# settings.py
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```
Confirm your proxy/load balancer actually forwards `X-Forwarded-Proto: https`
first, then point Django at whatever header it uses.

*(A frontend workaround is in place in the meantime — this isn't urgent, but
should still be fixed properly at some point.)*

---

## 2. No saved-card / recurring-charge endpoint

`app/subscriptions/page.js` (saved payment methods / recurring payments)
currently has to call Squad directly and store tokens in a Supabase table,
because Django's `payments` app has no equivalent endpoint —
`payments/urls.py` only has `methods/`, `initiate/`, `verify/<ref>/`, and
`webhook/`. There is no `tokenize` or `charge-token` view, and the `Payment`
model doesn't carry a `token` field.

**Fix needed:** Add `POST /api/payments/tokenize/` and
`POST /api/payments/charge-token/` (or fold token storage into the existing
`PaymentMethod` model), backed by Django's own `Payment`/`PaymentMethod`
tables. Once that exists, let us know and we'll switch the frontend over to
it instead of talking to Squad/Supabase directly.

---

## 3. Please confirm Squad's dashboard callback/redirect URL

Django's `InitiatePaymentView` doesn't pass an explicit `callback_url` to
Squad. The frontend now creates the order and calls Django's real
`/api/payments/initiate/` (rather than the old direct-to-Squad flow), so the
redirect after payment relies entirely on whatever default redirect URL is
configured in Squad's dashboard.

**Action needed:** Confirm Squad's dashboard-level default redirect is set to
your production `/verify-payment` route.

---

## 4. Order total isn't currency-aware (only matters if products use non-NGN base currencies)

Django computes `order.total` by summing raw `product.price` values with no
currency conversion, and `InitiatePaymentView` sends that total to Squad
labeled with whatever `currency` is passed (frontend currently always sends
`"NGN"`). `Product` has a per-product `base_currency` field — if a cart ever
mixes products priced in genuinely different base currencies, the resulting
order total isn't a well-defined amount in any single currency.

**Action needed (only if this applies to your catalog):** either enforce one
base currency store-wide, or make order total calculation currency-aware.
Not urgent if every product is actually priced in NGN today.

---

## 5. Promotional banner data: test rows left active in production

`GET /api/content/banners/` returns several `is_active: true` rows still
literally titled **"Test Banner"**, with every real content field
(`description`, `subtitle`, `discount_value`, `coupon_code`,
`background_image_url`, colors) and every `show_*` visibility flag set to
`null`. The frontend correctly renders nothing for a banner with no content
configured, which is why the homepage popup shows up blank/white.

**Action needed (content/admin, not code):** deactivate these test banner
rows, or fill in a real banner (title, description, colors, and explicitly
set the `show_*` flags to true) via whatever admin tool manages
`content.banners`.
