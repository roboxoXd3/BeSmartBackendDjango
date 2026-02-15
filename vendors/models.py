from django.db import models
from django.contrib.auth import get_user_model
import uuid
from categories.models import Category

User = get_user_model()

class Vendor(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
    )
    BUSINESS_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('partnership', 'Partnership'),
        ('llc', 'LLC'),
    )
    VERIFICATION_STATUS_CHOICES = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    PAYOUT_SCHEDULE_CHOICES = (
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    business_name = models.TextField()
    business_description = models.TextField(null=True, blank=True)
    business_logo = models.TextField(null=True, blank=True)
    business_email = models.TextField()
    business_phone = models.TextField(null=True, blank=True)
    business_address = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    business_registration_number = models.TextField(null=True, blank=True)
    tax_id = models.TextField(null=True, blank=True)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
    verification_documents = models.JSONField(null=True, blank=True)
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    payout_schedule = models.CharField(max_length=20, choices=PAYOUT_SCHEDULE_CHOICES, default='monthly')
    bank_account_info = models.JSONField(null=True, blank=True)
    payment_method_preference = models.TextField(default='bank_transfer')
    last_login_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    admin_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'vendors'

class VendorBankAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default='NGN')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_bank_accounts'

class VendorReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_reviews'

class VendorPayout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    status = models.CharField(max_length=20, default='pending')
    squad_transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    bank_account = models.ForeignKey(VendorBankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    failure_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'vendor_payouts'

class PayoutTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payout = models.ForeignKey(VendorPayout, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    transaction_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payout_transactions'

class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    billing_period = models.CharField(max_length=20, default='monthly') 
    features = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'

class VendorSubscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    payment_method_id = models.UUIDField(null=True, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_subscriptions'

class VendorSizeChartTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.CharField(max_length=255, null=True, blank=True)
    measurement_types = models.JSONField()
    measurement_instructions = models.TextField(null=True, blank=True)
    size_recommendations = models.JSONField(null=True, blank=True)
    chart_type = models.CharField(max_length=50, default='custom')
    template_data = models.JSONField()
    approval_status = models.CharField(max_length=20, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_dynamic = models.BooleanField(default=False)
    schema_version = models.CharField(max_length=10, default='1.0')
    migration_completed_at = models.DateTimeField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'vendor_size_chart_templates'

class VendorFollow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendor_follows'
        unique_together = [['user', 'vendor']]


class EscrowTransaction(models.Model):
    """Track escrow transactions linking orders to payouts"""
    
    ESCROW_STATUS_CHOICES = [
        ('held', 'Held'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='escrow_transactions')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='escrow_transactions')
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
