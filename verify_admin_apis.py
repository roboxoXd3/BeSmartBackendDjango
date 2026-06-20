import os
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "besmart_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

def run_verifications():
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("No staff user found, creating one.")
        user = User.objects.create(email="admin_test@test.com", is_staff=True, is_superuser=True)
        user.set_password("pass123")
        user.save()

    client = APIClient()
    client.force_authenticate(user=user)

    print("Verifying ADM-D-001 (GET /api/admin/dashboard/stats/)...")
    res = client.get('/api/admin/dashboard/stats/')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print("Keys present:", list(data.keys()))
        stats = data.get('data', data)
        assert 'totalRevenue' in stats, "totalRevenue missing"
        assert 'avgOrderValue' in stats, "avgOrderValue missing"
        assert 'revenueChange' in stats, "revenueChange missing"
        assert 'ordersChange' in stats, "ordersChange missing"
        print("ADM-D-001 Verification Passed!")

    print("\nVerifying ADM-D-002 (GET /api/admin/orders/)...")
    res = client.get('/api/admin/orders/?page_size=1')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        results = data.get('results', [])
        if results:
            first_order = results[0]
            print("Order Keys:", list(first_order.keys()))
            assert 'customer' in first_order, "customer missing"
            assert 'vendors' in first_order, "vendors missing"
            print("ADM-D-002 Verification Passed!")
        else:
            print("No orders to verify schema, but endpoint works.")

    print("\nVerifying ADM-D-003 (GET /api/admin/products/)...")
    res = client.get('/api/admin/products/?approval_status=pending')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        print("ADM-D-003 Verification Passed!")

    print("\nVerifying ADM-D-007 (GET /api/admin/vendors/)...")
    res = client.get('/api/admin/vendors/')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        results = data.get('results', [])
        if results:
            first_vendor = results[0]
            print("Vendor Keys:", list(first_vendor.keys()))
            assert 'product_count' in first_vendor, "product_count missing"
            assert 'approved_products' in first_vendor, "approved_products missing"
            assert 'pending_products' in first_vendor, "pending_products missing"
            print("ADM-D-007 Verification Passed!")
        else:
            print("No vendors to verify schema, but endpoint works.")

if __name__ == '__main__':
    run_verifications()
