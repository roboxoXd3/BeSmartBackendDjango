from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    card_holder_name = models.TextField()
    card_number = models.TextField() # Note: storing raw card numbers is not PCI compliant. Assuming tokenization or legacy Requirement.
    card_type = models.TextField()
    expiry_month = models.TextField()
    expiry_year = models.TextField()
    cvv = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True) # Usually not stored
    is_default = models.BooleanField(default=False)
    razorpay_card_token = models.TextField(null=True, blank=True) # Legacy or specific gateway
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_methods'

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
