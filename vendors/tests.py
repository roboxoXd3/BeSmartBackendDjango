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
import uuid

class VendorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_base = User.objects.create(email="testvendor@example.com", username="testvendor@example.com")
        self.vendor = Vendor.objects.create(
            user=self.user_base, 
            business_name="Test Store", 
            business_email="testvendor@example.com",
            status='approved'
        )
        self.product = Product.objects.create(
            name="Sample Item", 
            price=50.00, 
            vendor_id=self.vendor.id,
            approval_status='approved'
        )
        self.order = Order.objects.create(
            user=self.user_base, 
            vendor_id=self.vendor.id,
            total=50.00,
            status='delivered'
        )

    def test_vendor_dashboard_stats_requires_auth(self):
        url = reverse('vendor-dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vendor_dashboard_stats_success(self):
        url = reverse('vendor-dashboard-stats')
        self.client.force_authenticate(user=self.user_base)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('total_products', data)
        self.assertEqual(data['total_products'], 1)

    @patch('users.views.get_supabase_client')
    def test_vendor_login_success(self, mock_get_client):
        # Mocking the Supabase client
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.user.id = str(self.user_base.id)
        mock_response.user.email = self.user_base.email
        mock_response.session = {"access_token": "fake-token"}
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        mock_get_client.return_value = mock_supabase

        url = reverse('auth_vendor_login')
        response = self.client.post(url, {
            'email': 'testvendor@example.com',
            'password': 'password123'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session', response.json())

    def test_vendor_own_products_list(self):
        url = reverse('vendor-own-product-list')
        self.client.force_authenticate(user=self.user_base)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_vendor_own_products_create(self):
        url = reverse('vendor-own-product-list')
        self.client.force_authenticate(user=self.user_base)
        data = {
            "name": "New Item",
            "price": "19.99"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(vendor_id=self.vendor.id).count(), 2)

    def test_vendor_order_list(self):
        url = reverse('vendor-orders-list')
        self.client.force_authenticate(user=self.user_base)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_vendor_payout_summary(self):
        url = reverse('vendor-payouts-summary')
        self.client.force_authenticate(user=self.user_base)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('availableBalance', data)
        self.assertIn('lifetimeEarnings', data)
