from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, RegisterResponseSerializer, MessageSerializer, UserSerializer, ProfileSerializer,
    LogoutSerializer, LoginSerializer, PasswordResetSerializer, PasswordChangeSerializer,
    AccountDeleteSerializer, ProfilePhotoUploadSerializer, TokenRefreshSerializer,
    TokenRefreshResponseSerializer, LoginResponseSerializer, VendorLoginResponseSerializer,
    AdminLoginResponseSerializer, AuthErrorSerializer,
)
from .authentication import sync_supabase_user
from .supabase_gateway import SupabaseAuthError, call_supabase
from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from django.conf import settings
from django.core.files.storage import storages

import base64
import json
import os
import uuid
from besmart_backend.utils.logger import get_logger

logger = get_logger(__name__)

User = get_user_model()


def _session_tokens(session):
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": session.token_type or "bearer",
        "expires_in": session.expires_in,
        "expires_at": session.expires_at,
    }


def _bearer_token(request):
    parts = request.headers.get('Authorization', '').split(' ')
    if len(parts) == 2 and parts[0].lower() == 'bearer' and parts[1]:
        return parts[1]
    return None


def _sync_user(event, supabase_user):
    """Mirror the Supabase user into Django; a conflicting Django row is a 409, not a 500."""
    try:
        return sync_supabase_user(supabase_user)
    except IntegrityError as e:
        # A Django user already owns this email/username under a different id
        # (e.g. one created by the old native register endpoint).
        logger.error(f"{event}_user_sync_conflict", supabase_user_id=str(supabase_user.id), error=str(e))
        raise SupabaseAuthError("This account conflicts with an existing user record. Please contact support.", 409)


def supabase_sign_in(event, email, password):
    """Proxy email/password sign-in to Supabase Auth and mirror the user into Django."""
    auth_response = call_supabase(
        event, lambda supabase: supabase.auth.sign_in_with_password({"email": email, "password": password})
    )
    if not auth_response.user or not auth_response.session:
        logger.warning(f"{event}_failed", reason="no_session")
        raise SupabaseAuthError("Invalid email or password.", 401)

    user = _sync_user(event, auth_response.user)
    if not user.is_active:
        logger.warning(f"{event}_failed", user_id=str(user.id), reason="inactive_user")
        raise SupabaseAuthError("This account has been disabled.", 403)
    return user, auth_response.session


def verify_password(event, user, password):
    """
    True if `password` is the Supabase password of `user`. The session the check
    creates is revoked straight away. Rate limits / outages still raise.
    """
    try:
        signed_in_user, session = supabase_sign_in(event, user.email, password)
    except SupabaseAuthError as e:
        if e.status_code in (401, 403, 409):
            return False
        raise
    try:
        call_supabase(f"{event}_signout", lambda supabase: supabase.auth.admin.sign_out(session.access_token, "local"))
    except SupabaseAuthError:
        pass
    return signed_in_user.id == user.id


# Sessions created from an emailed link (password reset, magic link, invite):
# the user can set a password without knowing the current one.
LINK_AUTH_METHODS = {"recovery", "otp", "magiclink", "invite"}


def _token_auth_methods(token):
    """`amr` methods of an access token that SupabaseAuthentication already validated."""
    try:
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        return {entry.get("method") for entry in claims.get("amr", []) if isinstance(entry, dict)}
    except (IndexError, ValueError):
        return set()


def _field_errors(name, fields, description):
    return OpenApiResponse(
        response=inline_serializer(name=name, fields={
            f: serializers.ListField(child=serializers.CharField(), required=False) for f in fields
        }),
        description=description,
    )


def _error(description):
    return OpenApiResponse(response=AuthErrorSerializer, description=description)


UPSTREAM_ERROR_RESPONSES = {
    429: _error("Supabase Auth rate limit reached. Retry after a short wait."),
    502: _error("Supabase Auth could not be reached."),
    503: _error("Supabase credentials are not configured on the server."),
}

