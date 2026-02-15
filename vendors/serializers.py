from rest_framework import serializers
from .models import (
    Vendor, VendorReview, VendorBankAccount, VendorPayout, 
    PayoutTransaction, SubscriptionPlan, VendorSubscription, 
    VendorSizeChartTemplate, VendorFollow
)
from users.serializers import UserSerializer

class VendorBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBankAccount
        fields = '__all__'
        read_only_fields = ['vendor']

    def validate(self, attrs):
        # Validate account with Squad
        from payments.services.squad_service import SquadTransferService
        
        bank_code = attrs.get('bank_code')
        account_number = attrs.get('account_number')
        
        # If updating and fields not provided, skip or fetch from instance (not fully handled here for updates yet)
        # Assuming creation mostly or full update
        if bank_code and account_number:
            service = SquadTransferService()
            result = service.lookup_account(bank_code, account_number)
            
            if not result['success']:
                raise serializers.ValidationError(f"Invalid bank account: {result.get('message')}")
            
            # Auto-fill account name if not provided or ensure it matches
            # attrs['account_name'] = result['account_name'] # Could force overwrite
            if 'account_name' not in attrs:
                 attrs['account_name'] = result['account_name']
        
        return attrs

class VendorListSerializer(serializers.ModelSerializer):
    """Lightweight for customer-facing list/featured/search."""
    class Meta:
        model = Vendor
        fields = [
            'id', 'business_name', 'business_description', 'business_logo',
            'average_rating', 'total_reviews', 'is_featured'
        ]


class VendorDetailSerializer(serializers.ModelSerializer):
    """Detail for customer vendor profile (no sensitive data)."""
    follower_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'id', 'business_name', 'business_description', 'business_logo',
            'business_email', 'business_phone', 'business_address',
            'average_rating', 'total_reviews', 'is_featured', 'created_at',
            'follower_count',
        ]

    def get_follower_count(self, obj):
        return obj.followers.count()


class VendorSerializer(serializers.ModelSerializer):
    bank_accounts = VendorBankAccountSerializer(many=True, read_only=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at', 
            'average_rating', 'total_reviews', 'total_sales', 
            'total_orders', 'verification_status', 'commission_rate',
            'last_login_at', 'admin_notes', 'user'
        ]

class VendorRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'business_name', 'business_email', 'business_phone', 
            'business_address', 'business_type', 'business_description',
            'business_logo'
        ]

class VendorReviewSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = VendorReview
        fields = '__all__'
        read_only_fields = ['user', 'vendor', 'created_at', 'updated_at']


class VendorReviewCreateSerializer(serializers.ModelSerializer):
    """Create review - only rating and review_text from customer."""
    class Meta:
        model = VendorReview
        fields = ['rating', 'review_text']
        extra_kwargs = {
            'rating': {'min_value': 1, 'max_value': 5},
            'review_text': {'required': False, 'allow_blank': True},
        }

class PayoutTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutTransaction
        fields = '__all__'

class VendorPayoutSerializer(serializers.ModelSerializer):
    transactions = PayoutTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = VendorPayout
        fields = '__all__'
        read_only_fields = ['vendor', 'status', 'processed_at', 'completed_at', 'admin_notes', 'failure_reason', 'requested_at']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class VendorSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='subscription_plan', read_only=True)

    class Meta:
        model = VendorSubscription
        fields = '__all__'
        read_only_fields = ['vendor', 'status', 'started_at', 'expires_at', 'created_at', 'updated_at']

class VendorSizeChartTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorSizeChartTemplate
        fields = '__all__'
        read_only_fields = [
            'vendor', 'approval_status', 'approved_by', 'approved_at', 
            'rejection_reason', 'created_at', 'updated_at', 'migration_completed_at'
        ]
