import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def print_result(name, res):
    if str(res.status_code).startswith('2'):
        print(f"[✅ PASS] {name} - Status: {res.status_code}")
    else:
        print(f"[❌ FAIL] {name} - Status: {res.status_code}\n{res.text}")

def run_tests():
    # 1. Register a test user
    uid = str(uuid.uuid4())[:8]
    email = f"vendor_sdk_{uid}@example.com"
    pw = "VendorPass123!"
    
    res = requests.post(f"{BASE_URL}/users/register/", json={
        "email": email,
        "password": pw,
        "first_name": "Test",
        "last_name": "VendorSDK",
        "is_active": True
    })
    
    if res.status_code != 201:
        print(f"Failed to register: {res.text}")
        return
        
    # Login
    res = requests.post(f"{BASE_URL}/users/login/", json={
        "email": email,
        "password": pw
    })
    
    tokens = res.json()
    access = tokens.get('access_token')
    headers = {"Authorization": f"Bearer {access}"}
    
    # 2. Test User Profile (WEB-S-006)
    res = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    print_result("Get User Profile (WEB-S-006)", res)
    
    # 3. Create Vendor Profile manually (VendorRegisterView actually registers user + vendor, but we used users/register)
    # Actually, we should just use vendor register. Let's do that!
    
    res = requests.post(f"{BASE_URL}/vendors/register/", json={
        "business_name": f"Business {uid}",
        "business_email": email,
        "phone": "1234567890",
        "category": "retail"
    }, headers=headers)
    
    if res.status_code not in [200, 201]:
        print(f"Failed to register vendor: {res.text}")
        return
        
    # Login as vendor (Wait, if we already have token, we can just use it? Vendor login just checks vendor profile)
    res = requests.post(f"{BASE_URL}/users/vendor-login/", json={
        "email": email,
        "password": pw
    })
    tokens = res.json()
    access = tokens.get('access_token')
    headers = {"Authorization": f"Bearer {access}"}
    
    # 4. Get Vendor Profile (VND-S-004)
    res = requests.get(f"{BASE_URL}/vendors/profile/", headers=headers)
    print_result("Get Vendor Profile (VND-S-004)", res)
    
    # 5. Get Categories (WEB-S-003, VND-S-009)
    res = requests.get(f"{BASE_URL}/categories/")
    print_result("Get Categories", res)
    categories = res.json()
    if isinstance(categories, dict):
        categories = categories.get('results', [])
    cat_id = categories[0]['id'] if categories else None
    
    # 6. Bulk Upload (VND-S-008)
    if cat_id:
        bulk_payload = {
            "products": [
                {
                    "name": f"Bulk Product {uid}",
                    "description": "A great bulk product",
                    "price": 150.0,
                    "stock_quantity": 25,
                    "category_id": cat_id,
                    "brand": "BulkBrand"
                }
            ]
        }
        res = requests.post(f"{BASE_URL}/vendors/own-products/bulk-upload/", json=bulk_payload, headers=headers)
        print_result("Bulk Upload Products (VND-S-008)", res)
        if res.status_code == 200:
            print(f"  -> {res.json()}")
    else:
        print("Skipping bulk upload because no categories exist.")
        
    # 7. Get Own Products (VND-S-006)
    res = requests.get(f"{BASE_URL}/vendors/own-products/", headers=headers)
    print_result("Get Own Products (VND-S-006)", res)
    
    own_products = res.json()
    product_id = own_products[0]['id'] if isinstance(own_products, list) and own_products else None
    if isinstance(own_products, dict) and 'results' in own_products:
        product_id = own_products['results'][0]['id'] if own_products['results'] else None
        
    # 8. Update Stock (VND-S-007)
    if product_id:
        res = requests.patch(f"{BASE_URL}/vendors/own-products/{product_id}/stock/", json={"stock_quantity": 50}, headers=headers)
        print_result("Update Stock (VND-S-007)", res)
        
    # 9. Public Products List (WEB-S-001)
    res = requests.get(f"{BASE_URL}/products/")
    print_result("Public Products List (WEB-S-001)", res)

if __name__ == "__main__":
    run_tests()