LOGIN_ERROR_RESPONSES = {
    400: OpenApiResponse(
        response=inline_serializer(name="LoginValidationError", fields={
            "email": serializers.ListField(child=serializers.CharField(), required=False),
            "password": serializers.ListField(child=serializers.CharField(), required=False),
        }),
        description="Validation error (missing/invalid email or password), keyed by field.",
    ),
    401: _error("Invalid credentials, or Supabase rejected the sign-in (e.g. email not confirmed, user banned)."),
    409: _error("The Supabase user conflicts with an existing Django user record (same email, different id)."),
    **UPSTREAM_ERROR_RESPONSES,
}


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=["auth"],
        summary="Register User (Proxy to Supabase Auth)",
        description=(
            "Creates the user in Supabase Auth (the source of truth) and mirrors it into Django with the profile's "
            "`full_name` and `phone_number`. Email confirmation is enabled on the Supabase project, so the response "
            "normally has `email_confirmation_required: true` and null tokens: the user must click the link in the "
            "confirmation email, then log in via `POST /api/auth/login/`. If confirmation is ever disabled, the "
            "tokens are returned directly."
        ),
        request=RegisterSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: _error("Email already registered, or password too weak (Supabase's message is returned). Field validation errors are keyed by field instead, e.g. `{\"email\": [\"Enter a valid email address.\"]}`."),
            409: _error("The Supabase user conflicts with an existing Django user record."),
            **UPSTREAM_ERROR_RESPONSES,
        },
        auth=[],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        full_name = data.get('full_name') or data.get('first_name') or ''
        phone_number = data.get('phone_number') or ''

        # Refuse up front if Django already has this email (e.g. a legacy account with no
        # Supabase login); signing up first would leave an unusable Supabase user behind.
        if User.objects.filter(email__iexact=data['email']).exists():
            logger.warning("user_register_failed", reason="django_email_exists")
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        options = {"data": {"full_name": full_name, "phone_number": phone_number}}
        if data.get('redirect_to'):
            options["email_redirect_to"] = data['redirect_to']

        auth_response = call_supabase(
            "user_register",
            lambda supabase: supabase.auth.sign_up({"email": data['email'], "password": data['password'], "options": options}),
            client_error_status=400,
        )
        supabase_user = auth_response.user
        # With email confirmation on, Supabase hides "already registered" by returning
        # a fake user with no identities instead of an error.
        if not supabase_user or supabase_user.identities == []:
            logger.warning("user_register_failed", reason="email_exists")
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = _sync_user("user_register", supabase_user)
        except SupabaseAuthError:
            # Lost a race with another Django row for this email: don't leave the Supabase user behind.
            try:
                call_supabase("user_register_rollback", lambda supabase: supabase.auth.admin.delete_user(str(supabase_user.id)), admin=True)
            except SupabaseAuthError:
                pass
            raise
        # The on_auth_user_created trigger already inserted the profile row; fill in what it doesn't copy.
        from .models import Profile
        Profile.objects.update_or_create(id=user, defaults={'full_name': full_name, 'phone_number': phone_number})

        session = auth_response.session
        logger.info("user_registered", user_id=str(user.id), email_confirmation_required=session is None)
        return Response({
            "message": "Registration successful. Please check your email to confirm your account." if session is None else "Registration successful.",
            "user": {"id": user.id, "email": user.email},
            "email_confirmation_required": session is None,
            **(_session_tokens(session) if session else dict.fromkeys(
                ["access_token", "refresh_token", "token_type", "expires_in", "expires_at"])),
        }, status=status.HTTP_201_CREATED)


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
        responses={
            200: LoginResponseSerializer,
            **LOGIN_ERROR_RESPONSES,
            403: _error("The account has been suspended or deleted."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session = supabase_sign_in(
            "user_login", serializer.validated_data['email'], serializer.validated_data['password']
        )

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
            403: _error("Credentials are valid but the account is not a vendor, or it is suspended/deleted."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session = supabase_sign_in(
            "vendor_login", serializer.validated_data['email'], serializer.validated_data['password']
        )

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
            403: _error("Credentials are valid but the account is not an admin, or it is suspended/deleted."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, session = supabase_sign_in(
            "admin_login", serializer.validated_data['email'], serializer.validated_data['password']
        )

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
            "Supabase session. Refresh tokens rotate: always store the new `refresh_token` (the old one is rejected after Supabase's short reuse window). "
            "The response also includes `access`/`refresh` aliases for clients built against the old SimpleJWT endpoint. "
            "`refresh` is accepted as an alias of `refresh_token`."
        ),
        request=TokenRefreshSerializer,
        responses={
            200: TokenRefreshResponseSerializer,
            400: _error("No refresh token supplied."),
            401: _error("Refresh token is invalid, expired or already used."),
            403: _error("The account has been suspended or deleted."),
            409: _error("The Supabase user conflicts with an existing Django user record."),
            **UPSTREAM_ERROR_RESPONSES,
        },
        auth=[],
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh_token') or serializer.validated_data.get('refresh')
        if not refresh_token:
            return Response({"error": "refresh_token is required."}, status=status.HTTP_400_BAD_REQUEST)

        auth_response = call_supabase(
            "token_refresh", lambda supabase: supabase.auth.refresh_session(refresh_token)
        )
        if not auth_response.session:
            raise SupabaseAuthError("Session expired. Please log in again.", 401)
        if auth_response.user:
            user = _sync_user("token_refresh", auth_response.user)
            if not user.is_active:
                logger.warning("token_refresh_failed", user_id=str(user.id), reason="inactive_user")
                raise SupabaseAuthError("This account has been disabled.", 403)

        tokens = _session_tokens(auth_response.session)
        return Response({**tokens, "access": tokens["access_token"], "refresh": tokens["refresh_token"]}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=["auth"],
        summary="Logout User (Proxy to Supabase Auth)",
        description=(
            "Revokes the Supabase session of the access token in `Authorization: Bearer <token>`. Its refresh "
            "token stops working immediately, and the access token is rejected by this API from then on. "
            "Idempotent: an already-expired or already-revoked token still returns 200, so the client can "
            "always clear its stored tokens afterwards."
        ),
        request=LogoutSerializer,
        responses={
            200: MessageSerializer,
            400: _error("No `Authorization: Bearer <token>` header."),
            **UPSTREAM_ERROR_RESPONSES,
        },
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = _bearer_token(request)
        if not token:
            return Response({"error": "Authorization bearer token is required."}, status=status.HTTP_400_BAD_REQUEST)

        scope = serializer.validated_data['scope']
        try:
            call_supabase("user_logout", lambda supabase: supabase.auth.admin.sign_out(token, scope))
        except SupabaseAuthError as e:
            # Expired / already-revoked sessions are the normal case for a logout; only
            # rate limits and outages are worth reporting back.
            if e.status_code not in (401, 400):
                raise
        logger.info("user_logout", scope=scope)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = PasswordResetSerializer

    @extend_schema(
        tags=["auth"],
        summary="Request Password Reset Email (Proxy to Supabase Auth)",
        description=(
            "Asks Supabase to email a password-reset link. The link opens `redirect_to` with a recovery session "
            "(`access_token` in the URL fragment); the frontend then calls `POST /api/auth/password/change/` with "
            "that token as `Authorization: Bearer <token>` and the new `password`. Always returns the same "
            "message whether or not the account exists."
        ),
        request=PasswordResetSerializer,
        responses={
            200: MessageSerializer,
            400: _field_errors("PasswordResetValidationError", ["email", "redirect_to"], "Validation error (missing/invalid email), keyed by field."),
            **UPSTREAM_ERROR_RESPONSES,
        },
        auth=[],
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        options = {}
        if serializer.validated_data.get('redirect_to'):
            options["redirect_to"] = serializer.validated_data['redirect_to']

        try:
            call_supabase(
                "password_reset",
                lambda supabase: supabase.auth.reset_password_for_email(email, options),
                client_error_status=400,
            )
        except SupabaseAuthError as e:
            # Don't reveal whether the account exists. The per-email resend limit only
            # triggers for existing accounts, so it gets the same answer too.
            if e.status_code != 400 and e.supabase_code != "over_email_send_rate_limit":
                raise
        logger.info("password_reset_requested")
        return Response({"message": "If an account exists, a password reset email has been sent."}, status=status.HTTP_200_OK)

class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        tags=["auth"],
        summary="Change Password (Proxy to Supabase Auth)",
        description=(
            "Sets a new Supabase password for the logged-in user, as the user themselves (so Supabase's own rules "
            "apply, e.g. the new password must differ from the old one).\n\n"
            "- Normal session (logged in with a password): `current_password` is **required**.\n"
            "- Session from the password-reset email link (or magic link / invite): `current_password` may be "
            "omitted — send the link's `access_token` as `Authorization: Bearer <token>`.\n\n"
            "The session making the request stays valid; every other session of the user is signed out."
        ),
        request=PasswordChangeSerializer,
        responses={
            200: MessageSerializer,
            400: _error("`current_password` missing or wrong, password too weak (Supabase's message is returned), or same as the old one. Field validation errors are keyed by field instead."),
            401: _error("Missing/invalid access token."),
            **UPSTREAM_ERROR_RESPONSES,
        },
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        token = _bearer_token(request)
        current_password = serializer.validated_data.get('current_password')
        if current_password is None:
            if not (_token_auth_methods(token) & LINK_AUTH_METHODS):
                return Response({"error": "current_password is required."}, status=status.HTTP_400_BAD_REQUEST)
        elif not verify_password("password_change_verify", user, current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data['password']
        # PUT /user with the user's own token (supabase-py only exposes this for a
        # client-held session): Supabase keeps this session and revokes the others.
        call_supabase(
            "password_change",
            lambda supabase: supabase.auth._request("PUT", "user", body={"password": new_password}, jwt=token),
            client_error_status=400,
        )
        logger.info("password_changed", user_id=str(user.id))
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

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
    serializer_class = AccountDeleteSerializer

    @extend_schema(
        tags=["auth"],
        summary="Delete Account",
        description=(
            "Deletes the logged-in user's account after checking `password` against Supabase Auth. The Supabase "
            "user is banned and its email is released (renamed to `deleted_<id>@deleted.local`), so the email can "
            "be registered again. The Django user is deactivated and anonymised, and the profile is removed. "
            "Order history is kept. Accounts with an approved vendor cannot be deleted (see "
            "`GET /api/auth/account/deletion-eligibility/`)."
        ),
        request=AccountDeleteSerializer,
        responses={
            200: inline_serializer(name="AccountDeleteRes", fields={"success": serializers.BooleanField(), "message": serializers.CharField()}),
            400: OpenApiResponse(
                response=inline_serializer(name="AccountDeleteError", fields={
                    "success": serializers.BooleanField(),
                    "error": serializers.ChoiceField(choices=["invalid_password", "vendor_active"]),
                    "message": serializers.CharField(),
                }),
                description="Password missing or wrong (`invalid_password`), or the user has an approved vendor account (`vendor_active`).",
            ),
            401: OpenApiResponse(description="Missing/invalid access token."),
            500: OpenApiResponse(
                response=inline_serializer(name="AccountDeleteFailed", fields={
                    "success": serializers.BooleanField(), "error": serializers.CharField(), "message": serializers.CharField(),
                }),
                description="`deletion_failed`: the Django side failed; the Supabase side was reverted, so the user can retry.",
            ),
            **UPSTREAM_ERROR_RESPONSES,
        },
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

        user = request.user
        if not verify_password("account_delete_verify", user, password):
            return Response({"success": False, "error": "invalid_password", "message": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)

        original_email = user.email
        deleted_email = f"deleted_{user.id}@deleted.local"
        # Supabase first: if it fails nothing has changed and the user can retry.
        # The ban blocks sign-in and refresh; renaming the email frees it for re-registration.
        call_supabase(
            "account_delete",
            lambda supabase: supabase.auth.admin.update_user_by_id(
                str(user.id), {"email": deleted_email, "email_confirm": True, "ban_duration": "876000h"}
            ),
            admin=True,
            client_error_status=400,
        )

        try:
            with transaction.atomic():
                if hasattr(user, 'profile'):
                    user.profile.delete()
                user.email = deleted_email
                user.username = user.email
                user.is_active = False
                user.save()
            logger.info("account_deleted", user_id=str(user.id))
        except Exception as e:
            logger.error("account_delete_django_failed", user_id=str(user.id), error=str(e))
            # Undo the Supabase side so the user can log in and retry.
            try:
                call_supabase(
                    "account_delete_revert",
                    lambda supabase: supabase.auth.admin.update_user_by_id(
                        str(user.id), {"email": original_email, "email_confirm": True, "ban_duration": "none"}
                    ),
                    admin=True,
                )
            except SupabaseAuthError:
                logger.error("account_delete_revert_failed", user_id=str(user.id))
            return Response({"success": False, "error": "deletion_failed", "message": "Account deletion failed. Please contact support."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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

