# Backend Changes Needed — Vendor Dashboard

**Date:** 2026-07-24  
**For:** BeSmartBackendDjango  
**Frontend status:** Ready to go live. Items below improve correctness; they are **not blockers** for shipping the vendor panel.

---

## Go-live impact (if frontend ships before these fixes)

| # | Backend item | Breaks live vendor panel? | What vendors see today |
|---|--------------|---------------------------|------------------------|
| 1 | `upload_image` string overwrite | **No** | Product create/edit uses `upload-color-image` (works). Legacy `upload-image` BFF also repairs the array after upload. |
| 2 | Funnel / performance `period` filter | **No** | Analytics still shows real data; period dropdown does not change funnel/performance (always all-time). Sales / views-over-time / metrics period filters already work. |
| 3 | Inventory `inStock` / `lowStock` on statistics | **No** | Inventory widget works via a product-page scan (slower only for very large catalogs). |

**Bottom line:** You can put the frontend live now. Nothing in this doc will hard-break login, products, orders, payouts, settings, support, or media upload.

---

## 1. Fix `upload_image` — keep `images` as a JSON array

**Impact:** Medium (source-of-truth bug; frontend mitigates)  
**File:** `vendors/views.py` → `VendorOwnProductViewSet.upload_image`

**Bug:** `product.images = file_url` saves a string. Field must stay a list of URLs.

**Fix:**

```python
images = product.images or []
if isinstance(images, str):
    images = [images] if images else []
if file_url not in images:
    images.append(file_url)
product.images = images
product.save(update_fields=['images'])
return Response({"message": "Image uploaded", "images": images})
```

---

## 2. Honour `?period=` on funnel + performance

**Impact:** Low–Medium (UX accuracy only)  
**Endpoints:**

- `GET /api/vendors/analytics/funnel/`
- `GET /api/vendors/analytics/performance/`

**Expected:** Same `period=7d|30d|90d|1y` behaviour as sales / views-over-time. Filter `ProductAnalyticsEvent` by `created_at`.

Frontend already forwards `period`; Django currently ignores it.

---

## 3. Optional — inventory stock tiers on statistics

**Impact:** Low (performance nicety)  
**Endpoint:** `GET /api/vendors/own-products/statistics/`

Add `inStock` (qty > 10) and `lowStock` (qty 1–10) so the dashboard can skip scanning product pages.

---

## Already handled — do not re-open

Customer name on orders · ProductListSerializer fields · list filters / page_size · resubmit · KYC `document_type` · funnel/performance endpoints exist · metrics / best-sellers / inventory on Django via frontend · support polling · promotions “coming soon” · Supabase auth by design.
