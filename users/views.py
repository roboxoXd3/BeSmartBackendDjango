from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, UserSerializer, ProfileSerializer, LogoutSerializer,
    LoginSerializer, PasswordResetSerializer, PasswordChangeSerializer,
    ProfilePhotoUploadSerializer
)
from drf_spectacular.utils import extend_schema, inline_serializer
from django.conf import settings
from django.core.files.storage import storages

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
import os
import uuid
from besmart_backend.utils.logger import get_logger

logger = get_logger(__name__)

User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),
    }

class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register User (Native Django)",
        request=RegisterSerializer,
        responses={201: UserSerializer},
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')

        if not email or not password:
             return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Sign up with Django Native
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name
            )
            
            logger.info("user_registered", user_id=user.id)
            tokens = get_tokens_for_user(user)
            
            return Response({
                "message": "Registration successful.",
                "user": {"id": user.id, "email": user.email},
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login User (Native Django)",
        request=LoginSerializer,
        responses={200: inline_serializer(name="LoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "access_token": serializers.CharField(), "refresh_token": serializers.CharField()})},
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            logger.info("user_login_success", user_id=user.id)
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Login successful.",
                "user": {"id": user.id, "email": user.email},
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"]
            }, status=status.HTTP_200_OK)
        else:
            logger.warning("user_login_failed", reason="invalid_credentials")
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

class VendorLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Vendor specific login",
        request=LoginSerializer,
        responses={200: inline_serializer(name="VendorLoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "access_token": serializers.CharField(), "refresh_token": serializers.CharField()})},
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            from vendors.models import Vendor
            vendor = Vendor.objects.filter(user=user).first()
            if not vendor:
                logger.warning("vendor_login_failed", user_id=user.id, reason="not_a_vendor")
                return Response({"error": "This account is not registered as a vendor."}, status=status.HTTP_403_FORBIDDEN)
                
            logger.info("vendor_login_success", user_id=user.id, vendor_id=vendor.id)
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Vendor login successful.",
                "user": {
                    "id": user.id, 
                    "email": user.email, 
                    "vendor_id": vendor.id, 
                    "vendor_status": vendor.status
                },
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"]
            }, status=status.HTTP_200_OK)
        else:
            logger.warning("vendor_login_failed", reason="invalid_credentials")
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

class AdminLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Admin specific login",
        request=LoginSerializer,
        responses={200: inline_serializer(name="AdminLoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "access_token": serializers.CharField(), "refresh_token": serializers.CharField()})},
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.is_staff:
                logger.warning("admin_login_failed", user_id=user.id, reason="not_an_admin")
                return Response({"error": "This account does not have admin privileges."}, status=status.HTTP_403_FORBIDDEN)
                
            logger.info("admin_login_success", user_id=user.id)
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Admin login successful.",
                "user": {
                    "id": user.id, 
                    "email": user.email, 
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser
                },
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"]
            }, status=status.HTTP_200_OK)
        else:
            logger.warning("admin_login_failed", reason="invalid_credentials")
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Logout User (Blacklist Token)",
        responses={200: inline_serializer(name="LogoutResponse", fields={"message": serializers.CharField()})},
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except TokenError as e:
            # Also fine if token is already blacklisted
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetSerializer

    @extend_schema(
        summary="Request Password Reset Link",
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        # redirect_to = serializer.validated_data.get('redirect_to')

        try:
            user = User.objects.get(email=email)
            # In a real app we would generate a token and send an email.
            # Here we just log it to console or pretend we sent it.
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Just simulating for now to avoid SMTP setup
            logger.info("password_reset_requested", uid=uid, token=token, user_id=user.id)
            
            return Response({"message": "If an account exists, a password reset email has been sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # We don't want to leak whether the user exists or not
            return Response({"message": "If an account exists, a password reset email has been sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        summary="Change Password (LoggedIn User)",
        deprecated=True,
        description="DEPRECATED: We are using Supabase for all authentication. Do not use this native Django endpoint."
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_password = serializer.validated_data['password']

        try:
            user = request.user
            user.set_password(new_password)
            user.save()
            logger.info("password_changed", user_id=user.id)
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProfileSerializer # Or a specific update serializer
        return UserSerializer

    @extend_schema(summary="Get current user profile")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update current user profile")
    def patch(self, request, *args, **kwargs):
        instance = self.request.user.profile
        serializer = ProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        user_serializer = UserSerializer(self.request.user)
        return Response(user_serializer.data)


class AccountDeletionEligibilityView(APIView):
    """GET /api/users/account/deletion-eligibility/"""
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        summary="Check if account can be deleted",
        responses={200: inline_serializer(name="AccountDeletionEligibilityRes", fields={"eligible": serializers.BooleanField(), "message": serializers.CharField(), "is_vendor": serializers.BooleanField(), "error_code": serializers.CharField(required=False)})}
    )
    def get(self, request):
        from vendors.models import Vendor
        vendor = Vendor.objects.filter(user=request.user, status='approved').first()
        if vendor:
            return Response({
                "eligible": False,
                "message": "Cannot delete account while you have an active vendor account. Please contact support.",
                "is_vendor": True,
                "error_code": "vendor_active"
            })
        return Response({
            "eligible": True,
            "message": "Your account is eligible for deletion.",
            "is_vendor": False
        })


class AccountDeleteView(APIView):
    """POST /api/users/account/delete/ — requires password"""
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        summary="Delete Account",
        request=inline_serializer(name="AccountDeleteReq", fields={"password": serializers.CharField()}), 
        responses={200: inline_serializer(name="AccountDeleteRes", fields={"success": serializers.BooleanField(), "message": serializers.CharField()})}
    )
    def post(self, request):
        from vendors.models import Vendor
        password = request.data.get('password', '')
        if not password:
            return Response({"success": False, "error": "invalid_password", "message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        vendor = Vendor.objects.filter(user=request.user, status='approved').first()
        if vendor:
            return Response({"success": False, "error": "vendor_active", "message": "Cannot delete account with active vendor."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify password natively
        user = authenticate(request, username=request.user.email, password=password)
        if user is None:
            return Response({"success": False, "error": "invalid_password", "message": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            if hasattr(user, 'profile'):
                user.profile.delete()
            user.email = f"deleted_{user.id}@deleted.local"
            user.username = user.email
            user.is_active = False
            user.save()
            logger.info("account_deleted", user_id=user.id)
            # No Supabase call needed anymore
        except Exception as e:
            return Response({"success": False, "error": "deletion_failed", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"success": True, "message": "Your account has been successfully deleted."})

class ProfilePhotoUploadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfilePhotoUploadSerializer

    @extend_schema(
        summary="Upload User Profile Photo",
        description="Uploads an image file to Cloudflare R2 avatars storage, updates the user's profile image path, and returns the updated profile info.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'The profile photo image file'
                    }
                },
                'required': ['file']
            }
        },
        responses={
            200: inline_serializer(
                name="ProfilePhotoUploadResponse",
                fields={
                    "message": serializers.CharField(),
                    "image_url": serializers.CharField(),
                    "profile": ProfileSerializer(),
                }
            ),
            400: inline_serializer(
                name="ProfilePhotoUploadError",
                fields={
                    "error": serializers.CharField(),
                }
            )
        }
    )
    def post(self, request):
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        
        # Determine the file extension and validate
        _, ext = os.path.splitext(uploaded_file.name)
        ext = ext.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            return Response({"error": "Unsupported image format. Allowed formats: JPG, JPEG, PNG, WEBP, GIF."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get avatars storage
            avatar_storage = storages['avatars']
            
            # Generate a unique path/filename under the user's namespace to avoid CDN caching issues
            unique_id = uuid.uuid4().hex[:8]
            file_name = f"{request.user.id}/avatar_{unique_id}{ext}"
            
            # Get or create profile defensively
            from .models import Profile
            profile, created = Profile.objects.get_or_create(id=request.user)
            
            # If the profile already has an image, attempt to delete the old one
            if profile.image_path:
                try:
                    import re
                    # Look for the path after "/avatars/" to match R2 location folder structure
                    match = re.search(r'/avatars/(.+)$', profile.image_path)
                    if match:
                        old_relative_path = match.group(1)
                        if avatar_storage.exists(old_relative_path):
                            avatar_storage.delete(old_relative_path)
                except Exception as ex:
                    # Non-blocking: just log or ignore deletion errors so the upload succeeds
                    logger.warning("avatar_deletion_failed", image_path=profile.image_path, error=str(ex))
            
            # Save the file to storage (Cloudflare R2)
            saved_name = avatar_storage.save(file_name, uploaded_file)
            
            # Generate public URL
            file_url = avatar_storage.url(saved_name)
            
            # Update user's profile image path
            profile.image_path = file_url
            profile.save(update_fields=['image_path', 'updated_at'])
            
            logger.info("profile_photo_uploaded", user_id=request.user.id, file_url=file_url)
            
            # Return response
            profile_serializer = ProfileSerializer(profile)
            return Response({
                "message": "Profile photo uploaded successfully.",
                "image_url": file_url,
                "profile": profile_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Failed to upload profile photo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

