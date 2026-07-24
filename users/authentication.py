from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
from supabase import create_client

User = get_user_model()

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
    allow or deny the request.  Only raises AuthenticationFailed for
    malformed Authorization headers (no actual token after "Bearer").
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

            return (user, None)

        except Exception as e:
            # Ignoring the print to avoid IOError in background processes
            pass
            return None
