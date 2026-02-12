# Django Squad Payment Integration - Complete Backend Guide

## Table of Contents
1. [Overview](#overview)
2. [Project Setup](#project-setup)
3. [Database Models](#database-models)
4. [Settings Configuration](#settings-configuration)
5. [Service Layer](#service-layer)
6. [API Views & Endpoints](#api-views--endpoints)
7. [Webhook Implementation](#webhook-implementation)
8. [Security & Validation](#security--validation)
9. [Testing](#testing)
10. [Deployment](#deployment)

---

## 1. Overview

### What This Guide Covers

This guide provides complete Django implementation for Squad payment gateway integration, including:
- ✅ Payment initiation and processing
- ✅ Order management with payment tracking
- ✅ Webhook handling for payment notifications
- ✅ Vendor payout system
- ✅ Escrow management
- ✅ Transaction verification
- ✅ Multi-currency support

### Architecture Overview

```
Client Request → Django View → Service Layer → Squad API
                      ↓
                Database Models
                      ↓
                Webhook Handler → Update Order Status
```

---

## 2. Project Setup

### 2.1 Install Required Packages

```bash
pip install djangorestframework
pip install requests
pip install python-decouple
pip install django-cors-headers
pip install celery  # For async tasks (optional but recommended)
```

### 2.2 Update `requirements.txt`

```txt
Django==4.2.7
djangorestframework==3.14.0
requests==2.31.0
python-decouple==3.8
django-cors-headers==4.3.1
celery==5.3.4
redis==5.0.1  # For Celery broker
psycopg2-binary==2.9.9  # PostgreSQL adapter
```

### 2.3 Create Django App

```bash
# Create payments app
python manage.py startapp payments

# Create orders app (if not exists)
python manage.py startapp orders

# Create payouts app (for vendor payouts)
python manage.py startapp payouts
```

### 2.4 Add Apps to `settings.py`

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    
    # Your apps
    'payments',
    'orders',
    'payouts',
    'products',  # Assuming you have this
    'users',     # Assuming you have this
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this at the top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

## 3. Database Models

### 3.1 Create Models for Payments App

Create `payments/models.py`:

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Payment(models.Model):
    """Main payment model to track all payment transactions"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('ussd', 'USSD'),
        ('wallet', 'Wallet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Transaction details
    transaction_ref = models.CharField(max_length=255, unique=True, db_index=True)
    gateway_transaction_ref = models.CharField(max_length=255, blank=True, null=True)
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    
    # Squad specific fields
    checkout_url = models.URLField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_ref']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_ref} - {self.status}"
    
    def mark_as_success(self, gateway_ref=None, payment_method=None):
        """Mark payment as successful"""
        self.status = 'success'
        self.completed_at = timezone.now()
        if gateway_ref:
            self.gateway_transaction_ref = gateway_ref
        if payment_method:
            self.payment_method = payment_method
        self.save()
    
    def mark_as_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()


class PaymentWebhook(models.Model):
    """Store all webhook events from Squad"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='webhooks')
    
    # Webhook details
    event_type = models.CharField(max_length=100)
    transaction_ref = models.CharField(max_length=255, db_index=True)
    
    # Raw data
    payload = models.JSONField()
    signature = models.CharField(max_length=255)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_webhooks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook {self.event_type} - {self.transaction_ref}"


class Refund(models.Model):
    """Track payment refunds"""
    
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    REFUND_TYPE_CHOICES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    # Squad reference
    refund_reference = models.CharField(max_length=255, blank=True, null=True)
    gateway_refund_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    
    # Admin details
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.id} - {self.amount} - {self.status}"
```

### 3.2 Update Orders Model

Add to `orders/models.py`:

```python
from django.db import models
import uuid

class Order(models.Model):
    """Order model with payment tracking"""
    
    ORDER_STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partially_refunded', 'Partially Refunded'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending_payment')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    # Escrow tracking
    escrow_status = models.CharField(max_length=20, default='none')
    escrow_release_date = models.DateTimeField(blank=True, null=True)
    vendor_payout_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Shipping details
    shipping_address = models.JSONField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        prefix = 'ORD'
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return f"{prefix}{random_part}"


class OrderItem(models.Model):
    """Individual items in an order"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
```

### 3.3 Create Payouts Models

Create `payouts/models.py`:

```python
from django.db import models
import uuid

class VendorBankAccount(models.Model):
    """Store vendor bank account details for payouts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('users.Vendor', on_delete=models.CASCADE, related_name='bank_accounts')
    
    # Bank details
    bank_code = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_bank_accounts'
        unique_together = ['vendor', 'account_number']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class VendorPayout(models.Model):
    """Track vendor payout requests"""
    
    PAYOUT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('users.Vendor', on_delete=models.CASCADE, related_name='payouts')
    bank_account = models.ForeignKey(VendorBankAccount, on_delete=models.CASCADE)
    
    # Payout details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Squad transaction reference
    transaction_ref = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='pending')
    
    # Admin approval
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Processing details
    failure_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'vendor_payouts'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Payout {self.id} - {self.vendor} - {self.amount}"


class EscrowTransaction(models.Model):
    """Track escrow transactions linking orders to payouts"""
    
    ESCROW_STATUS_CHOICES = [
        ('held', 'Held'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='escrow_transactions')
    vendor = models.ForeignKey('users.Vendor', on_delete=models.CASCADE, related_name='escrow_transactions')
    payout = models.ForeignKey(VendorPayout, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=ESCROW_STATUS_CHOICES, default='held')
    
    # Release date
    release_date = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'escrow_transactions'
        ordering = ['-created_at']
```

### 3.4 Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 4. Settings Configuration

### 4.1 Update `settings.py`

```python
from decouple import config

# Squad Payment Configuration
SQUAD_CONFIG = {
    'SECRET_KEY': config('SQUAD_SECRET_KEY'),
    'PUBLIC_KEY': config('SQUAD_PUBLIC_KEY'),
    'BASE_URL': config('SQUAD_BASE_URL', default='https://sandbox-api-d.squadco.com'),
    'WEBHOOK_SECRET': config('SQUAD_WEBHOOK_SECRET'),
}

# Payment Configuration
PAYMENT_CONFIG = {
    'MIN_PAYOUT_AMOUNT': 5000,  # ₦50 minimum payout
    'PAYOUT_PROCESSING_FEE': 0.025,  # 2.5% fee
    'ESCROW_HOLD_DAYS': 7,  # Hold funds for 7 days
    'CALLBACK_URL': config('PAYMENT_CALLBACK_URL', default='http://localhost:8000/api/payments/callback/'),
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your production frontend URL
]

CORS_ALLOW_CREDENTIALS = True
```

### 4.2 Create `.env` File

```bash
# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Squad API Keys
SQUAD_SECRET_KEY=sandbox_sk_your_secret_key
SQUAD_PUBLIC_KEY=sandbox_pk_your_public_key
SQUAD_BASE_URL=https://sandbox-api-d.squadco.com
SQUAD_WEBHOOK_SECRET=your_webhook_secret

# Payment Configuration
PAYMENT_CALLBACK_URL=http://localhost:8000/api/payments/callback/
MIN_PAYOUT_AMOUNT=5000

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

---

## 5. Service Layer

### 5.1 Create Squad Service

Create `payments/services/squad_service.py`:

```python
import requests
import hashlib
import hmac
import json
from decimal import Decimal
from django.conf import settings
from typing import Dict, Optional


class SquadPaymentService:
    """Service class to interact with Squad API"""
    
    def __init__(self):
        self.secret_key = settings.SQUAD_CONFIG['SECRET_KEY']
        self.public_key = settings.SQUAD_CONFIG['PUBLIC_KEY']
        self.base_url = settings.SQUAD_CONFIG['BASE_URL']
        self.webhook_secret = settings.SQUAD_CONFIG['WEBHOOK_SECRET']
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Squad API"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initiate_payment(
        self,
        amount: Decimal,
        email: str,
        transaction_ref: str,
        currency: str = 'NGN',
        callback_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Initiate payment with Squad
        
        Args:
            amount: Payment amount in naira (will be converted to kobo)
            email: Customer email
            transaction_ref: Unique transaction reference
            currency: Currency code (default: NGN)
            callback_url: URL to redirect after payment
            metadata: Additional data to store
        
        Returns:
            Dict containing checkout_url and transaction details
        """
        url = f"{self.base_url}/transaction/initiate"
        
        # Convert amount to smallest currency unit (kobo)
        amount_in_kobo = int(amount * 100)
        
        payload = {
            'amount': amount_in_kobo,
            'email': email,
            'currency': currency,
            'initiate_type': 'inline',
            'transaction_ref': transaction_ref,
            'callback_url': callback_url or settings.PAYMENT_CONFIG['CALLBACK_URL'],
        }
        
        if metadata:
            payload['metadata'] = metadata
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Squad API Error: {str(e)}")
    
    def verify_transaction(self, transaction_ref: str) -> Dict:
        """
        Verify transaction status with Squad
        
        Args:
            transaction_ref: Transaction reference to verify
        
        Returns:
            Dict containing transaction details
        """
        url = f"{self.base_url}/transaction/verify/{transaction_ref}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Squad Verification Error: {str(e)}")
    
    def validate_webhook_signature(self, payload: Dict, signature: str) -> bool:
        """
        Validate webhook signature from Squad
        
        Args:
            payload: Webhook payload
            signature: Signature from x-squad-encrypted-body header
        
        Returns:
            Boolean indicating if signature is valid
        """
        payload_string = json.dumps(payload, separators=(',', ':'))
        
        computed_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)


class SquadTransferService:
    """Service class for Squad transfer/payout operations"""
    
    def __init__(self):
        self.secret_key = settings.SQUAD_CONFIG['SECRET_KEY']
        self.base_url = settings.SQUAD_CONFIG['BASE_URL']
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def lookup_account(self, bank_code: str, account_number: str) -> Dict:
        """
        Lookup and verify bank account details
        
        Args:
            bank_code: Bank's NIP code
            account_number: Account number to verify
        
        Returns:
            Dict containing account name and number
        """
        url = f"{self.base_url}/payout/account/lookup"
        
        payload = {
            'bank_code': bank_code,
            'account_number': account_number
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 200 and data.get('success'):
                return {
                    'success': True,
                    'account_name': data['data']['account_name'],
                    'account_number': data['data']['account_number']
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Account lookup failed')
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f"Lookup Error: {str(e)}"
            }
    
    def initiate_transfer(
        self,
        transaction_ref: str,
        amount: Decimal,
        bank_code: str,
        account_number: str,
        account_name: str,
        remark: str = 'Vendor payout',
        currency: str = 'NGN'
    ) -> Dict:
        """
        Initiate bank transfer to vendor
        
        Args:
            transaction_ref: Unique transaction reference (must include merchant ID)
            amount: Transfer amount in naira (will be converted to kobo)
            bank_code: Bank's NIP code
            account_number: Recipient account number
            account_name: Account name from lookup
            remark: Transfer description
            currency: Currency code
        
        Returns:
            Dict containing transfer status
        """
        url = f"{self.base_url}/payout/transfer"
        
        # Convert to kobo
        amount_in_kobo = str(int(amount * 100))
        
        payload = {
            'transaction_reference': transaction_ref,
            'amount': amount_in_kobo,
            'bank_code': bank_code,
            'account_number': account_number,
            'account_name': account_name,
            'currency_id': currency,
            'remark': remark
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Transfer Error: {str(e)}")
    
    def query_transfer_status(self, transaction_ref: str) -> Dict:
        """
        Query the status of a transfer
        
        Args:
            transaction_ref: Transfer reference to query
        
        Returns:
            Dict containing transfer status
        """
        url = f"{self.base_url}/payout/requery"
        
        payload = {'transaction_reference': transaction_ref}
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Query Error: {str(e)}")
```

### 5.2 Create Order Service

Create `orders/services.py`:

```python
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from orders.models import Order, OrderItem
from payments.models import Payment
from payments.services.squad_service import SquadPaymentService


class OrderService:
    """Business logic for order management"""
    
    @staticmethod
    def create_order_from_cart(user, cart_items, shipping_address):
        """
        Create order from cart items
        
        Args:
            user: User object
            cart_items: List of cart items
            shipping_address: Dict with shipping details
        
        Returns:
            Order object
        """
        with transaction.atomic():
            # Calculate total
            total_amount = Decimal('0.00')
            
            # Generate unique order number
            order = Order(user=user)
            order.order_number = order.generate_order_number()
            order.shipping_address = shipping_address
            order.status = 'pending_payment'
            order.payment_status = 'unpaid'
            
            # Validate stock and calculate total
            order_items_data = []
            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity
                
                # Check stock availability
                if product.stock < quantity:
                    raise ValueError(f"Insufficient stock for {product.name}")
                
                # Calculate subtotal
                subtotal = product.price * quantity
                total_amount += subtotal
                
                order_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.price,
                    'subtotal': subtotal
                })
            
            # Save order
            order.total_amount = total_amount
            order.save()
            
            # Create order items
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    **item_data
                )
            
            return order
    
    @staticmethod
    def initiate_payment_for_order(order):
        """
        Initiate payment for an order
        
        Args:
            order: Order object
        
        Returns:
            Payment object with checkout_url
        """
        # Generate unique transaction reference
        transaction_ref = f"PAY_{order.order_number}_{timezone.now().timestamp()}"
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=order.user,
            transaction_ref=transaction_ref,
            amount=order.total_amount,
            currency=order.currency,
            status='pending',
            metadata={
                'order_number': order.order_number,
                'order_id': str(order.id),
            }
        )
        
        # Call Squad API
        squad_service = SquadPaymentService()
        
        try:
            response = squad_service.initiate_payment(
                amount=order.total_amount,
                email=order.user.email,
                transaction_ref=transaction_ref,
                currency=order.currency,
                metadata={
                    'order_id': str(order.id),
                    'user_id': str(order.user.id),
                }
            )
            
            if response.get('status') == 200:
                data = response.get('data', {})
                payment.checkout_url = data.get('checkout_url')
                payment.status = 'processing'
                payment.save()
                
                return payment
            else:
                payment.mark_as_failed()
                raise Exception(response.get('message', 'Payment initiation failed'))
                
        except Exception as e:
            payment.mark_as_failed()
            raise e
    
    @staticmethod
    def handle_successful_payment(payment):
        """
        Handle successful payment processing
        
        Args:
            payment: Payment object
        """
        with transaction.atomic():
            # Update payment
            payment.mark_as_success()
            
            # Update order
            order = payment.order
            order.status = 'confirmed'
            order.payment_status = 'paid'
            order.save()
            
            # Deduct inventory
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                product.save()
            
            # Create escrow transaction (if vendor system)
            # EscrowService.create_escrow_for_order(order)
            
            # Send confirmation email
            # EmailService.send_order_confirmation(order)
```

---

## 6. API Views & Endpoints

### 6.1 Create Serializers

Create `payments/serializers.py`:

```python
from rest_framework import serializers
from payments.models import Payment, Refund
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_ref', 'amount', 'currency',
            'status', 'payment_method', 'checkout_url',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'transaction_ref', 'checkout_url', 'created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    
    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
            if order.payment_status == 'paid':
                raise serializers.ValidationError("Order already paid")
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")


class VerifyPaymentSerializer(serializers.Serializer):
    transaction_ref = serializers.CharField()


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'refund_type', 'amount', 'reason', 'status', 'created_at']
```

### 6.2 Create Payment Views

Create `payments/views.py`:

```python
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from payments.models import Payment, PaymentWebhook
from payments.serializers import (
    PaymentSerializer,
    InitiatePaymentSerializer,
    VerifyPaymentSerializer
)
from payments.services.squad_service import SquadPaymentService
from orders.models import Order
from orders.services import OrderService


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment operations
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments by current user"""
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate payment for an order
        
        POST /api/payments/initiate/
        Body: {"order_id": "uuid"}
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get order
            order = get_object_or_404(
                Order,
                id=serializer.validated_data['order_id'],
                user=request.user
            )
            
            # Initiate payment
            payment = OrderService.initiate_payment_for_order(order)
            
            return Response({
                'success': True,
                'data': {
                    'payment_id': str(payment.id),
                    'transaction_ref': payment.transaction_ref,
                    'checkout_url': payment.checkout_url,
                    'amount': float(payment.amount),
                    'currency': payment.currency
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def verify(self, request):
        """
        Verify payment status
        
        GET /api/payments/verify/?transaction_ref=xxx
        """
        transaction_ref = request.query_params.get('transaction_ref')
        
        if not transaction_ref:
            return Response({
                'success': False,
                'message': 'Transaction reference required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get payment from database
            payment = get_object_or_404(
                Payment,
                transaction_ref=transaction_ref,
                user=request.user
            )
            
            # Verify with Squad API
            squad_service = SquadPaymentService()
            verification = squad_service.verify_transaction(transaction_ref)
            
            if verification.get('status') == 200:
                data = verification.get('data', {})
                transaction_status = data.get('transaction_status')
                
                if transaction_status == 'Success':
                    # Update payment and order
                    if payment.status != 'success':
                        OrderService.handle_successful_payment(payment)
                    
                    return Response({
                        'success': True,
                        'data': {
                            'status': 'success',
                            'transaction_ref': transaction_ref,
                            'amount': data.get('transaction_amount'),
                            'payment_method': data.get('transaction_type'),
                            'order_id': str(payment.order.id)
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Payment not successful',
                        'data': {'status': transaction_status}
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                raise Exception('Verification failed')
                
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get payment history for current user
        
        GET /api/payments/history/
        """
        payments = self.get_queryset().select_related('order')
        serializer = self.get_serializer(payments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def squad_webhook(request):
    """
    Handle webhook notifications from Squad
    
    POST /api/payments/webhook/
    """
    try:
        # Get signature from header
        signature = request.headers.get('x-squad-encrypted-body', '')
        
        if not signature:
            return Response({
                'message': 'Missing signature'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        payload = request.data
        
        # Validate signature
        squad_service = SquadPaymentService()
        if not squad_service.validate_webhook_signature(payload, signature):
            return Response({
                'message': 'Invalid signature'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Store webhook
        event_type = payload.get('Event')
        body = payload.get('Body', {})
        transaction_ref = body.get('transaction_ref')
        
        webhook = PaymentWebhook.objects.create(
            event_type=event_type,
            transaction_ref=transaction_ref,
            payload=payload,
            signature=signature
        )
        
        # Process webhook based on event type
        if event_type == 'charge_successful':
            try:
                payment = Payment.objects.get(transaction_ref=transaction_ref)
                webhook.payment = payment
                
                # Update payment status
                if payment.status != 'success':
                    payment.gateway_transaction_ref = body.get('gateway_transaction_ref')
                    payment.payment_method = body.get('transaction_type', '').lower()
                    
                    OrderService.handle_successful_payment(payment)
                
                webhook.is_processed = True
                webhook.save()
                
            except Payment.DoesNotExist:
                pass
        
        return Response({
            'message': 'Webhook received'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'message': f'Webhook processing error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 6.3 Create URL Configuration

Create `payments/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', views.squad_webhook, name='squad-webhook'),
]
```

Update main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('payments.urls')),
    path('api/', include('orders.urls')),
    # ... other URLs
]
```

---

## 7. Webhook Implementation

### 7.1 Webhook Security

The webhook handler already includes signature validation. Make sure to:

1. **Always validate signatures** before processing
2. **Use CSRF exemption** for webhook endpoint
3. **Store all webhooks** for audit trail
4. **Handle duplicate webhooks** (idempotency)

### 7.2 Webhook Testing with ngrok

For local development:

```bash
# Install ngrok
npm install -g ngrok

# Start ngrok
ngrok http 8000

# Use the ngrok URL in Squad dashboard
# Example: https://abc123.ngrok.io/api/webhook/
```

---

## 8. Security & Validation

### 8.1 Input Validation

```python
# Always validate amounts on the server
def validate_order_amount(order):
    """Recalculate order total to prevent tampering"""
    calculated_total = sum(
        item.price * item.quantity
        for item in order.items.all()
    )
    
    if calculated_total != order.total_amount:
        raise ValueError("Order amount mismatch")
```

### 8.2 Environment Variables

Never commit sensitive data:

```python
# ❌ WRONG
SQUAD_SECRET_KEY = 'sandbox_sk_123456789'

# ✅ CORRECT
SQUAD_SECRET_KEY = config('SQUAD_SECRET_KEY')
```

### 8.3 API Rate Limiting

Add to `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',
        'user': '100/hour'
    }
}
```

---

## 9. Testing

### 9.1 Create Test Cases

Create `payments/tests/test_payment_flow.py`:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from decimal import Decimal

from payments.services.squad_service import SquadPaymentService
from orders.services import OrderService
from orders.models import Order
from payments.models import Payment

User = get_user_model()


class PaymentFlowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            total_amount=Decimal('10000.00'),
            status='pending_payment'
        )
    
    @patch('payments.services.squad_service.requests.post')
    def test_initiate_payment_success(self, mock_post):
        """Test successful payment initiation"""
        # Mock Squad API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 200,
            'data': {
                'checkout_url': 'https://sandbox-pay.squadco.com/test',
                'transaction_ref': 'PAY_TEST123',
                'transaction_amount': 1000000
            }
        }
        mock_post.return_value = mock_response
        
        # Initiate payment
        payment = OrderService.initiate_payment_for_order(self.order)
        
        # Assertions
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'processing')
        self.assertIsNotNone(payment.checkout_url)
        self.assertEqual(payment.amount, self.order.total_amount)
    
    @patch('payments.services.squad_service.requests.get')
    def test_verify_payment_success(self, mock_get):
        """Test payment verification"""
        # Create payment
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            transaction_ref='PAY_TEST123',
            amount=Decimal('10000.00'),
            status='processing'
        )
        
        # Mock verification response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 200,
            'data': {
                'transaction_status': 'Success',
                'transaction_ref': 'PAY_TEST123',
                'transaction_amount': 1000000
            }
        }
        mock_get.return_value = mock_response
        
        # Verify payment
        squad_service = SquadPaymentService()
        result = squad_service.verify_transaction('PAY_TEST123')
        
        # Assertions
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['data']['transaction_status'], 'Success')
    
    def test_handle_successful_payment(self):
        """Test successful payment handling"""
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            transaction_ref='PAY_TEST123',
            amount=Decimal('10000.00'),
            status='processing'
        )
        
        # Handle successful payment
        OrderService.handle_successful_payment(payment)
        
        # Refresh from database
        payment.refresh_from_db()
        self.order.refresh_from_db()
        
        # Assertions
        self.assertEqual(payment.status, 'success')
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.order.payment_status, 'paid')


class WebhookTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            total_amount=Decimal('10000.00')
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            transaction_ref='PAY_TEST123',
            amount=Decimal('10000.00'),
            status='processing'
        )
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        squad_service = SquadPaymentService()
        
        payload = {
            'Event': 'charge_successful',
            'TransactionRef': 'PAY_TEST123'
        }
        
        # This will fail with invalid signature
        # In production, use actual webhook secret
        result = squad_service.validate_webhook_signature(
            payload,
            'invalid_signature'
        )
        
        self.assertFalse(result)
```

### 9.2 Run Tests

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test payments.tests.test_payment_flow

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 10. Deployment

### 10.1 Production Checklist

- [ ] Update `DEBUG = False` in production
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Use production Squad API keys
- [ ] Update `SQUAD_BASE_URL` to production: `https://api-d.squadco.com`
- [ ] Configure HTTPS for webhook endpoint
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure Redis for Celery (if using async tasks)
- [ ] Set up email service for notifications
- [ ] Configure static files with CDN
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy

### 10.2 Environment Variables for Production

```bash
# Production settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/production_db

# Squad Production Keys
SQUAD_SECRET_KEY=live_sk_your_production_key
SQUAD_PUBLIC_KEY=live_pk_your_production_key
SQUAD_BASE_URL=https://api-d.squadco.com
SQUAD_WEBHOOK_SECRET=your_production_webhook_secret

# Production URLs
PAYMENT_CALLBACK_URL=https://yourdomain.com/api/payments/callback/
FRONTEND_URL=https://yourdomain.com
```

