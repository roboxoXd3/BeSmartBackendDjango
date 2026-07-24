import requests
import uuid

BASE_URL = "http://localhost:8000/api"
session = requests.Session()

def print_result(name, res):
    print(f"[{'PASS' if res.status_code in (200, 201, 404) else 'FAIL'}] {name} - Status: {res.status_code}")
    if res.status_code not in (200, 201, 204, 404):
        print(f"  Response: {res.text[:200]}")

print("--- Testing Public Endpoints ---")
res = session.get(f"{BASE_URL}/products/?subcategory_id={uuid.uuid4()}")
print_result("Filter by subcategory", res)

res = session.get(f"{BASE_URL}/products/?rating__gte=4")
print_result("Filter by rating", res)

res = session.get(f"{BASE_URL}/products/{uuid.uuid4()}/")
print_result("Product Detail", res)
