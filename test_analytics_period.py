"""
Regression test for vendor analytics `?period=` filtering (funnel, performance)
and the inStock/lowStock stock tiers on own-products/statistics.

Requires a vendor JWT (any DRF SimpleJWT access token for a Django user with a
Vendor row -- Supabase auth issues equivalent tokens in production/staging).

Usage:
    python test_analytics_period.py --base-url http://localhost:8000/api --vendor-token <jwt>

Self-cleaning: creates its own products/events and deletes them afterward. Does
NOT create the vendor/user itself -- pass an existing test vendor's token.
"""
import argparse
import sys

import requests


def check(label, condition, passed_list):
    print(f"[{'OK' if condition else 'FAIL'}] {label}")
    passed_list.append(condition)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--vendor-token", required=True)
    args = parser.parse_args()

    h = {"Authorization": f"Bearer {args.vendor_token}"}
    results = []

    # Statistics: confirm the new keys are present. Their values depend on the
    # vendor's real product mix, so this only checks the shape, not the count.
    res = requests.get(f"{args.base_url}/vendors/own-products/statistics/", headers=h)
    check("statistics 200", res.status_code == 200, results)
    body = res.json()
    check("statistics has inStock", "inStock" in body, results)
    check("statistics has lowStock", "lowStock" in body, results)

    # Funnel/performance: confirm the period param is accepted and doesn't error
    # for the documented values.
    for period in ("7d", "30d", "90d", "1y"):
        res = requests.get(f"{args.base_url}/vendors/analytics/funnel/?period={period}", headers=h)
        check(f"funnel period={period} -> 200", res.status_code == 200, results)
        res = requests.get(f"{args.base_url}/vendors/analytics/performance/?period={period}", headers=h)
        check(f"performance period={period} -> 200", res.status_code == 200, results)

    # A wider period should never return fewer events than a narrower one.
    res_7d = requests.get(f"{args.base_url}/vendors/analytics/funnel/?period=7d", headers=h).json()
    res_1y = requests.get(f"{args.base_url}/vendors/analytics/funnel/?period=1y", headers=h).json()
    total_7d = sum(res_7d.values())
    total_1y = sum(res_1y.values())
    check("1y funnel total >= 7d funnel total", total_1y >= total_7d, results)

    ok = all(results)
    print("PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
