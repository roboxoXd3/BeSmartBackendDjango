from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, UserSerializer, ProfileSerializer, LogoutSerializer,
    LoginSerializer, PasswordResetSerializer, PasswordChangeSerializer,
    ProfilePhotoUploadSerializer, TokenRefreshSerializer, TokenRefreshResponseSerializer, AuthTokensSerializer,
    LoginResponseSerializer, VendorLoginResponseSerializer, AdminLoginResponseSerializer,
    AuthErrorSerializer,
)
from .authentication import get_supabase_client, sync_supabase_user
from supabase import AuthApiError
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
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

def _session_tokens(session):
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": session.token_type or "bearer",
        "expires_in": session.expires_in,
        "expires_at": session.expires_at,
    }


# Supabase error codes -> the message we show. Anything unlisted gets the default,
# so raw Supabase messages never reach the client (they're still logged).
AUTH_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid email or password.",
    "email_not_confirmed": "Please confirm your email address before logging in.",
    "user_banned": "This account has been disabled.",
    "refresh_token_not_found": "Session expired. Please log in again.",
    "refresh_token_already_used": "Session expired. Please log in again.",
    "session_not_found": "Session expired. Please log in again.",
}
DEFAULT_AUTH_ERROR = "Authentication failed."


def _supabase_auth_call(event, fn):
    """
    Run a Supabase Auth call and translate its failures into the Response the
    frontend should see. Returns (auth_response, None) or (None, Response).
    """
    try:
        supabase = get_supabase_client()
    except ValueError as e:
        logger.error(f"{event}_misconfigured", error=str(e))
        return None, Response({"error": "Authentication service is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        auth_response = fn(supabase)
    except AuthApiError as e:
        code = getattr(e, "code", None)
        upstream_status = getattr(e, "status", None) or 400
        logger.warning(f"{event}_failed", reason=code or "auth_api_error", upstream_status=upstream_status, error=str(e))
        if upstream_status == 429:
            return None, Response({"error": "Too many attempts. Please wait a moment and try again."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if upstream_status >= 500:
            return None, Response({"error": "Authentication service is unavailable. Please try again."}, status=status.HTTP_502_BAD_GATEWAY)
        return None, Response({"error": AUTH_ERROR_MESSAGES.get(code, DEFAULT_AUTH_ERROR)}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logger.error(f"{event}_error", error=str(e), error_type=type(e).__name__)
        return None, Response({"error": "Authentication service is unavailable. Please try again."}, status=status.HTTP_502_BAD_GATEWAY)

    if not auth_response.user or not auth_response.session:
        logger.warning(f"{event}_failed", reason="no_session")
        return None, Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

    return auth_response, None


def supabase_sign_in(event, email, password):
    """Proxy email/password sign-in to Supabase Auth and mirror the user into Django."""
    auth_response, error = _supabase_auth_call(
        event,
        lambda supabase: supabase.auth.sign_in_with_password({"email": email, "password": password}),
    )
    if error:
        return None, None, error

    try:
        user = sync_supabase_user(auth_response.user)
    except IntegrityError as e:
        # A Django user already owns this email/username under a different id
        # (e.g. one created by the deprecated native RegisterView).
        logger.error(f"{event}_user_sync_conflict", supabase_user_id=str(auth_response.user.id), error=str(e))
        return None, None, Response(
            {"error": "This account conflicts with an existing user record. Please contact support."},
            status=status.HTTP_409_CONFLICT,
        )
    return user, auth_response.session, None


LOGIN_ERROR_RESPONSES = {
    400: OpenApiResponse(
        response=inline_serializer(name="LoginValidationError", fields={
            "email": serializers.ListField(child=serializers.CharField(), required=False),
            "password": serializers.ListField(child=serializers.CharField(), required=False),
        }),
        description="Validation error (missing/invalid email or password), keyed by field.",
    ),
    401: OpenApiResponse(response=AuthErrorSerializer, description="Invalid credentials, or Supabase rejected the sign-in (e.g. email not confirmed, user banned)."),
    409: OpenApiResponse(response=AuthErrorSerializer, description="The Supabase user conflicts with an existing Django user record (same email, different id)."),
    429: OpenApiResponse(response=AuthErrorSerializer, description="Supabase Auth rate limit reached. Retry after a short wait."),
    502: OpenApiResponse(response=AuthErrorSerializer, description="Supabase Auth could not be reached."),
    503: OpenApiResponse(response=AuthErrorSerializer, description="Supabase credentials are not configured on the server."),
}


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["auth"],
        summary="Login User (Proxy to Supabase Auth)",
        description=(
            "Signs the user in against Supabase Auth with email + password and returns the Supabase session. "
            "The backend acts as a BFF: the frontend never talks to Supabase directly. "
            "Use `access_token` as `Authorization: Bearer <token>` on every other API call, and exchange "
            "`refresh_token` at `POST /api/auth/token/refresh/` before `expires_at`."
        ),
        request=LoginSerializer,
        responses={200: LoginResponseSerializer, **LOGIN_ERROR_RESPONSES},
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session, error = supabase_sign_in(
            "user_login", serializer.validated_data['email'], serializer.validated_data['password']
        )
        if error:
            return error

        logger.info("user_login_success", user_id=str(user.id))
        return Response({
            "message": "Login successful.",
            "user": {"id": user.id, "email": user.email},
            **_session_tokens(session),
        }, status=status.HTTP_200_OK)

class VendorLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["auth"],
        summary="Vendor Login (Proxy to Supabase Auth)",
        description=(
            "Same as `POST /api/auth/login/`, but only succeeds if the Supabase user has a vendor account. "
            "Returns 403 for valid credentials that do not belong to a vendor."
        ),
        request=LoginSerializer,
        responses={
            200: VendorLoginResponseSerializer,
            **LOGIN_ERROR_RESPONSES,
            403: OpenApiResponse(response=AuthErrorSerializer, description="Credentials are valid but the account is not registered as a vendor."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session, error = supabase_sign_in(
            "vendor_login", serializer.validated_data['email'], serializer.validated_data['password']
        )
        if error:
            return error

        from vendors.models import Vendor
        vendor = Vendor.objects.filter(user=user).first()
        if not vendor:
            logger.warning("vendor_login_failed", user_id=str(user.id), reason="not_a_vendor")
            return Response({"error": "This account is not registered as a vendor."}, status=status.HTTP_403_FORBIDDEN)

        logger.info("vendor_login_success", user_id=str(user.id), vendor_id=str(vendor.id))
        return Response({
            "message": "Vendor login successful.",
            "user": {
                "id": user.id,
                "email": user.email,
                "vendor_id": vendor.id,
                "vendor_status": vendor.status
            },
            **_session_tokens(session),
        }, status=status.HTTP_200_OK)

class AdminLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["auth"],
        summary="Admin Login (Proxy to Supabase Auth)",
        description=(
            "Same as `POST /api/auth/login/`, but only succeeds for admins. Admin status is taken from an active "
            "row in `admin_users` (matched by email) or Django superuser, and is synced to `is_staff` on login. "
            "Returns 403 for valid credentials that do not belong to an admin."
        ),
        request=LoginSerializer,
        responses={
            200: AdminLoginResponseSerializer,
            **LOGIN_ERROR_RESPONSES,
            403: OpenApiResponse(response=AuthErrorSerializer, description="Credentials are valid but the account does not have admin privileges."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session, error = supabase_sign_in(
            "admin_login", serializer.validated_data['email'], serializer.validated_data['password']
        )
        if error:
            return error

        if not user.is_staff:
            logger.warning("admin_login_failed", user_id=str(user.id), reason="not_an_admin")
            return Response({"error": "This account does not have admin privileges."}, status=status.HTTP_403_FORBIDDEN)

        logger.info("admin_login_success", user_id=str(user.id))
        return Response({
            "message": "Admin login successful.",
            "user": {
                "id": user.id,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser
            },
            **_session_tokens(session),
        }, status=status.HTTP_200_OK)

class TokenRefreshView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = TokenRefreshSerializer

    @extend_schema(
        tags=["auth"],
        summary="Refresh Session (Proxy to Supabase Auth)",
        description=(
            "Exchanges a Supabase `refresh_token` (from any login endpoint or a previous refresh) for a new "
            "Supabase session. Refresh tokens rotate: always store the new `refresh_token` (the old one is rejected after Supabase's short reuse window). The response also includes `access`/`refresh` aliases for clients built against the old SimpleJWT endpoint. "
            "`refresh` is accepted as an alias of `refresh_token`."
        ),
        request=TokenRefreshSerializer,
        responses={
            200: TokenRefreshResponseSerializer,
            400: OpenApiResponse(response=AuthErrorSerializer, description="No refresh token supplied."),
            401: OpenApiResponse(response=AuthErrorSerializer, description="Refresh token is invalid, expired or already used."),
            429: OpenApiResponse(response=AuthErrorSerializer, description="Supabase Auth rate limit reached. Retry after a short wait."),
            502: OpenApiResponse(response=AuthErrorSerializer, description="Supabase Auth could not be reached."),
            503: OpenApiResponse(response=AuthErrorSerializer, description="Supabase credentials are not configured on the server."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh_token') or serializer.validated_data.get('refresh')
        if not refresh_token:
            return Response({"error": "refresh_token is required."}, status=status.HTTP_400_BAD_REQUEST)

        auth_response, error = _supabase_auth_call(
            "token_refresh", lambda supabase: supabase.auth.refresh_session(refresh_token)
        )
        if error:
            return error

        tokens = _session_tokens(auth_response.session)
        return Response({**tokens, "access": tokens["access_token"], "refresh": tokens["refresh_token"]}, status=status.HTTP_200_OK)

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
            logger.info("password_reset_requested", user_id=user.id)
            
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
        logger.info("profile_update_started")
        instance = self.request.user.profile
        serializer = ProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info("profile_updated")
        
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
        logger.info("account_deletion_started")
        if not password:
            return Response({"success": False, "error": "invalid_password", "message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        vendor = Vendor.objects.filter(user=request.user, status='approved').first()
        if vendor:
            logger.warning("account_deletion_rejected", reason="vendor_active", vendor_id=vendor.id)
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
        logger.info("profile_photo_upload_started")
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
            
            logger.info("profile_photo_uploaded", file_url=file_url)
            
            # Return response
            profile_serializer = ProfileSerializer(profile)
            return Response({
                "message": "Profile photo uploaded successfully.",
                "image_url": file_url,
                "profile": profile_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"Failed to upload profile photo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

