import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"
TEST_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_PASSWORD = "StrongPassword123!"

def print_result(name, success, details=""):
    status_str = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status_str}] {name} {details}")
    if not success:
        print("Stopping tests due to failure.")
        sys.exit(1)

def test_auth_flow():
    print(f"Testing Auth Flow with email: {TEST_EMAIL}")
    
    # 1. Register
    reg_res = requests.post(f"{BASE_URL}/users/register/", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": "Test",
        "last_name": "User"
    })
    print_result("Register User", reg_res.status_code == 201, reg_res.text)
    
    # 2. Login
    login_res = requests.post(f"{BASE_URL}/users/login/", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    print_result("Login User", login_res.status_code == 200, login_res.text)
    data = login_res.json()
    
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    
    if not access_token or not refresh_token:
        print_result("Token Check", False, "Missing tokens in response")
        
    print_result("Token Check", True)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 3. Get Profile (Requires Auth)
    profile_res = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    print_result("Get Profile", profile_res.status_code == 200, profile_res.text)
    
    # 4. Refresh Token
    refresh_res = requests.post(f"{BASE_URL}/users/token/refresh/", json={
        "refresh": refresh_token
    })
    print_result("Refresh Token", refresh_res.status_code == 200, refresh_res.text)
    new_access = refresh_res.json().get("access")
    
    # 5. Delete Account
    new_headers = {"Authorization": f"Bearer {new_access}"}
    del_res = requests.post(f"{BASE_URL}/users/account/delete/", json={
        "password": TEST_PASSWORD
    }, headers=new_headers)
    
    # Our view expects "password" but some logic might fail if user logic is wrong.
    print_result("Delete Account", del_res.status_code == 200, del_res.text)

if __name__ == "__main__":
    try:
        requests.get("http://127.0.0.1:8000/api/version-check/")
    except requests.exceptions.ConnectionError:
        print("Server is not running on 127.0.0.1:8000")
        sys.exit(1)
        
    test_auth_flow()
