from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone_number', 'image_path', 'role', 'is_deleted']
        read_only_fields = ['role', 'is_deleted']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['id', 'is_active', 'date_joined']

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email to register in Supabase Auth.")
    password = serializers.CharField(write_only=True, help_text="Password (Supabase password rules apply, min 6 characters by default).")
    full_name = serializers.CharField(required=False, allow_blank=True, help_text="Stored on the user's profile.")
    first_name = serializers.CharField(required=False, allow_blank=True, help_text="Legacy alias used as full_name when full_name is not sent.")
    phone_number = serializers.CharField(required=False, allow_blank=True, help_text="Stored on the user's profile.")
    redirect_to = serializers.URLField(required=False, help_text="Where the email-confirmation link should send the user. Must be in Supabase's allowed redirect URLs; defaults to the Supabase Site URL.")

class RegisterResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = serializers.DictField(help_text="`{id, email}` of the new Supabase user.")
    email_confirmation_required = serializers.BooleanField(help_text="True when the user must confirm their email before logging in; tokens are then null.")
    access_token = serializers.CharField(allow_null=True)
    refresh_token = serializers.CharField(allow_null=True)
    token_type = serializers.CharField(allow_null=True)
    expires_in = serializers.IntegerField(allow_null=True)
    expires_at = serializers.IntegerField(allow_null=True)

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email of the Supabase Auth user.")
    password = serializers.CharField(write_only=True, help_text="Supabase Auth password.")

class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Supabase refresh_token returned by any login endpoint.")
    refresh = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Alias of refresh_token (kept for older clients).")

class AuthTokensSerializer(serializers.Serializer):
    access_token = serializers.CharField(help_text="Supabase access token (JWT). Send as `Authorization: Bearer <token>`.")
    refresh_token = serializers.CharField(help_text="Supabase refresh token. Exchange at /api/auth/token/refresh/.")
    token_type = serializers.CharField(help_text="Always `bearer`.")
    expires_in = serializers.IntegerField(help_text="Access token lifetime in seconds.")
    expires_at = serializers.IntegerField(allow_null=True, help_text="Access token expiry as a unix timestamp.")

class TokenRefreshResponseSerializer(AuthTokensSerializer):
    access = serializers.CharField(help_text="Alias of access_token (kept for older clients).")
    refresh = serializers.CharField(help_text="Alias of refresh_token (kept for older clients).")

class LoginUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()

class LoginResponseSerializer(AuthTokensSerializer):
    message = serializers.CharField()
    user = LoginUserSerializer()

class VendorLoginUserSerializer(LoginUserSerializer):
    vendor_id = serializers.UUIDField()
    vendor_status = serializers.CharField()

class VendorLoginResponseSerializer(AuthTokensSerializer):
    message = serializers.CharField()
    user = VendorLoginUserSerializer()

class AdminLoginUserSerializer(LoginUserSerializer):
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()

class AdminLoginResponseSerializer(AuthTokensSerializer):
    message = serializers.CharField()
    user = AdminLoginUserSerializer()

class AuthErrorSerializer(serializers.Serializer):
    error = serializers.CharField()

class LogoutSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(
        choices=["local", "global", "others"], required=False, default="local",
        help_text="`local` ends only this session, `global` ends every session of the user, `others` ends every session except this one.",
    )
    refresh = serializers.CharField(required=False, help_text="Ignored. Accepted for backwards compatibility.")

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email of the account to reset.")
    redirect_to = serializers.CharField(required=False, allow_blank=True, help_text="Page the reset link opens (your 'set new password' screen). Must be in Supabase's allowed redirect URLs; defaults to the Supabase Site URL.")

class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, help_text="The new password.")
    current_password = serializers.CharField(write_only=True, required=False, help_text="Optional. When sent, it is verified before the password is changed. Omit it in the reset-password flow, where the user doesn't know it.")

class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, help_text="The user's current password, to confirm the deletion.")

class ProfilePhotoUploadSerializer(serializers.Serializer):
    file = serializers.ImageField(help_text="The profile photo image file to upload.")

