"""
Regression tests for the Supabase-proxy account endpoints:
  - POST   /auth/register/                 sign-up via Supabase (email confirmation required)
  - POST   /admin/users/                   admin creates a Supabase login + Django user
  - PATCH  /admin/users/{id}/              admin sets password / email in Supabase
  - POST   /auth/password/change/          change password (current_password required for normal sessions)
  - POST   /auth/password/reset/           Supabase reset email, same answer for unknown emails
  - POST   /auth/logout/                   revokes the Supabase session
  - POST   /auth/account/delete/           verifies password in Supabase, bans + frees the email
  - PATCH  /admin/users/{id}/status/       suspended users can't log in, refresh or use their token
  - DELETE /admin/users/{id}/              removes both the Django user and the Supabase login

Throwaway users are plus-addresses of the admin email (e.g. you+bstest1a2b@gmail.com),
so the confirmation / reset emails land in your own inbox. Every user created is
deleted again through DELETE /admin/users/{id}/, also when a check fails.

Steps that send email can hit Supabase's email rate limit; those report SKIP on 429.

Usage:
    python test_auth_account.py --base-url http://localhost:8000/api \
        --admin-email you@example.com --admin-password secret
"""
import argparse
import sys
import uuid

import requests

TIMEOUT = 30


def check(label, condition, passed_list, detail=""):
    print(f"[{'OK' if condition else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not condition else ""))
    passed_list.append(bool(condition))


def skip(label, res):
    print(f"[SKIP] {label}  (Supabase rate limit: {res.status_code} {res.text[:120]})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    passed = []
    created_ids = []

    local, domain = args.admin_email.split("@")
    run = uuid.uuid4().hex[:6]

    def throwaway(tag):
        return f"{local}+bstest{run}{tag}@{domain}".lower()

    def post(path, json=None, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return requests.post(f"{base}{path}", json=json, headers=headers, timeout=TIMEOUT)

    def login(email, password):
        return post("/auth/login/", {"email": email, "password": password})

    res = post("/auth/admin-login/", {"email": args.admin_email, "password": args.admin_password})
    check("admin login -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
    if res.status_code != 200:
        sys.exit(1)
    admin_token = res.json()["access_token"]
    admin = {"Authorization": f"Bearer {admin_token}"}

    try:
        # --- register ---
        reg_email = throwaway("r")
        res = post("/auth/register/", {"email": reg_email, "password": "Str0ng-pass!", "full_name": "BS Test", "phone_number": "+2348000000000"})
        if res.status_code == 429:
            skip("register", res)
        else:
            body = res.json()
            check("register -> 201", res.status_code == 201, passed, f"{res.status_code} {res.text[:200]}")
            if res.status_code == 201:
                created_ids.append(body["user"]["id"])
                check("register reports email confirmation required", body.get("email_confirmation_required") is True and body.get("access_token") is None, passed, str(body))

                res = login(reg_email, "Str0ng-pass!")
                check("login before email confirmation -> 401", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

        res = post("/auth/register/", {"email": throwaway("w"), "password": "1"})
        check("register with weak password -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")
        if res.status_code == 201:
            created_ids.append(res.json()["user"]["id"])

        res = post("/auth/register/", {"email": "not-an-email", "password": "Str0ng-pass!"})
        check("register with invalid email -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        # --- admin create / update ---
        user_email = throwaway("c")
        res = requests.post(f"{base}/admin/users/", headers=admin, timeout=TIMEOUT, json={
            "email": user_email, "password": "Pass-one-111", "first_name": "BS", "last_name": "Test",
            "phone_number": "+2348000000001", "role": "customer",
        })
        check("admin create user -> 201", res.status_code == 201, passed, f"{res.status_code} {res.text[:200]}")
        if res.status_code != 201:
            return passed
        user_id = res.json()["id"]
        created_ids.append(user_id)

        res = requests.post(f"{base}/admin/users/", headers=admin, timeout=TIMEOUT, json={"email": user_email, "password": "Pass-one-111"})
        check("admin create duplicate email -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        res = post("/auth/register/", {"email": user_email, "password": "Str0ng-pass!"})
        check("register an already-registered email -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        res = requests.post(f"{base}/admin/users/", headers=admin, timeout=TIMEOUT, json={"first_name": "No email"})
        check("admin create without email -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        res = login(user_email, "Pass-one-111")
        check("admin-created user can log in", res.status_code == 200 and res.json()["user"]["id"] == user_id, passed, f"{res.status_code} {res.text[:200]}")
        user_token = res.json().get("access_token")
        res = requests.post(f"{base}/admin/users/", headers={"Authorization": f"Bearer {user_token}"}, timeout=TIMEOUT, json={"email": throwaway("x"), "password": "Pass-one-111"})
        check("non-admin create user -> 403", res.status_code == 403, passed, f"{res.status_code} {res.text[:200]}")

        res = requests.patch(f"{base}/admin/users/{user_id}/", headers=admin, timeout=TIMEOUT, json={"password": "Pass-two-222"})
        check("admin set password -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        check("old password rejected after admin change", login(user_email, "Pass-one-111").status_code == 401, passed)
        check("new password works after admin change", login(user_email, "Pass-two-222").status_code == 200, passed)

        new_email = throwaway("e")
        res = requests.patch(f"{base}/admin/users/{user_id}/", headers=admin, timeout=TIMEOUT, json={"email": new_email})
        check("admin change email -> 200", res.status_code == 200 and res.json().get("email") == new_email, passed, f"{res.status_code} {res.text[:200]}")
        res = login(new_email, "Pass-two-222")
        check("login with the new email works", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        user_email = new_email
        token = res.json().get("access_token")

        # --- password change ---
        other_session = login(user_email, "Pass-two-222").json()
        res = post("/auth/password/change/", {"password": "Pass-three-333"}, token)
        check("password change without current_password (normal session) -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/password/change/", {"password": "Pass-three-333", "current_password": "wrong-one"}, token)
        check("password change with wrong current_password -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/password/change/", {"password": "Pass-two-222", "current_password": "Pass-two-222"}, token)
        check("password change to the same password -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/password/change/", {"password": "Pass-three-333", "current_password": "Pass-two-222"}, token)
        check("password change -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
        check("session that changed the password stays valid", res.status_code == 200, passed, f"{res.status_code}")
        res = post("/auth/token/refresh/", {"refresh_token": other_session["refresh_token"]})
        check("other sessions are signed out after password change", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")
        check("old password rejected after change", login(user_email, "Pass-two-222").status_code == 401, passed)
        res = login(user_email, "Pass-three-333")
        check("new password works after change", res.status_code == 200, passed, f"{res.status_code}")
        res = post("/auth/password/change/", {"password": "Pass-four-444"})
        check("password change without token -> 401/403", res.status_code in (401, 403), passed, f"{res.status_code}")

        # --- suspend / activate ---
        session = login(user_email, "Pass-three-333").json()
        res = requests.patch(f"{base}/admin/users/{user_id}/status/", headers=admin, timeout=TIMEOUT, json={"action": "suspend"})
        check("admin suspend -> 200", res.status_code == 200 and res.json().get("is_active") is False, passed, f"{res.status_code} {res.text[:200]}")
        res = login(user_email, "Pass-three-333")
        check("suspended user login -> 403", res.status_code == 403, passed, f"{res.status_code} {res.text[:200]}")
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {session['access_token']}"}, timeout=TIMEOUT)
        check("suspended user's token rejected", res.status_code in (401, 403), passed, f"{res.status_code}")
        res = post("/auth/token/refresh/", {"refresh_token": session["refresh_token"]})
        check("suspended user refresh -> 403", res.status_code == 403, passed, f"{res.status_code} {res.text[:200]}")
        res = requests.patch(f"{base}/admin/users/{user_id}/status/", headers=admin, timeout=TIMEOUT, json={"action": "activate"})
        check("admin activate -> 200", res.status_code == 200 and res.json().get("is_active") is True, passed, f"{res.status_code} {res.text[:200]}")
        check("re-activated user can log in", login(user_email, "Pass-three-333").status_code == 200, passed)

        # --- logout ---
        keep = login(user_email, "Pass-three-333").json()
        other = login(user_email, "Pass-three-333").json()
        res = post("/auth/logout/", {"scope": "others"}, keep["access_token"])
        check("logout scope=others -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {keep['access_token']}"}, timeout=TIMEOUT)
        check("scope=others keeps the current session", res.status_code == 200, passed, f"{res.status_code}")
        res = post("/auth/token/refresh/", {"refresh_token": other["refresh_token"]})
        check("scope=others signs out the other session", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")

        session = login(user_email, "Pass-three-333").json()
        res = post("/auth/logout/", {}, session["access_token"])
        check("logout -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {session['access_token']}"}, timeout=TIMEOUT)
        check("access token rejected after logout", res.status_code in (401, 403), passed, f"{res.status_code}")
        res = post("/auth/token/refresh/", {"refresh_token": session["refresh_token"]})
        check("refresh token rejected after logout", res.status_code == 401, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/logout/", {}, session["access_token"])
        check("logout again (already revoked) -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/logout/", {})
        check("logout without token -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        # --- password reset ---
        res = post("/auth/password/reset/", {"email": user_email})
        if res.status_code == 429:
            skip("password reset for existing user", res)
        else:
            check("password reset for existing user -> 200", res.status_code == 200, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/password/reset/", {"email": f"nobody-{run}@example.com"})
        check("password reset for unknown email -> same 200", res.status_code == 200 or res.status_code == 429, passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/password/reset/", {"email": "not-an-email"})
        check("password reset with invalid email -> 400", res.status_code == 400, passed, f"{res.status_code} {res.text[:200]}")

        # --- account delete ---
        token = login(user_email, "Pass-three-333").json()["access_token"]
        res = post("/auth/account/delete/", {"password": "wrong-one"}, token)
        check("account delete with wrong password -> 400", res.status_code == 400 and res.json().get("error") == "invalid_password", passed, f"{res.status_code} {res.text[:200]}")
        res = post("/auth/account/delete/", {"password": "Pass-three-333"}, token)
        check("account delete -> 200", res.status_code == 200 and res.json().get("success") is True, passed, f"{res.status_code} {res.text[:200]}")
        res = login(user_email, "Pass-three-333")
        check("deleted account can't log in", res.status_code in (401, 403), passed, f"{res.status_code} {res.text[:200]}")
        res = requests.get(f"{base}/auth/me/", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
        check("deleted account's token rejected", res.status_code in (401, 403), passed, f"{res.status_code}")

        res = post("/auth/register/", {"email": user_email, "password": "Str0ng-pass!"})
        if res.status_code == 429:
            skip("re-register a deleted account's email", res)
        else:
            check("deleted account's email can register again -> 201", res.status_code == 201, passed, f"{res.status_code} {res.text[:200]}")
            if res.status_code == 201:
                created_ids.append(res.json()["user"]["id"])
    finally:
        # --- cleanup: removes the Django user and the Supabase login ---
        for uid in created_ids:
            res = requests.delete(f"{base}/admin/users/{uid}/", headers=admin, timeout=TIMEOUT)
            check(f"cleanup: admin delete user {uid} -> 204", res.status_code == 204, passed, f"{res.status_code} {res.text[:200]}")
            res = requests.get(f"{base}/admin/users/{uid}/", headers=admin, timeout=TIMEOUT)
            check(f"cleanup: user {uid} gone -> 404", res.status_code == 404, passed, f"{res.status_code}")
        # Anything left behind (e.g. the run died before its id was recorded) shows up here.
        res = requests.get(f"{base}/admin/users/", headers=admin, params={"page_size": 100}, timeout=TIMEOUT)
        if res.ok:
            data = res.json()
            leftovers = [u["email"] for u in (data.get("results", data) if isinstance(data, dict) else data)
                         if f"bstest{run}" in (u.get("email") or "")]
            check("cleanup: no throwaway users left in Django", not leftovers, passed, str(leftovers))

    return passed


if __name__ == "__main__":
    results = main()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)
