from rest_framework import serializers
from .models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyReward, 
    LoyaltyVoucher, LoyaltyBadge, LoyaltyEarningRule
)

class LoyaltyPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyPoints
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'tier_updated_at']

class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class LoyaltyRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyReward
        fields = '__all__'

class LoyaltyVoucherSerializer(serializers.ModelSerializer):
    reward_name = serializers.CharField(source='reward.name', read_only=True)
    
    class Meta:
        model = LoyaltyVoucher
        fields = '__all__'
        read_only_fields = ['user', 'voucher_code', 'created_at', 'redeemed_at', 'expires_at', 'reward_name']

class LoyaltyBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyBadge
        fields = '__all__'

class RedeemRewardSerializer(serializers.Serializer):
    reward_id = serializers.UUIDField()
