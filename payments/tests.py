from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from orders.models import Order
import uuid

User = get_user_model()

class PaymentAPITests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword"
        )
        self.client.force_authenticate(user=self.user)

        # Create a test order
        self.order = Order.objects.create(
            user=self.user,
            subtotal=100.00,
            shipping_fee=10.00,
            total=110.00,
            status='pending',
            payment_status='pending'
        )

    @patch('requests.post')
    def test_initiate_payment_success(self, mock_post):
        # Mock successful Squad API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'status': 200,
            'message': 'Success',
            'data': {
                'checkout_url': 'https://checkout.squadco.com/pay/test_ref',
                'transaction_ref': 'BESMART-TEST12345'
            }
        }

        url = reverse('initiate-payment')
        data = {
            'order_id': str(self.order.id),
            'currency': 'NGN',
            'email': 'testuser@example.com'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['transaction_ref'], 'BESMART-TEST12345')
        self.assertEqual(response.data['data']['checkout_url'], 'https://checkout.squadco.com/pay/test_ref')

        # Check if the order is updated with the transaction reference
        self.order.refresh_from_db()
        self.assertEqual(self.order.squad_transaction_ref, 'BESMART-TEST12345')

    @patch('requests.post')
    def test_initiate_payment_api_failure(self, mock_post):
        # Mock Squad API failure response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            'status': 400,
            'message': 'Invalid transaction parameters'
        }

        url = reverse('initiate-payment')
        data = {
            'order_id': str(self.order.id)
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Invalid transaction parameters')

    @patch('requests.get')
    def test_verify_payment_success(self, mock_get):
        self.order.squad_transaction_ref = 'BESMART-TESTVERIFY'
        self.order.save()

        # Mock successful Squad verification API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': 200,
            'message': 'Success',
            'data': {
                'transaction_status': 'success',
                'gateway_transaction_ref': 'SQUAD-GWAY-12345'
            }
        }

        url = reverse('verify-payment', kwargs={'ref': 'BESMART-TESTVERIFY'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['gateway_ref'], 'SQUAD-GWAY-12345')

        # Check if order is marked as paid and confirmed
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.order.squad_gateway_ref, 'SQUAD-GWAY-12345')

    @patch('requests.get')
    def test_verify_payment_not_successful(self, mock_get):
        self.order.squad_transaction_ref = 'BESMART-TESTFAIL'
        self.order.save()

        # Mock failed Squad verification API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': 200,
            'message': 'Success',
            'data': {
                'transaction_status': 'failed'
            }
        }

        url = reverse('verify-payment', kwargs={'ref': 'BESMART-TESTFAIL'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')

        # Check order payment status did not change
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'pending')
