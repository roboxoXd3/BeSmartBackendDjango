import requests
from supabase import create_client, Client
import random
import string
import time
import json

BASE_URL = "https://besmartbackenddjango-staging.up.railway.app"
SUPABASE_URL = "https://mfbnxhjfbzbxvuzzbryu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1mYm54aGpmYnpieHZ1enpicnl1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYzMTExNTcsImV4cCI6MjA1MTg4NzE1N30.E94k7v8aMXASQnI9Pe2vIubhK3zjX6TWrAqxd4a2S2U"

def run_scenario():
    email = "sa3198154@gmail.com"
    password = "avi10102"
    
    print(f"--- Triggering events on {BASE_URL} ---")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        token = response.session.access_token
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("Obtained Supabase token successfully.")
    except Exception as e:
        print(f"Failed to get Supabase token: {e}")
        return
        
    # 1. Update Profile (Authenticated POST/PATCH)
    print("Hitting PATCH /api/users/profile/")
    res = requests.patch(f"{BASE_URL}/api/users/profile/", headers=headers, json={"first_name": "Log", "last_name": "Tester"})
    print(res.status_code, res.text)
    
    # 2. Try creating a product as a vendor (Will likely 403 if not a vendor, or 400 if bad payload)
    print("Hitting POST /api/vendors/own-products/")
    res = requests.post(f"{BASE_URL}/api/vendors/own-products/", headers=headers, json={
        "name": f"Test Product {random.randint(1000, 9999)}",
        "description": "Generated for log testing",
        "price": "99.99",
        "stock": 50,
        "is_active": True
    })
    print(res.status_code, res.text)

    # 3. Hit cart or orders if available
    print("Hitting GET /api/orders/")
    res = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
    print(res.status_code)
    
    print("--- Finished generating logs! ---")

if __name__ == "__main__":
    run_scenario()
