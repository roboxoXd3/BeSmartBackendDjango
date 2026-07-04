#!/usr/bin/env python3
"""
Quick local API test — hits the most critical endpoints that are timing out on production.
Compares with prod timings to isolate whether it's Railway vs code.
"""

import requests
import time
import json
from datetime import datetime

LOCAL_BASE_URL = "http://127.0.0.1:8888"
EMAIL = "sa3198154@gmail.com"
PASSWORD = "avi10102"
TIMEOUT = 60  # longer timeout for local to let it complete

def test(label, method, path, auth_token=None, data=None):
    url = f"{LOCAL_BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        else:
            resp = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
        elapsed = time.time() - start
        
        try:
            body = resp.json()
            if isinstance(body, list):
                count = len(body)
            elif isinstance(body, dict) and "results" in body:
                count = len(body["results"])
            else:
                count = "N/A"
        except:
            count = "N/A"
            body = resp.text[:200]

        # Perf rating
        if elapsed < 0.5: perf = "🟢 FAST"
        elif elapsed < 2.0: perf = "🟡 MODERATE"  
        elif elapsed < 5.0: perf = "🟠 SLOW"
        else: perf = "🔴 VERY SLOW"

        print(f"  {perf}  {elapsed:>8.3f}s  {resp.status_code}  {len(resp.content):>8,} B  items={count:<6}  {label}")
        return resp.status_code, elapsed, resp
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"  🔴 TIMEOUT  {elapsed:>8.3f}s  ---  {label}")
        return "TIMEOUT", elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ❌ ERROR  {elapsed:>8.3f}s  {str(e)[:80]}  {label}")
        return "ERROR", elapsed, None

print(f"\n{'='*80}")
print(f"  LOCAL API PERFORMANCE TEST (Port 8888, same prod database)")
print(f"  Started: {datetime.now().isoformat()}")
print(f"{'='*80}")

print(f"\n  {'Rating':<15} {'Time':>10} {'Status':>6} {'Size':>12} {'Items':>12}  {'Endpoint'}")
print(f"  {'-'*15} {'-'*10} {'-'*6} {'-'*12} {'-'*12}  {'-'*30}")

# ── Public endpoints ──
test("Categories List", "GET", "/api/categories/")
test("Products List (ALL)", "GET", "/api/products/")
test("Featured Products", "GET", "/api/products/featured/")
test("New Arrivals", "GET", "/api/products/new-arrivals/")
test("On Sale Products", "GET", "/api/products/on-sale/")
test("Content: Hero Section", "GET", "/api/content/hero-section/")
test("Content: Banners", "GET", "/api/content/banners/")
test("Content: Support Info", "GET", "/api/content/support-info/")
test("Currency: Rates", "GET", "/api/currency/rates/")
test("Currency: Supported", "GET", "/api/currency/supported/")

# ── Login ──
print(f"\n  --- AUTHENTICATION ---")
status, login_time, login_resp = test("Login", "POST", "/api/auth/login/", data={"email": EMAIL, "password": PASSWORD})
token = None
if login_resp and login_resp.status_code == 200:
    token = login_resp.json().get("access_token")

if token:
    print(f"\n  --- AUTHENTICATED ENDPOINTS ---")
    test("Get Me", "GET", "/api/auth/me/", auth_token=token)
    test("User Profile", "GET", "/api/users/profile/", auth_token=token)
    test("Currency Preference", "GET", "/api/currency/user-preference/", auth_token=token)

# ── Get a product ID for detail tests ──
print(f"\n  --- PRODUCT DETAIL TESTS ---")
try:
    resp = requests.get(f"{LOCAL_BASE_URL}/api/products/featured/", 
                       headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
    if resp.status_code == 200:
        products = resp.json()
        if isinstance(products, dict) and "results" in products:
            products = products["results"]
        if isinstance(products, list) and len(products) > 0:
            pid = products[0]["id"]
            print(f"  Using product: {pid}")
            test("Product Detail", "GET", f"/api/products/{pid}/")
            test("Product Delivery Info", "GET", f"/api/products/{pid}/delivery-info/")
            test("Product Offers", "GET", f"/api/products/{pid}/offers/")
            test("Product Highlights", "GET", f"/api/products/{pid}/highlights/")
            test("Product Specs", "GET", f"/api/products/{pid}/specifications/")
            test("Product Recommendations", "GET", f"/api/products/{pid}/recommendations/")
            test("Product Reviews Summary", "GET", f"/api/products/{pid}/reviews-summary/")
            test("Product Reviews", "GET", f"/api/products/{pid}/reviews/")
except Exception as e:
    print(f"  Could not test product details: {e}")

# ── Category detail tests ──
print(f"\n  --- CATEGORY DETAIL TESTS ---")
try:
    resp = requests.get(f"{LOCAL_BASE_URL}/api/categories/", 
                       headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
    if resp.status_code == 200:
        cats = resp.json()
        if isinstance(cats, list) and len(cats) > 0:
            cid = cats[0]["id"]
            print(f"  Using category: {cid}")
            test("Category Detail", "GET", f"/api/categories/{cid}/")
            test("Category Subcategories", "GET", f"/api/categories/{cid}/subcategories/")
            test("Category Products", "GET", f"/api/categories/{cid}/products/")
except Exception as e:
    print(f"  Could not test category details: {e}")

print(f"\n{'='*80}")
print(f"  Finished: {datetime.now().isoformat()}")
print(f"{'='*80}\n")
