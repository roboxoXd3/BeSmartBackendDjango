#!/usr/bin/env python3
"""
API Performance Test Script
Tests response times and status codes for key BeSmart APIs on production.
"""

import requests
import time
import json
import sys
from datetime import datetime

# ============================================================
# Configuration
# ============================================================
PROD_BASE_URL = "https://api.xbesmart.com"
RAILWAY_BASE_URL = "https://web-production-7cd3c.up.railway.app"
LOCAL_BASE_URL = "http://127.0.0.1:8000"

# Credentials
EMAIL = "sa3198154@gmail.com"
PASSWORD = "avi10102"

# Test settings
TIMEOUT = 20  # seconds per request
RUNS = 2      # number of test runs per endpoint for avg timing


def separator(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def test_endpoint(session, base_url, method, path, label, auth_token=None, data=None, timeout=TIMEOUT):
    """Test a single endpoint and return timing + status info."""
    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    results = []
    for run in range(RUNS):
        start = time.time()
        try:
            if method.upper() == "GET":
                resp = session.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                resp = session.post(url, headers=headers, json=data, timeout=timeout)
            else:
                resp = session.get(url, headers=headers, timeout=timeout)

            elapsed = time.time() - start
            # Truncate body for display
            try:
                body = resp.json()
                body_preview = json.dumps(body, default=str)[:300]
            except Exception:
                body = resp.text[:300]
                body_preview = body

            results.append({
                "status": resp.status_code,
                "time_s": round(elapsed, 3),
                "size_bytes": len(resp.content),
                "body_preview": body_preview,
            })
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            results.append({
                "status": "TIMEOUT",
                "time_s": round(elapsed, 3),
                "size_bytes": 0,
                "body_preview": f"Request timed out after {timeout}s",
            })
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start
            results.append({
                "status": "CONN_ERROR",
                "time_s": round(elapsed, 3),
                "size_bytes": 0,
                "body_preview": str(e)[:200],
            })
        except Exception as e:
            elapsed = time.time() - start
            results.append({
                "status": "ERROR",
                "time_s": round(elapsed, 3),
                "size_bytes": 0,
                "body_preview": str(e)[:200],
            })

    # Compute averages
    times = [r["time_s"] for r in results]
    avg_time = sum(times) / len(times) if times else 0
    statuses = [r["status"] for r in results]

    # Performance classification
    if avg_time < 0.5:
        perf = "🟢 FAST"
    elif avg_time < 2.0:
        perf = "🟡 MODERATE"
    elif avg_time < 5.0:
        perf = "🟠 SLOW"
    else:
        perf = "🔴 VERY SLOW"

    # Check for errors
    has_errors = any(s not in (200, 201, 301, 302) for s in statuses if isinstance(s, int))
    has_conn_errors = any(s in ("TIMEOUT", "CONN_ERROR", "ERROR") for s in statuses)

    print(f"\n  📍 {label}")
    print(f"     {method.upper()} {path}")
    print(f"     Status codes: {statuses}")
    print(f"     Times: {times}")
    print(f"     Avg time: {avg_time:.3f}s  {perf}")
    print(f"     Response size: {results[0]['size_bytes']} bytes")
    if has_errors or has_conn_errors:
        print(f"     ⚠️  Body preview: {results[0]['body_preview']}")

    return {
        "label": label,
        "path": path,
        "method": method,
        "statuses": statuses,
        "times": times,
        "avg_time": round(avg_time, 3),
        "perf": perf,
        "size_bytes": results[0]["size_bytes"],
        "body_preview": results[0]["body_preview"],
        "has_errors": has_errors or has_conn_errors,
    }


def login(session, base_url):
    """Login and return access token."""
    print(f"\n  🔑 Logging in to {base_url}...")
    url = f"{base_url}/api/auth/login/"
    start = time.time()
    try:
        resp = session.post(url, json={"email": EMAIL, "password": PASSWORD}, timeout=TIMEOUT)
        elapsed = time.time() - start
        print(f"     Login status: {resp.status_code} in {elapsed:.3f}s")
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            print(f"     ✅ Login successful, token obtained")
            return token, elapsed
        else:
            print(f"     ❌ Login failed: {resp.text[:300]}")
            return None, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"     ❌ Login error: {e}")
        return None, elapsed


