from rest_framework import serializers
from rest_framework.validators import UniqueValidator
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
        extra_kwargs = {'password_hash': {'write_only': True}}

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

def check_can_manage_user(caller, target):
    """
    Staff can manage customers and vendors. Superusers and other staff accounts
    (and your own account) can only be changed by a superuser.
    """
    from rest_framework.exceptions import PermissionDenied
    if caller.is_superuser:
        if caller.pk == target.pk:
            raise PermissionDenied("You can't change your own account here.")
        return
    if target.is_superuser or target.is_staff:
        raise PermissionDenied("Only a superuser can manage admin accounts.")


class UserAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Admin create/update of a user. Supabase Auth is the source of truth for
    logins, so the Supabase user is created/updated first (service-role key)
    and Django mirrors it with the same id.
    """
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), lookup='iexact', message="A user with this email already exists.")],
        help_text="Required on create. Changing it also changes the Supabase login email (no confirmation email is sent).",
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, help_text="Sets the Supabase login password. On create, omit it to create a user that must use the password-reset flow.")
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[('customer', 'Customer'), ('vendor', 'Vendor'), ('admin', 'Admin')], write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'is_active', 'first_name', 'last_name', 'phone_number', 'role']
        read_only_fields = ['id']

    def validate(self, attrs):
        if self.instance is None and not attrs.get('email'):
            raise serializers.ValidationError({"email": ["This field is required."]})
        request = self.context.get('request')
        caller = getattr(request, 'user', None)
        if self.instance is not None and caller is not None:
            check_can_manage_user(caller, self.instance)
        # An email listed in admin_users makes its owner staff on their next request.
        if attrs.get('email') and caller is not None and not caller.is_superuser:
            if AdminUser.objects.filter(email__iexact=attrs['email'], is_active=True).exists():
                raise serializers.ValidationError({"email": ["This email belongs to an admin account; only a superuser can assign it."]})
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from users.models import Profile
        from users.supabase_gateway import call_supabase, SupabaseAuthError

        password = validated_data.pop('password', None)
        phone_number = validated_data.pop('phone_number', None)
        role = validated_data.pop('role', 'customer')
        email = validated_data['email']
        full_name = f"{validated_data.get('first_name', '')} {validated_data.get('last_name', '')}".strip()

        attributes = {
            "email": email,
            "email_confirm": True,
            # The on_auth_user_created trigger copies full_name and role into profiles.
            "user_metadata": {"full_name": full_name, "phone_number": phone_number or "", "role": role},
        }
        if password:
            attributes["password"] = password
        supabase_user = call_supabase(
            "admin_user_create",
            lambda supabase: supabase.auth.admin.create_user(attributes),
            admin=True,
            client_error_status=400,
        ).user

        try:
            with transaction.atomic():
                validated_data.setdefault('username', email)
                user = User(id=supabase_user.id, **validated_data)
                user.set_unusable_password()
                user.save()
                Profile.objects.update_or_create(id=user, defaults={
                    'phone_number': phone_number,
                    'role': role,
                    'full_name': full_name,
                })
        except Exception:
            # Don't leave a Supabase login (or the profile row its trigger inserted) behind.
            try:
                call_supabase("admin_user_create_rollback", lambda supabase: supabase.auth.admin.delete_user(str(supabase_user.id)), admin=True)
            except SupabaseAuthError:
                pass
            Profile.objects.filter(pk=supabase_user.id).delete()
            raise

        return user

    def update(self, instance, validated_data):
        from django.db import transaction
        from users.supabase_gateway import call_supabase, SupabaseAuthError

        password = validated_data.pop('password', None)
        phone_number = validated_data.pop('phone_number', None)
        role = validated_data.pop('role', None)

        supabase_changes = {}
        if password:
            supabase_changes["password"] = password
        old_email = instance.email
        new_email = validated_data.get('email')
        email_changed = bool(new_email) and new_email.lower() != (old_email or '').lower()
        if email_changed:
            supabase_changes.update(email=new_email, email_confirm=True)
            # Keep username == email so a later sign-up with the old email doesn't collide.
            validated_data['username'] = new_email
        if supabase_changes:
            try:
                call_supabase(
                    "admin_user_update",
                    lambda supabase: supabase.auth.admin.update_user_by_id(str(instance.id), supabase_changes),
                    admin=True,
                    client_error_status=400,
                )
            except SupabaseAuthError as e:
                if e.supabase_code == "user_not_found":
                    raise SupabaseAuthError(
                        "This user only exists in Django and has no Supabase login, so its email/password can't be changed.",
                        400, e.supabase_code,
                    )
                raise

        try:
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
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
        except Exception:
            if email_changed:
                # Put the Supabase login email back so both sides still agree.
                try:
                    call_supabase(
                        "admin_user_update_revert",
                        lambda supabase: supabase.auth.admin.update_user_by_id(str(instance.id), {"email": old_email, "email_confirm": True}),
                        admin=True,
                    )
                except SupabaseAuthError:
                    pass
            raise

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
