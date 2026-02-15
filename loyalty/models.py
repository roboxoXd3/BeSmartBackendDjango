from django.db import models
from django.contrib.auth import get_user_model
import uuid
from orders.models import Order

User = get_user_model()

class LoyaltyBadge(models.Model):
    BADGE_TYPE_CHOICES = (
        ('order_count', 'Order Count'),
        ('spending_amount', 'Spending Amount'),
        ('streak', 'Streak'),
        ('special', 'Special'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    icon_url = models.TextField(null=True, blank=True)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPE_CHOICES)
    requirement_value = models.IntegerField(null=True, blank=True)
    bonus_points = models.IntegerField(default=0)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loyalty_badges'


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(LoyaltyBadge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_badges'


class LoyaltyEarningRule(models.Model):
    RULE_TYPE_CHOICES = (
        ('order_purchase', 'Order Purchase'),
        ('milestone', 'Milestone'),
        ('bonus', 'Bonus'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.TextField()
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES, default='order_purchase')
    points_per_currency_unit = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loyalty_earning_rules'

class LoyaltyPoints(models.Model):
    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_points')
    points_balance = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    tier_updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loyalty_points'

class LoyaltyReward(models.Model):
    REWARD_TYPE_CHOICES = (
        ('discount_percentage', 'Discount Percentage'),
        ('discount_fixed', 'Discount Fixed'),
        ('free_shipping', 'Free Shipping'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    points_required = models.IntegerField()
    reward_type = models.CharField(max_length=50, choices=REWARD_TYPE_CHOICES)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    validity_days = models.IntegerField(default=30)
    max_redemptions_per_user = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loyalty_rewards'

class LoyaltyVoucher(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vouchers')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE)
    voucher_code = models.TextField(unique=True)
    points_spent = models.IntegerField()
    discount_type = models.TextField()
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    redeemed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_voucher')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loyalty_vouchers'

class LoyaltyTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
        ('expire', 'Expire'),
        ('adjustment', 'Adjustment'),
        ('bonus', 'Bonus'),
    )
    REFERENCE_TYPE_CHOICES = (
        ('order', 'Order'),
        ('voucher', 'Voucher'),
        ('admin', 'Admin'),
        ('milestone', 'Milestone'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    points_change = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES, null=True, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    description = models.TextField()
    points_balance_after = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loyalty_transactions'
