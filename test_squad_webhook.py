import hmac
import hashlib
import json
import requests
import argparse
import sys

def test_webhook(url, secret_str):
    secret = secret_str.encode('utf-8')

    payload_dict = {
        "Event": "charge_successful",
        "TransactionRef": "TEST-12345678",
        "Body": {
            "amount": 50000,
            "transaction_ref": "TEST-12345678",
            "status": "success",
            "customer_email": "test@example.com",
            "is_test": True
        }
    }

    # Squad uses raw JSON bytes
    payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
    
    # Calculate signature
    signature = hmac.new(secret, payload_bytes, hashlib.sha512).hexdigest().upper()

    headers = {
        "Content-Type": "application/json",
        "x-squad-encrypted-body": signature
    }

    print(f"Sending webhook to {url}")
    try:
        response = requests.post(url, data=payload_bytes, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def _send(url, secret_str, payload_dict):
    secret = secret_str.encode('utf-8')
    payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(secret, payload_bytes, hashlib.sha512).hexdigest().upper()
    headers = {"Content-Type": "application/json", "x-squad-encrypted-body": signature}
    return requests.post(url, data=payload_bytes, headers=headers)


def test_transfer_webhook(url, secret_str, transaction_ref):
    """transfer_successful for a real squad_transaction_ref should settle the payout."""
    payload = {
        "Event": "transfer_successful",
        "Body": {"transaction_reference": transaction_ref, "amount": "1000"},
    }
    res = _send(url, secret_str, payload)
    print(f"[transfer_successful] Status: {res.status_code} Body: {res.text[:200]}")
    return res


def test_transfer_webhook_replay(url, secret_str, transaction_ref):
    """A second transfer_successful for the same ref must be a no-op, not an error."""
    return test_transfer_webhook(url, secret_str, transaction_ref)


def test_transfer_webhook_missing_ref(url, secret_str):
    """Regression for the IntegrityError-on-null-ref bug: must return 200, not 500."""
    payload = {"Event": "transfer_successful", "Body": {}}
    res = _send(url, secret_str, payload)
    print(f"[missing ref] Status: {res.status_code} Body: {res.text[:200]}")
    ok = res.status_code == 200
    print("[OK] missing ref returns 200" if ok else "[FAIL] missing ref did not return 200")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Squad Webhook Endpoint")
    parser.add_argument("--env", choices=["local", "staging", "prod"], default="local", help="Environment to test")
    parser.add_argument("--secret", required=True, help="The SQUAD_WEBHOOK_HASH for the target environment")
    parser.add_argument("--transfer-ref", help="An existing VendorPayout.squad_transaction_ref to exercise the transfer_successful/replay flow")
    parser.add_argument("--skip-charge", action="store_true", help="Skip the original charge_successful smoke test")

    args = parser.parse_args()

    urls = {
        "local": "http://localhost:8000/api/payments/webhook/",
        "staging": "https://besmartbackenddjango-staging.up.railway.app/api/payments/webhook/",
        "prod": "https://api.xbesmart.com/api/payments/webhook/"
    }

    target_url = urls[args.env]

    if not args.skip_charge:
        test_webhook(target_url, args.secret)

    passed = test_transfer_webhook_missing_ref(target_url, args.secret)

    if args.transfer_ref:
        test_transfer_webhook(target_url, args.secret, args.transfer_ref)
        test_transfer_webhook_replay(target_url, args.secret, args.transfer_ref)

    sys.exit(0 if passed else 1)
