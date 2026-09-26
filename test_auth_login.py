"""
Regression tests for the Supabase-proxy (BFF) auth endpoints:
  - POST /auth/login/          valid creds -> Supabase session; bad creds -> 401; bad body -> 400
  - GET  /auth/me/             works with the returned access_token
  - POST /auth/token/refresh/  rotates the session; garbage -> 401; missing -> 400
  - POST /auth/vendor-login/   200 for vendors, 403 for everyone else
  - POST /auth/admin-login/    200 for admins, 403 for everyone else

Nothing is created or modified: login only mirrors an already-existing Supabase
user into Django (a no-op for existing users), so there is nothing to clean up.

Usage:
    python test_auth_login.py --base-url http://localhost:8000/api \
        --email you@example.com --password secret
"""
import argparse
import sys
import uuid

import requests


def check(label, condition, passed_list, detail=""):
    print(f"[{'OK' if condition else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not condition else ""))
    passed_list.append(condition)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    creds = {"email": args.email, "password": args.password}
    passed = []

    # --- login ---
    res = requests.post(f"{base}/auth/login/", json=creds, timeout=30)
    body = res.json()
    check("login with valid credentials -> 200", res.status_code == 200, passed, f"{res.status_code} {body}")
    if res.status_code != 200:
        sys.exit(1)
    for key in ("access_token", "refresh_token", "token_type", "expires_in", "expires_at"):
        check(f"login response has {key}", body.get(key) not in (None, ""), passed)
    check("login response user email matches", body.get("user", {}).get("email", "").lower() == args.email.lower(), passed, str(body.get("user")))
    access, refresh = body["access_token"], body["refresh_token"]

    res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {access}"}, timeout=30)
    check("GET /auth/me/ with login access_token -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
    check("/auth/me/ returns the logged-in user", res.ok and res.json().get("email", "").lower() == args.email.lower(), passed)

    res = requests.post(f"{base}/auth/login/", json={**creds, "password": creds["password"] + "-wrong"}, timeout=30)
    check("login with wrong password -> 401", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

    res = requests.post(f"{base}/auth/login/", json={"email": f"nobody-{uuid.uuid4().hex[:8]}@example.com", "password": "x" * 10}, timeout=30)
    check("login with unknown email -> 401", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

    res = requests.post(f"{base}/auth/login/", json={"email": args.email}, timeout=30)
    check("login without password -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

    # A stale/foreign bearer token must not break login (login ignores Authorization).
    res = requests.post(f"{base}/auth/login/", json=creds, headers={"Authorization": "Bearer garbage"}, timeout=30)
    check("login with a stale Authorization header -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")

    # --- refresh ---
    res = requests.post(f"{base}/auth/token/refresh/", json={"refresh_token": refresh}, timeout=30)
    check("token refresh -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
    if res.ok:
        new = res.json()
        check("refresh returns a new refresh_token", new.get("refresh_token") and new["refresh_token"] != refresh, passed)
        check("refresh returns legacy access/refresh aliases", new.get("access") == new.get("access_token") and new.get("refresh") == new.get("refresh_token"), passed)
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {new['access_token']}"}, timeout=30)
        check("GET /auth/me/ with refreshed access_token -> 200", res.status_code == 200, passed, f"{res.status_code}")

        res = requests.post(f"{base}/auth/token/refresh/", json={"refresh": new["refresh_token"]}, timeout=30)
        check("token refresh via legacy `refresh` field -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")

    res = requests.post(f"{base}/auth/token/refresh/", json={"refresh_token": "not-a-real-token"}, timeout=30)
    check("token refresh with garbage token -> 401", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

    for payload in ({}, {"refresh_token": ""}):
        res = requests.post(f"{base}/auth/token/refresh/", json=payload, timeout=30)
        check(f"token refresh with {payload} -> 400 {{error}}", res.status_code == 400 and "error" in res.json(), passed, f"{res.status_code} {res.text[:200]}")

    # --- role-specific logins: 200 when the account has the role, 403 otherwise ---
    for path, role_key in (("vendor-login", "vendor_id"), ("admin-login", "is_staff")):
        res = requests.post(f"{base}/auth/{path}/", json=creds, timeout=30)
        ok = (res.status_code == 200 and res.json().get("access_token") and role_key in res.json().get("user", {})) \
            or (res.status_code == 403 and "error" in res.json())
        check(f"{path} -> 200 with tokens or 403 (got {res.status_code})", ok, passed, res.text[:200])

        res = requests.post(f"{base}/auth/{path}/", json={**creds, "password": creds["password"] + "-wrong"}, timeout=30)
        check(f"{path} with wrong password -> 401", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

    print(f"\n{sum(passed)}/{len(passed)} checks passed")
    sys.exit(0 if all(passed) else 1)


if __name__ == "__main__":
    main()
