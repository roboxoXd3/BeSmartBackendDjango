from rest_framework import authentication
from django.conf import settings
from django.contrib.auth import get_user_model
from supabase import create_client

from besmart_backend.metrics import auth_attempts_total
from besmart_backend.utils.logger import get_logger

User = get_user_model()
logger = get_logger(__name__)

try:
    from supabase_auth.errors import AuthApiError
except ImportError:
    # Defensive: if the supabase client's internals ever move this class, fall back
    # to treating every failure as the generic "error" case below rather than
    # crashing the whole auth path.
    AuthApiError = None

def get_supabase_client():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        raise ValueError("Supabase credentials not configured.")
    return create_client(url, key)

try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class SupabaseAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = 'users.authentication.SupabaseAuthentication'
        name = 'bearerAuth'  # standard name for UI

        def get_security_definition(self, auto_schema):
            return {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
except ImportError:
    pass


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Validates Supabase JWTs and syncs the user to Django.

    Returns (user, None) on success, or None when the token is missing /
    invalid / expired — letting DRF permission classes decide whether to
    allow or deny the request. Never raises: a malformed Authorization header
    or a rejected token both just fall through to an anonymous request, same
    as before.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        if not token:
            return None

        try:
            supabase = get_supabase_client()

            user_response = supabase.auth.get_user(token)
            user_data = user_response.user

            if not user_data:
                auth_attempts_total.labels(result="invalid_token").inc()
                return None

            user, _ = User.objects.get_or_create(
                id=user_data.id,
                defaults={
                    'email': user_data.email,
                    'username': user_data.email,
                },
            )

            # Reconcile Django's is_staff with the admin_users table Supabase
            # writes to, so a new/deactivated admin doesn't need a manual flip.
            # Superusers are left alone — they may not have an admin_users row.
            if not user.is_superuser:
                from admin_api.models import AdminUser
                is_admin = AdminUser.objects.filter(
                    email__iexact=user.email, is_active=True
                ).exists()
                if user.is_staff != is_admin:
                    user.is_staff = is_admin
                    user.save(update_fields=['is_staff'])

            auth_attempts_total.labels(result="success").inc()
            return (user, None)

        except ValueError as e:
            # get_supabase_client() raises this when SUPABASE_URL/KEY are unset --
            # a config problem, not normal traffic. Every authenticated request
            # silently becomes anonymous until this is fixed, so it's worth paging on.
            auth_attempts_total.labels(result="misconfigured").inc()
            logger.error("supabase_auth_misconfigured", error=str(e))
            return None

        except Exception as e:
            # An expired/invalid/malformed token surfaces here as AuthApiError from
            # supabase's own client -- that's normal traffic, not a failure, so it's
            # logged at info level and excluded from the "error" alerting bucket.
            # Anything else (network timeout to Supabase, unexpected shape, a DB
            # error from get_or_create/AdminUser above) is a real problem.
            if AuthApiError is not None and isinstance(e, AuthApiError):
                auth_attempts_total.labels(result="invalid_token").inc()
                logger.info("supabase_auth_token_rejected", error=str(e))
            else:
                auth_attempts_total.labels(result="error").inc()
                logger.error("supabase_auth_error", error=str(e), error_type=type(e).__name__)
            return None
