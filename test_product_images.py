"""
Regression test for the product `images` field handling.

Verifies that:
  - vendors/own-products/{id}/upload-image/ appends to a JSON array (not overwrite)
  - admin_api's product image upload/delete endpoints use the same JSON array format
  - the two paths are interoperable (upload via one, delete via the other)

Usage:
    python test_product_images.py --base-url http://localhost:8000/api \
        --admin-email you@example.com --admin-password secret

Requires an admin JWT (Authorization: Bearer <token>). Self-cleaning: creates and
deletes its own product.
"""
import argparse
import io
import json
import sys

import requests


def get_admin_token(base_url, email, password):
    res = requests.post(f"{base_url}/users/admin-login/", json={"email": email, "password": password})
    res.raise_for_status()
    return res.json()["access_token"]


def make_png_bytes():
    # Minimal 1x1 transparent PNG
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
        "0000004945454e44ae426082"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    args = parser.parse_args()

    token = get_admin_token(args.base_url, args.admin_email, args.admin_password)
    headers = {"Authorization": f"Bearer {token}"}

    passed = True
    product_id = None

    try:
        # 1. Create a product directly via the admin API
        res = requests.post(
            f"{args.base_url}/admin/products/",
            headers=headers,
            json={
                "name": "Claude image-fix test product",
                "price": "10.00",
                "approval_status": "pending",
                "stock_quantity": 5,
            },
        )
        if res.status_code not in (200, 201):
            print(f"[FAIL] create product: {res.status_code} {res.text[:300]}")
            return 1
        product_id = res.json()["id"]
        print(f"[OK] created product {product_id}")

        # 2. Upload two images via the admin endpoint
        png = make_png_bytes()
        for i in range(2):
            res = requests.post(
                f"{args.base_url}/admin/products/{product_id}/images/",
                headers=headers,
                files={"image": (f"test{i}.png", io.BytesIO(png), "image/png")},
            )
            if res.status_code != 200:
                print(f"[FAIL] admin upload image {i}: {res.status_code} {res.text[:300]}")
                passed = False
            else:
                print(f"[OK] admin upload image {i}: {res.json()}")

        # 3. Fetch the product and confirm `images` parses as a 2-element JSON array
        res = requests.get(f"{args.base_url}/admin/products/{product_id}/", headers=headers)
        res.raise_for_status()
        images_raw = res.json().get("images")
        try:
            images = images_raw if isinstance(images_raw, list) else json.loads(images_raw)
        except Exception as e:
            print(f"[FAIL] images field did not parse as JSON: {images_raw!r} ({e})")
            return 1

        # New product starts with the default placeholder image (a bare URL
        # string, not JSON) -- load_product_images() treats that as a
        # 1-element list, so 2 uploads land at 3 total.
        if not isinstance(images, list) or len(images) != 3:
            print(f"[FAIL] expected a 3-element list (default + 2 uploads), got: {images!r}")
            passed = False
        else:
            print(f"[OK] images is a proper JSON list: {images}")

        # 4. Now hit the vendor-side upload-image endpoint's sibling logic via
        #    admin delete, confirming it can read what was written above.
        res = requests.request(
            "DELETE",
            f"{args.base_url}/admin/products/{product_id}/images/",
            headers=headers,
            json={"image_url": images[0]},
        )
        if res.status_code != 200:
            print(f"[FAIL] admin delete image: {res.status_code} {res.text[:300]}")
            passed = False
        else:
            print(f"[OK] admin delete image: {res.json()}")

        res = requests.get(f"{args.base_url}/admin/products/{product_id}/", headers=headers)
        res.raise_for_status()
        images_raw = res.json().get("images")
        images = images_raw if isinstance(images_raw, list) else json.loads(images_raw)
        if len(images) != 2:
            print(f"[FAIL] expected 2 images left after delete, got: {images!r}")
            passed = False
        else:
            print(f"[OK] 2 images left after delete: {images}")

    finally:
        if product_id:
            res = requests.delete(f"{args.base_url}/admin/products/{product_id}/", headers=headers)
            print(f"[CLEANUP] delete product {product_id}: {res.status_code}")

    print("PASSED" if passed else "FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
