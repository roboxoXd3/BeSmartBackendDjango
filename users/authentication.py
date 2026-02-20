from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

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
            from users.views import get_supabase_client
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
            return (user, None)

        except Exception as e:
            print(f"DEBUG: Supabase token validation failed (treating as anonymous): {e}")
            return None
