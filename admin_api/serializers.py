from rest_framework import serializers
from .models import AdminUser, AdminActionLog, AppSettings
from users.serializers import UserSerializer
from users.models import User
from vendors.models import Vendor, VendorPayout, PayoutTransaction

class AdminUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = AdminUser
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_login_at']

class AdminActionLogSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)

    class Meta:
        model = AdminActionLog
        fields = '__all__'
        read_only_fields = ['created_at']

class AppSettingsSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.email', read_only=True)

    class Meta:
        model = AppSettings
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'updated_by']

class UserManagementSerializer(serializers.ModelSerializer):
    # Serializer for Admin to manage generic Users
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'email']

class VendorAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class PayoutAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = VendorPayout
        fields = '__all__'

class TransactionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutTransaction
        fields = '__all__'
