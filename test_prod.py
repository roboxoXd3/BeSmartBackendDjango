import requests
import uuid
import sys
import time

BASE_URL = "https://api.xbesmart.com/api"
session = requests.Session()

def print_result(name, res):
    success = res.status_code in (200, 201, 204, 404)
    status_str = "PASS" if success else "FAIL"
    print(f"[{status_str}] {name} - Status: {res.status_code}")
    if not success:
        print(f"  Response: {res.text[:300]}")
    return success

print("--- Testing Production Endpoints ---")
all_passed = True

start_time = time.time()
res = session.get(f"{BASE_URL}/products/?subcategory_id={uuid.uuid4()}")
duration = time.time() - start_time
print(f"Subcategory filter latency: {duration:.3f}s")
if not print_result("Filter by subcategory", res):
    all_passed = False

start_time = time.time()
res = session.get(f"{BASE_URL}/products/?rating__gte=4")
duration = time.time() - start_time
print(f"Rating filter latency: {duration:.3f}s")
if not print_result("Filter by rating", res):
    all_passed = False

start_time = time.time()
res = session.get(f"{BASE_URL}/products/{uuid.uuid4()}/")
duration = time.time() - start_time
print(f"Product Detail latency: {duration:.3f}s")
if not print_result("Product Detail (Inactive handling/404 expected)", res):
    all_passed = False

if all_passed:
    print("All production tests passed.")
    sys.exit(0)
else:
    print("Some production tests failed.")
    sys.exit(1)
