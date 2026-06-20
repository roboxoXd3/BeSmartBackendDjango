from rest_framework import serializers
from .models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyReward, 
    LoyaltyVoucher, LoyaltyBadge, LoyaltyEarningRule
)

class LoyaltyPointsSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = LoyaltyPoints
        fields = [
            'id', 'user_id', 'points_balance', 'lifetime_points',
            'tier', 'tier_updated_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at', 'tier_updated_at']

class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'user_id', 'points_change', 'transaction_type',
            'reference_type', 'reference_id', 'description',
            'points_balance_after', 'created_at',
        ]
        read_only_fields = ['user_id', 'created_at']

class LoyaltyRewardSerializer(serializers.ModelSerializer):
    can_redeem_more = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyReward
        fields = '__all__'

    from drf_spectacular.utils import extend_schema_field
    @extend_schema_field(serializers.BooleanField())
    def get_can_redeem_more(self, obj):
        if not obj.max_redemptions_per_user:
            return True
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return True
        count = LoyaltyVoucher.objects.filter(user=request.user, reward=obj).count()
        return count < obj.max_redemptions_per_user

class LoyaltyVoucherSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    reward_id = serializers.UUIDField(source='reward.id', read_only=True)
    reward_name = serializers.CharField(source='reward.name', read_only=True)

    reward_type = serializers.CharField(source='discount_type', read_only=True)

    order_id = serializers.SerializerMethodField()

    from drf_spectacular.utils import extend_schema_field
    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_order_id(self, obj):
        return str(obj.order_id) if obj.order_id else None

    class Meta:
        model = LoyaltyVoucher
        fields = [
            'id', 'user_id', 'reward_id', 'reward_name', 'voucher_code',
            'points_spent', 'discount_type', 'reward_type', 'discount_value',
            'minimum_order_amount', 'status', 'redeemed_at', 'expires_at',
            'used_at', 'order_id', 'created_at',
        ]
        read_only_fields = [
            'user_id', 'reward_id', 'voucher_code', 'created_at',
            'redeemed_at', 'expires_at', 'reward_name', 'reward_type', 'order_id',
        ]

class LoyaltyBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyBadge
        fields = '__all__'

class RedeemRewardSerializer(serializers.Serializer):
    reward_id = serializers.UUIDField()