def run_test_suite(base_url, label="PRODUCTION"):
    """Run the complete test suite against a base URL."""
    separator(f"TESTING: {label} ({base_url})")
    print(f"  Started at: {datetime.now().isoformat()}")

    session = requests.Session()
    all_results = []

    # ---- Phase 1: Unauthenticated (Public) endpoints ----
    separator("Phase 1: PUBLIC ENDPOINTS (No Auth Required)")

    public_endpoints = [
        ("GET", "/api/categories/", "Categories List"),
        ("GET", "/api/products/", "Products List (ALL)"),
        ("GET", "/api/products/featured/", "Featured Products"),
        ("GET", "/api/products/new-arrivals/", "New Arrivals"),
        ("GET", "/api/products/on-sale/", "On Sale Products"),
        ("GET", "/api/content/hero-section/", "Hero Section"),
        ("GET", "/api/content/banners/", "Promotional Banners"),
        ("GET", "/api/content/support-info/", "Support Info / FAQs"),
        ("GET", "/api/currency/rates/", "Currency Rates"),
        ("GET", "/api/currency/supported/", "Supported Currencies"),
    ]

    for method, path, label_text in public_endpoints:
        result = test_endpoint(session, base_url, method, path, label_text)
        all_results.append(result)

    # ---- Phase 2: Authentication ----
    separator("Phase 2: AUTHENTICATION")
    token, login_time = login(session, base_url)
    all_results.append({
        "label": "Login",
        "path": "/api/auth/login/",
        "method": "POST",
        "statuses": [200 if token else "FAILED"],
        "times": [round(login_time, 3)],
        "avg_time": round(login_time, 3),
        "perf": "🟢 FAST" if login_time < 0.5 else "🟡 MODERATE" if login_time < 2 else "🔴 SLOW",
        "size_bytes": 0,
        "body_preview": "Token obtained" if token else "Login failed",
        "has_errors": token is None,
    })

    if not token:
        print("\n  ❌ Cannot proceed with authenticated tests without token")
        return all_results

    # ---- Phase 3: Authenticated endpoints ----
    separator("Phase 3: AUTHENTICATED ENDPOINTS")

    auth_endpoints = [
        ("GET", "/api/auth/me/", "Get Current User (me)"),
        ("GET", "/api/users/profile/", "User Profile"),
        ("GET", "/api/currency/user-preference/", "Currency User Preference"),
    ]

    for method, path, label_text in auth_endpoints:
        result = test_endpoint(session, base_url, method, path, label_text, auth_token=token)
        all_results.append(result)

    # ---- Phase 4: Try to get a product ID for detail endpoint tests ----
    separator("Phase 4: PRODUCT DETAIL TESTS")
    print("  Fetching a product ID from products list...")
    try:
        resp = session.get(f"{base_url}/api/products/", headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
        if resp.status_code == 200:
            products = resp.json()
            if isinstance(products, dict) and "results" in products:
                products = products["results"]
            if isinstance(products, list) and len(products) > 0:
                product_id = products[0].get("id")
                print(f"  Found product ID: {product_id}")
                print(f"  Total products returned: {len(products)}")

                detail_endpoints = [
                    ("GET", f"/api/products/{product_id}/", "Product Detail"),
                    ("GET", f"/api/products/{product_id}/delivery-info/", "Product Delivery Info"),
                    ("GET", f"/api/products/{product_id}/warranty-info/", "Product Warranty Info"),
                    ("GET", f"/api/products/{product_id}/offers/", "Product Offers"),
                    ("GET", f"/api/products/{product_id}/highlights/", "Product Highlights"),
                    ("GET", f"/api/products/{product_id}/specifications/", "Product Specifications"),
                    ("GET", f"/api/products/{product_id}/recommendations/", "Product Recommendations"),
                    ("GET", f"/api/products/{product_id}/reviews-summary/", "Product Reviews Summary"),
                    ("GET", f"/api/products/{product_id}/reviews/", "Product Reviews"),
                ]

                for method, path, label_text in detail_endpoints:
                    result = test_endpoint(session, base_url, method, path, label_text)
                    all_results.append(result)
            else:
                print("  ⚠️  No products found in response")
        else:
            print(f"  ⚠️  Products list failed: {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  Error fetching products: {e}")

    # ---- Phase 5: Category detail tests ----
    separator("Phase 5: CATEGORY DETAIL TESTS")
    print("  Fetching a category ID from categories list...")
    try:
        resp = session.get(f"{base_url}/api/categories/", headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
        if resp.status_code == 200:
            categories = resp.json()
            if isinstance(categories, dict) and "results" in categories:
                categories = categories["results"]
            if isinstance(categories, list) and len(categories) > 0:
                cat_id = categories[0].get("id")
                print(f"  Found category ID: {cat_id}")
                print(f"  Total categories returned: {len(categories)}")

                cat_endpoints = [
                    ("GET", f"/api/categories/{cat_id}/", "Category Detail"),
                    ("GET", f"/api/categories/{cat_id}/subcategories/", "Category Subcategories"),
                    ("GET", f"/api/categories/{cat_id}/products/", "Category Products"),
                ]

                for method, path, label_text in cat_endpoints:
                    result = test_endpoint(session, base_url, method, path, label_text)
                    all_results.append(result)
            else:
                print("  ⚠️  No categories found in response")
        else:
            print(f"  ⚠️  Categories list failed: {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  Error fetching categories: {e}")

    return all_results


def print_summary(results, label):
    """Print a summary table of all results."""
    separator(f"SUMMARY: {label}")

    print(f"\n  {'Endpoint':<40} {'Status':<15} {'Avg Time':>10} {'Size':>10}  {'Perf'}")
    print(f"  {'-'*40} {'-'*15} {'-'*10} {'-'*10}  {'-'*15}")

    slow_endpoints = []
    error_endpoints = []

    for r in results:
        status_str = str(r["statuses"][0]) if r["statuses"] else "N/A"
        size_str = f"{r['size_bytes']:,}" if r.get("size_bytes") else "N/A"
        print(f"  {r['label']:<40} {status_str:<15} {r['avg_time']:>8.3f}s {size_str:>10}  {r['perf']}")

        if r["avg_time"] >= 2.0:
            slow_endpoints.append(r)
        if r.get("has_errors"):
            error_endpoints.append(r)

    if slow_endpoints:
        print(f"\n  ⚠️  SLOW ENDPOINTS (>= 2s):")
        for r in slow_endpoints:
            print(f"     - {r['label']}: {r['avg_time']:.3f}s")

    if error_endpoints:
        print(f"\n  ❌ ERROR ENDPOINTS:")
        for r in error_endpoints:
            print(f"     - {r['label']}: {r['statuses']}")
            print(f"       Preview: {r['body_preview'][:200]}")

    # Overall stats
    times = [r["avg_time"] for r in results]
    if times:
        print(f"\n  📊 Overall Stats:")
        print(f"     Total endpoints tested: {len(results)}")
        print(f"     Fastest: {min(times):.3f}s")
        print(f"     Slowest: {max(times):.3f}s")
        print(f"     Average: {sum(times)/len(times):.3f}s")
        print(f"     Median:  {sorted(times)[len(times)//2]:.3f}s")

    return slow_endpoints, error_endpoints


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "prod"

    if mode == "prod":
        results = run_test_suite(PROD_BASE_URL, "PRODUCTION")
        slow, errors = print_summary(results, "PRODUCTION")
    elif mode == "local":
        results = run_test_suite(LOCAL_BASE_URL, "LOCAL")
        slow, errors = print_summary(results, "LOCAL")
    elif mode == "both":
        prod_results = run_test_suite(PROD_BASE_URL, "PRODUCTION")
        slow_prod, errors_prod = print_summary(prod_results, "PRODUCTION")

        local_results = run_test_suite(LOCAL_BASE_URL, "LOCAL")
        slow_local, errors_local = print_summary(local_results, "LOCAL")

        separator("COMPARISON: PRODUCTION vs LOCAL")
        print(f"\n  {'Endpoint':<40} {'Prod (s)':>10} {'Local (s)':>10} {'Diff':>10} {'Slowdown'}")
        print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        for pr in prod_results:
            matching_local = [lr for lr in local_results if lr["label"] == pr["label"]]
            if matching_local:
                lr = matching_local[0]
                diff = pr["avg_time"] - lr["avg_time"]
                if lr["avg_time"] > 0:
                    slowdown = pr["avg_time"] / lr["avg_time"]
                    print(f"  {pr['label']:<40} {pr['avg_time']:>8.3f}s {lr['avg_time']:>8.3f}s {diff:>+8.3f}s {slowdown:>8.1f}x")
                else:
                    print(f"  {pr['label']:<40} {pr['avg_time']:>8.3f}s {lr['avg_time']:>8.3f}s {diff:>+8.3f}s    N/A")
    else:
        print(f"Usage: python {sys.argv[0]} [prod|local|both]")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  Test completed at {datetime.now().isoformat()}")
    print(f"{'='*70}\n")