### 10.3 Deploy with Gunicorn & Nginx

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 your_project.wsgi:application
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/static/;
    }
}
```

### 10.4 Monitoring & Logging

```python
# settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        },
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/payments.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'payments': {
            'handlers': ['payment_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## API Endpoints Summary

### Payment Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/payments/initiate/` | Initiate payment for order | Yes |
| GET | `/api/payments/verify/?transaction_ref=xxx` | Verify payment status | Yes |
| GET | `/api/payments/history/` | Get user payment history | Yes |
| POST | `/api/webhook/` | Squad webhook handler | No (signature validated) |

### Request/Response Examples

**1. Initiate Payment**

```bash
POST /api/payments/initiate/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "order_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "payment_id": "123e4567-e89b-12d3-a456-426614174000",
        "transaction_ref": "PAY_ORD123_1234567890",
        "checkout_url": "https://sandbox-pay.squadco.com/PAY_ORD123_1234567890",
        "amount": 25000.00,
        "currency": "NGN"
    }
}
```

**2. Verify Payment**

```bash
GET /api/payments/verify/?transaction_ref=PAY_ORD123_1234567890
Authorization: Bearer <jwt_token>
```

Response:
```json
{
    "success": true,
    "data": {
        "status": "success",
        "transaction_ref": "PAY_ORD123_1234567890",
        "amount": 2500000,
        "payment_method": "Card",
        "order_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

---

## Squad Bank Codes Reference

```python
# Add to your constants file

SQUAD_BANK_CODES = {
    '000013': 'GTBank',
    '000014': 'Access Bank',
    '000016': 'First Bank',
    '000004': 'UBA',
    '000015': 'Zenith Bank',
    '000010': 'Ecobank',
    '000003': 'FCMB',
    '000001': 'Sterling Bank',
    '000007': 'Fidelity Bank',
    '000018': 'Union Bank',
    '000005': 'Stanbic IBTC',
    '000011': 'Unity Bank',
    '000017': 'Wema Bank',
    '000008': 'Polaris Bank',
    '000012': 'Keystone Bank',
}
```

---

## Common Issues & Solutions

### Issue 1: Amount Mismatch

**Problem:** Squad rejects transaction due to amount format

**Solution:** Always convert to smallest unit (kobo)

```python
# ✅ CORRECT
amount_in_kobo = int(amount * 100)

# ❌ WRONG
amount_in_kobo = amount  # Don't send naira value
```

### Issue 2: Webhook Not Receiving Events

**Problem:** Webhook endpoint not accessible

**Solution:**
- Ensure endpoint is publicly accessible
- Use ngrok for local testing
- Check firewall settings
- Verify webhook URL in Squad dashboard

### Issue 3: Signature Validation Fails

**Problem:** Webhook signature doesn't match

**Solution:**
```python
# Ensure exact payload structure
payload_string = json.dumps(payload, separators=(',', ':'))
# No spaces after separators
```

---

## Next Steps

1. **Implement the models** - Run migrations
2. **Create the service layer** - Implement Squad integration
3. **Build the API endpoints** - Create views and serializers
4. **Test thoroughly** - Use Squad sandbox environment
5. **Set up webhooks** - Configure webhook URL in Squad dashboard
6. **Deploy to production** - Update to live keys

---

## Support & Resources

- **Squad API Documentation:** https://docs.squadco.com
- **Squad Dashboard:** https://dashboard.squadco.com
- **Django REST Framework:** https://www.django-rest-framework.org/
- **This Project Repository:** [Add your repo URL]

---

**Document Version:** 1.0  
**Last Updated:** February 9, 2026  
**Target Audience:** Django Backend Developers  
**Status:** ✅ Ready for Implementation
