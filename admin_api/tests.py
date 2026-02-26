from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from users.models import User
from vendors.models import Vendor
from products.models import Product
from orders.models import Order
from django.utils import timezone

class AdminAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create(email="superuser@example.com", username="superuser@example.com", is_staff=True, is_superuser=True)
        self.normal_user = User.objects.create(email="normal@example.com", username="normal@example.com")
        self.vendor = Vendor.objects.create(
            user=self.normal_user, 
            business_name="Test Vendor", 
            business_email="vendor@example.com",
            status='pending'
        )

    def test_admin_dashboard_stats_requires_staff(self):
        url = reverse('admin-system-stats')
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        # Normal user does not have is_staff=True
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_stats_success(self):
        url = reverse('admin-system-stats')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_users'], 2)
        self.assertEqual(data['pending_vendors'], 1)

    def test_admin_approve_vendor(self):
        url = reverse('admin-vendors-status', args=[self.vendor.id])
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(url, {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.status, 'approved')

    def test_admin_suspend_user(self):
        url = reverse('admin-users-status', args=[self.normal_user.id])
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(url, {'action': 'suspend'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    def test_admin_loyalty_points(self):
        url = reverse('admin-loyalty-points', args=[self.normal_user.id])
        self.client.force_authenticate(user=self.admin_user)
        # Add 100 points
        response = self.client.post(url, {'points': 100}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        if hasattr(self.normal_user, 'loyalty_points_earned'):
            self.assertEqual(self.normal_user.loyalty_points_earned, 100)
