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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    user_email = models.TextField()
    
    # Amount details
    amount = models.IntegerField()
    currency = models.TextField(default='NGN')
    
    # Transaction details
    transaction_ref = models.TextField(unique=True, db_index=True)
    
    # Status tracking
    status = models.TextField(default='pending')
    payment_type = models.TextField()
    
    # Gateway specific fields
    token = models.TextField(blank=True, null=True)
    gateway_response = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
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
    
    def mark_as_success(self, gateway_res=None, payment_type=None):
        """Mark payment as successful"""
        self.status = 'success'
        if gateway_res:
            self.gateway_response = gateway_res
        if payment_type:
            self.payment_type = payment_type
        self.save()
    
    def mark_as_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()

class PaymentWebhook(models.Model):
    """Store all webhook events from Squad"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Webhook details
    transaction_ref = models.CharField(max_length=255, db_index=True)
    order_id = models.UUIDField(null=True, blank=True)
    
    # Raw data
    webhook_data = models.JSONField()
    
    # Processing status
    status = models.CharField(max_length=255)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
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

class OtherPaymentMethods(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.UUIDField()
    payment_method = models.TextField()
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'other_payment_methods'

