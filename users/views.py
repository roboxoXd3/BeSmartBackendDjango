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
from supabase import create_client, Client
import os
import uuid

User = get_user_model()

# Initialize Supabase Client (Helper)
def get_supabase_client():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        raise ValueError("Supabase credentials not configured.")
    return create_client(url, key)

class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register User (Proxy to Supabase)",
        request=RegisterSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        # phone_number = request.data.get('phone_number', '') # Extract if needed

        if not email or not password:
             return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            supabase = get_supabase_client()
            # 1. Sign up with Supabase
            auth_response = supabase.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "data": {
                        "first_name": first_name,
                        # "phone_number": phone_number
                    }
                }
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if user_data:
                # Sync logic - Ensure username is set to avoid UniqueConstraint error
                user, created = User.objects.get_or_create(
                    id=user_data.id,
                    defaults={
                        'email': user_data.email, 
                        'first_name': first_name, 
                        'username': user_data.email  # Ensure username is set and unique
                    }
                )
                # If profile creation is needed beyond signals, do it here.

            return Response({
                "message": "Registration successful. Please check your email for verification.",
                "user": {"id": user_data.id, "email": user_data.email},
                "session": session_data # May be None if email confirm enabled
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login User (Proxy to Supabase)",
        request=LoginSerializer,
        responses={200: inline_serializer(name="LoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "session": serializers.DictField()})}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            supabase = get_supabase_client()
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if user_data:
                # Sync local user
                user, created = User.objects.get_or_create(
                    id=user_data.id,
                    defaults={
                        'email': user_data.email,
                        'username': user_data.email
                    }
                )
                
            return Response({
                "message": "Login successful.",
                "user": {"id": user_data.id, "email": user_data.email},
                "session": session_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class VendorLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Vendor specific login",
        request=LoginSerializer,
        responses={200: inline_serializer(name="VendorLoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "session": serializers.DictField()})}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            supabase = get_supabase_client()
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if user_data:
                # Sync local user
                user, created = User.objects.get_or_create(
                    id=user_data.id,
                    defaults={
                        'email': user_data.email,
                        'username': user_data.email
                    }
                )
                from vendors.models import Vendor
                vendor = Vendor.objects.filter(user=user).first()
                if not vendor:
                    return Response({"error": "This account is not registered as a vendor."}, status=status.HTTP_403_FORBIDDEN)
                
            return Response({
                "message": "Vendor logic successful.",
                "user": {
                    "id": user_data.id, 
                    "email": user_data.email, 
                    "vendor_id": vendor.id, 
                    "vendor_status": vendor.status
                },
                "session": session_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class AdminLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Admin specific login",
        request=LoginSerializer,
        responses={200: inline_serializer(name="AdminLoginResponse", fields={"message": serializers.CharField(), "user": serializers.DictField(), "session": serializers.DictField()})}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            supabase = get_supabase_client()
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            if user_data:
                # Sync local user
                user, created = User.objects.get_or_create(
                    id=user_data.id,
                    defaults={
                        'email': user_data.email,
                        'username': user_data.email
                    }
                )
                if not user.is_staff:
                    return Response({"error": "This account does not have admin privileges."}, status=status.HTTP_403_FORBIDDEN)
                
            return Response({
                "message": "Admin login successful.",
                "user": {
                    "id": user_data.id, 
                    "email": user_data.email, 
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser
                },
                "session": session_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Logout User (Invalidate Supabase Session)",
        responses={200: inline_serializer(name="LogoutResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        try:
            # We strictly proxy to Supabase for logout if possible.
            # Supabase server-side logout usually requires the access token.
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token = auth_header.split(' ')[1]
                supabase = get_supabase_client()
                # Attempt to sign out the user identified by the token
                # In supabase-py, invalidating a generic JWT might be via admin or just client sign_out if session set
                # For safety/simplicity in proxy:
                try:
                    supabase.auth.sign_out(scope='global', jwt=token)
                except:
                    # If this specific method fails (SDK difference), generic return is fallback
                    pass
            
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetSerializer

    @extend_schema(summary="Request Password Reset Link")
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        redirect_to = serializer.validated_data.get('redirect_to')

        try:
            supabase = get_supabase_client()
            options = {}
            if redirect_to:
                options['redirect_to'] = redirect_to
                
            supabase.auth.reset_password_email(email, options=options)
            
            return Response({"message": "If an account exists, a password reset email has been sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    @extend_schema(summary="Change Password (LoggedIn User)")
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_password = serializer.validated_data['password']

        try:
            # Extract token to use for Supabase update
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                 return Response({"error": "No Bearer token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            token = auth_header.split(' ')[1]
            
            supabase = get_supabase_client()
            # Update user using their JWT
            auth_response = supabase.auth.update_user({"password": new_password}, jwt=token)
            
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


class TokenRefreshView(APIView):
    """POST /api/users/token/refresh/ — refresh Supabase access token"""
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        summary="Refresh access token using refresh_token",
        request=inline_serializer(name="TokenRefreshReq", fields={"refresh_token": serializers.CharField()}),
        responses={200: inline_serializer(name="TokenRefreshRes", fields={"access_token": serializers.CharField(), "refresh_token": serializers.CharField(), "expires_in": serializers.IntegerField()})},
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            supabase = get_supabase_client()
            auth_response = supabase.auth.refresh_session(refresh_token)
            session = auth_response.session
            if session is None:
                return Response(
                    {"error": "Failed to refresh session."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return Response({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expires_in": session.expires_in,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


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
        try:
            auth_response = get_supabase_client().auth.sign_in_with_password({"email": request.user.email, "password": password})
            if not auth_response or not auth_response.user:
                return Response({"success": False, "error": "invalid_password", "message": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"success": False, "error": "invalid_password", "message": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = request.user
            if hasattr(user, 'profile'):
                user.profile.delete()
            user.email = f"deleted_{user.id}@deleted.local"
            user.username = user.email
            user.is_active = False
            user.save()
            get_supabase_client().auth.admin.delete_user(str(user.id))
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
                    print(f"DEBUG: Failed to delete old avatar {profile.image_path}: {ex}")
            
            # Save the file to storage (Cloudflare R2)
            saved_name = avatar_storage.save(file_name, uploaded_file)
            
            # Generate public URL
            file_url = avatar_storage.url(saved_name)
            
            # Update user's profile image path
            profile.image_path = file_url
            profile.save(update_fields=['image_path', 'updated_at'])
            
            # Return response
            profile_serializer = ProfileSerializer(profile)
            return Response({
                "message": "Profile photo uploaded successfully.",
                "image_url": file_url,
                "profile": profile_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Failed to upload profile photo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

