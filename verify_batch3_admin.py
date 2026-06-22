import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "besmart_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from loyalty.models import LoyaltyPoints, LoyaltyTransaction

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

    print("Verifying Category Admin GET /api/admin/categories/ ...")
    res = client.get('/api/admin/categories/')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print("Categories fetched:", len(data.get('results', [])))
        print("Category Admin Verification Passed!")
    else:
        print("Category Admin Verification Failed:", res.content)

    print("\nVerifying Loyalty Admin POST /api/admin/loyalty/{id}/points/ ...")
    target_user = User.objects.first()
    res = client.post(f'/api/admin/loyalty/{target_user.id}/points/', {
        "points": 50,
        "description": "Test bonus points"
    }, format='json')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print("Response:", data)
        assert data['points_balance'] >= 50, "Points balance not updated correctly in response"
        
        # Verify db
        loyalty = LoyaltyPoints.objects.get(user=target_user)
        assert loyalty.points_balance >= 50, "Points balance not updated in DB"
        
        tx = LoyaltyTransaction.objects.filter(user=target_user).order_by('-created_at').first()
        assert tx is not None, "Transaction not created"
        assert tx.points_change == 50, "Transaction points mismatch"
        assert tx.description == "Test bonus points", "Transaction description mismatch"
        
        print("Loyalty Admin Verification Passed!")
    else:
        print("Loyalty Admin Verification Failed:", res.content)

if __name__ == '__main__':
    run_verifications()
