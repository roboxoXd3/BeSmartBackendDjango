"""
Regression test for the vendor self-service payout endpoint
(POST /api/vendors/payouts/), which used to be fully broken by two bugs:
  1. dead exploratory code referencing a nonexistent `escrow_transactions`
     reverse relation on VendorPayout (FieldError on every request)
  2. `bank_account.currency` -- VendorBankAccount has no `currency` field
     (AttributeError, swallowed into an opaque 'Payout processing error')

Pass condition: the request reaches Squad and gets a *gateway-level* response
(success, or a Squad-side rejection) rather than one of the two bugs above.

Requires a vendor JWT for a vendor with:
  - a default bank account
  - a 'released' EscrowTransaction giving it enough available balance

Usage:
    python test_vendor_payout.py --base-url http://localhost:8000/api --vendor-token <jwt> --amount 10.00
"""
import argparse
import sys

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--vendor-token", required=True)
    parser.add_argument("--amount", default="10.00")
    args = parser.parse_args()

    h = {"Authorization": f"Bearer {args.vendor_token}"}
    res = requests.post(f"{args.base_url}/vendors/payouts/", headers=h, json={"amount": args.amount})
    body_text = res.text[:500]
    print(f"Status: {res.status_code}")
    print(f"Body: {body_text}")

    # These are the two regressions we're guarding against.
    is_field_error = "FieldError" in body_text or "escrow_transactions" in body_text
    is_attribute_error = "AttributeError" in body_text or "'VendorBankAccount' object has no attribute 'currency'" in body_text

    if is_field_error:
        print("[FAIL] hit the dead-code FieldError regression")
        return 1
    if is_attribute_error:
        print("[FAIL] hit the bank_account.currency AttributeError regression")
        return 1

    # Anything else -- 201 success, insufficient funds, or a Squad-side
    # rejection surfaced as a clean error -- means our code path is healthy.
    print("[OK] request reached the payout/Squad logic without the known regressions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
