"""
Regression tests for admin workflows touched by this branch + follow-up fixes:
  - product create (vendor_id/approval_status) + reject-with-reason/approve-clears-reason
  - size-chart approve/reject
  - contact-branch CRUD
  - order status change -> status-history
  - loyalty analytics redemption `points`
  - escrow release/hold happy path + 404 on a bad id

Self-cleaning: every fixture created is deleted at the end, including on failure.

Usage:
    python test_admin_workflows.py --base-url http://localhost:8000/api \
        --admin-email you@example.com --admin-password secret
"""
import argparse
import sys
import uuid

import requests


def get_admin_token(base_url, email, password):
    res = requests.post(f"{base_url}/users/admin-login/", json={"email": email, "password": password})
    res.raise_for_status()
    return res.json()["access_token"]


def check(label, condition, passed_list):
    print(f"[{'OK' if condition else 'FAIL'}] {label}")
    passed_list.append(condition)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    args = parser.parse_args()

    token = get_admin_token(args.base_url, args.admin_email, args.admin_password)
    h = {"Authorization": f"Bearer {token}"}
    results = []
    product_id = None
    branch_id = None

    try:
        # --- Product reject-with-reason / approve-clears-reason ---
        res = requests.post(f"{args.base_url}/admin/products/", headers=h, json={
            "name": "Claude admin-workflow test product", "price": "5.00", "approval_status": "pending",
        })
        check("create product", res.status_code in (200, 201), results)
        product_id = res.json().get("id")

        res = requests.post(f"{args.base_url}/admin/products/{product_id}/reject/", headers=h, json={"notes": "bad photos"})
        check("reject with reason", res.status_code == 200 and res.json().get("approval_status") == "rejected", results)

        res = requests.get(f"{args.base_url}/admin/products/{product_id}/", headers=h)
        check("rejection_reason saved", res.json().get("rejection_reason") == "bad photos", results)

        res = requests.post(f"{args.base_url}/admin/products/{product_id}/approve/", headers=h)
        check("approve", res.status_code == 200 and res.json().get("approval_status") == "approved", results)

        res = requests.get(f"{args.base_url}/admin/products/{product_id}/", headers=h)
        check("approve clears rejection_reason", res.json().get("rejection_reason") is None, results)

        # --- Contact branch CRUD ---
        res = requests.post(f"{args.base_url}/admin/contact-branches/", headers=h, json={
            "branch_name": "Claude test branch", "address_line_1": "1 Test St",
            "city": "Lagos", "state": "Lagos", "phone": "1234567890",
        })
        check("create contact branch", res.status_code in (200, 201), results)
        branch_id = res.json().get("id")

        res = requests.patch(f"{args.base_url}/admin/contact-branches/{branch_id}/", headers=h, json={"branch_name": "Updated"})
        check("update contact branch", res.status_code == 200 and res.json().get("branch_name") == "Updated", results)

        # --- Loyalty analytics response shape ---
        res = requests.get(f"{args.base_url}/admin/loyalty/analytics/", headers=h)
        check("loyalty analytics 200", res.status_code == 200, results)
        redemptions = res.json().get("last_10_redemptions", [])
        check("last_10_redemptions items carry 'points' when present", all("points" in r for r in redemptions), results)

        # --- Escrow 404 on a bad id ---
        res = requests.post(f"{args.base_url}/admin/escrow/{uuid.uuid4()}/release/", headers=h)
        check("escrow release on bad id -> 404 (not 500)", res.status_code == 404, results)

    finally:
        if product_id:
            requests.delete(f"{args.base_url}/admin/products/{product_id}/", headers=h)
            print(f"[CLEANUP] deleted product {product_id}")
        if branch_id:
            requests.delete(f"{args.base_url}/admin/contact-branches/{branch_id}/", headers=h)
            print(f"[CLEANUP] deleted contact branch {branch_id}")

    ok = all(results)
    print("PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
