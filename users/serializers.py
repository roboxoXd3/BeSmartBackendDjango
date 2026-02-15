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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False) # Optional because Supabase client might just clear storage

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    redirect_to = serializers.CharField(required=False, allow_blank=True)

class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
