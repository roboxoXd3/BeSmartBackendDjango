from rest_framework import serializers
from .models import AdminUser, AdminActionLog, AppSettings
from users.serializers import UserSerializer
from users.models import User
from vendors.models import Vendor, VendorPayout, PayoutTransaction
from orders.serializers import OrderSerializer
from orders.models import Order

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
    product_count = serializers.SerializerMethodField()
    approved_products = serializers.SerializerMethodField()
    pending_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_product_count(self, obj):
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id).count()

    def get_approved_products(self, obj):
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id, approval_status='approved').count()

    def get_pending_products(self, obj):
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id, approval_status='pending').count()

class PayoutAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = VendorPayout
        fields = '__all__'

class TransactionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutTransaction
        fields = '__all__'

class OrderAdminSerializer(OrderSerializer):
    customer = serializers.SerializerMethodField()
    vendors = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = '__all__'

    def get_customer(self, obj):
        try:
            user = obj.user
            if user:
                # Assumes profile might exist or user has these fields
                name = f"{user.first_name} {user.last_name}".strip()
                if not name:
                    name = getattr(user, 'email', '')
                phone = getattr(user, 'phone', None)
                if not phone and hasattr(user, 'profile'):
                    phone = user.profile.phone_number
                return {
                    "name": name,
                    "phone": phone,
                    "email": getattr(user, 'email', '')
                }
        except Exception:
            pass
        return None

    def get_vendors(self, obj):
        # Admin needs to see which vendors are involved in this order
        try:
            from products.models import Product
            # obj.items is the related_name for OrderItem
            product_ids = obj.items.values_list('product_id', flat=True)
            vendor_ids = Product.objects.filter(id__in=product_ids).values_list('vendor_id', flat=True).distinct()
            vendors = Vendor.objects.filter(id__in=[vid for vid in vendor_ids if vid])
            return [
                {
                    "id": v.id,
                    "business_name": v.business_name,
                    "logo_url": v.logo_url if hasattr(v, 'logo_url') else None
                } for v in vendors
            ]
        except Exception as e:
            print("Error in get_vendors:", e)
            return []
