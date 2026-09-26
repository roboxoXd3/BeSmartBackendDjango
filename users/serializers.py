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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'phone_number']

    def create(self, validated_data):
        profile_data = {
            'full_name': validated_data.pop('full_name', ''),
            'phone_number': validated_data.pop('phone_number', '')
        }
        password = validated_data.pop('password')
        email = validated_data.get('email')
        
        # Username is same as email
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        Profile.objects.create(id=user, **profile_data)
        return user

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
    refresh = serializers.CharField(required=False) # Optional because Supabase client might just clear storage

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    redirect_to = serializers.CharField(required=False, allow_blank=True)

class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

class ProfilePhotoUploadSerializer(serializers.Serializer):
    file = serializers.ImageField(help_text="The profile photo image file to upload.")

