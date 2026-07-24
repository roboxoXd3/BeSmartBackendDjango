from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import AdminUser, AdminActionLog, AppSettings, AdminSession
from users.serializers import UserSerializer
from users.models import User
from vendors.models import Vendor, VendorPayout, PayoutTransaction
from orders.serializers import OrderSerializer
from orders.models import Order, OrderStatusHistory
from categories.models import Category, Subcategory
from loyalty.models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyBadge, LoyaltyReward, LoyaltyEarningRule
)
from products.models import Product
from vendors.models import VendorSizeChartTemplate
from support.models import ContactBranch

class LoyaltyBadgeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyBadge
        fields = '__all__'

class LoyaltyRewardAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyReward
        fields = '__all__'

class LoyaltyEarningRuleAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEarningRule
        fields = '__all__'

class AdminUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = AdminUser
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_login_at']

class AdminSessionSerializer(serializers.ModelSerializer):
    admin_user = AdminUserSerializer(source='admin', read_only=True)
    
    class Meta:
        model = AdminSession
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

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
    profile = serializers.SerializerMethodField()
    # Serializer for Admin to manage generic Users
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined', 'email']

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                "full_name": profile.full_name,
                "phone_number": profile.phone_number,
                "role": profile.role,
                "image_path": profile.image_path
            }
        except Exception:
            return None

class UserAdminCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[('customer', 'Customer'), ('vendor', 'Vendor'), ('admin', 'Admin')], write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'is_active', 'first_name', 'last_name', 'phone_number', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        phone_number = validated_data.pop('phone_number', None)
        role = validated_data.pop('role', 'customer')
        if 'username' not in validated_data and 'email' in validated_data:
            validated_data['username'] = validated_data['email']
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()

        # Profile creation/update
        from users.models import Profile
        Profile.objects.update_or_create(id=user, defaults={
            'phone_number': phone_number,
            'role': role,
            'full_name': f"{user.first_name} {user.last_name}".strip()
        })
        
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        phone_number = validated_data.pop('phone_number', None)
        role = validated_data.pop('role', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        # Profile update
        if phone_number is not None or role is not None:
            from users.models import Profile
            profile, _ = Profile.objects.get_or_create(id=instance)
            if phone_number is not None:
                profile.phone_number = phone_number
            if role is not None:
                profile.role = role
            profile.full_name = f"{instance.first_name} {instance.last_name}".strip()
            profile.save()

        return instance

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
        if hasattr(obj, 'product_count_annotated'):
            return obj.product_count_annotated
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id).count()

    def get_approved_products(self, obj):
        if hasattr(obj, 'approved_products_annotated'):
            return obj.approved_products_annotated
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id, approval_status='approved').count()

    def get_pending_products(self, obj):
        if hasattr(obj, 'pending_products_annotated'):
            return obj.pending_products_annotated
        from products.models import Product
        return Product.objects.filter(vendor_id=obj.id, approval_status='pending').count()

class PayoutAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    vendor_email = serializers.CharField(source='vendor.user.email', read_only=True)
    business_logo = serializers.CharField(source='vendor.business_logo', read_only=True)
    bank_details = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorPayout
        fields = '__all__'

    def get_bank_details(self, obj):
        bank = None
        if hasattr(obj.vendor, 'bank_accounts'):
            bank_accounts = obj.vendor.bank_accounts.all()
            if bank_accounts:
                bank = bank_accounts[0]
        if not bank:
            from vendors.models import VendorBankAccount
            bank = VendorBankAccount.objects.filter(vendor=obj.vendor).first()
        if bank:
            return {
                "bank_name": bank.bank_name,
                "account_name": bank.account_name,
                "account_number": bank.account_number,
                "bank_code": bank.bank_code
            }
        return None

class TransactionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutTransaction
        fields = '__all__'

class EscrowAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        from vendors.models import EscrowTransaction
        model = EscrowTransaction
        fields = '__all__'

class VendorBankAccountAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)

    class Meta:
        from vendors.models import VendorBankAccount
        model = VendorBankAccount
        fields = '__all__'

class SupportTicketAdminSerializer(serializers.ModelSerializer):
    vendor_business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    messages = serializers.SerializerMethodField()
    assigned_to_details = AdminUserSerializer(source='assigned_to', read_only=True)
    resolved_by_details = AdminUserSerializer(source='resolved_by', read_only=True)

    class Meta:
        from support.models import SupportTicket
        model = SupportTicket
        fields = '__all__'

    def get_messages(self, obj):
        from support.serializers import SupportMessageSerializer
        return SupportMessageSerializer(obj.messages.all().order_by('created_at'), many=True).data

class SupportMessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        from support.models import SupportMessage
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'sender', 'sender_role']

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
        try:
            ctx = self.context
            if 'product_vendor_map' in ctx and 'vendors_map' in ctx:
                product_vendor_map = ctx['product_vendor_map']
                vendors_map = ctx['vendors_map']
                vendors_dict = {}
                for item in obj.items.all():
                    vendor_id = product_vendor_map.get(item.product_id)
                    if vendor_id and vendor_id in vendors_map:
                        v = vendors_map[vendor_id]
                        if v.id not in vendors_dict:
                            vendors_dict[v.id] = {
                                "id": v.id,
                                "business_name": v.business_name,
                                "business_logo": v.business_logo
                            }
                if vendors_dict:
                    return list(vendors_dict.values())
                    
            # Fallback for when relations aren't context-cached
            from products.models import Product
            from vendors.models import Vendor
            product_ids = obj.items.values_list('product_id', flat=True)
            vendor_ids = Product.objects.filter(id__in=product_ids).values_list('vendor_id', flat=True).distinct()
            vendors = Vendor.objects.filter(id__in=[vid for vid in vendor_ids if vid])
            return [
                {
                    "id": v.id,
                    "business_name": v.business_name,
                    "business_logo": v.business_logo
                } for v in vendors
            ]
        except Exception as e:
            print("Error in get_vendors:", e)
            return []

class CategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SubcategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = '__all__'

class LoyaltyPointsAdminSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = LoyaltyPoints
        fields = '__all__'

class LoyaltyTransactionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'


class AdminProductDetailSerializer(serializers.ModelSerializer):
    """Admin can set vendor_id and approval_status (unlike vendor ProductDetailSerializer)."""
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'added_date']


class SizeChartAdminSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()
    vendor_email = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = VendorSizeChartTemplate
        fields = '__all__'

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_vendor_name(self, obj):
        return getattr(obj.vendor, 'business_name', None) if obj.vendor_id else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_vendor_email(self, obj):
        return getattr(obj.vendor, 'business_email', None) if obj.vendor_id else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_category_name(self, obj):
        return obj.category.name if getattr(obj, 'category_id', None) and obj.category else None


class ContactBranchAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactBranch
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderStatusHistoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'
        read_only_fields = ['id', 'order_id', 'previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
