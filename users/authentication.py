from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
import jwt

User = get_user_model()

class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            # Bearer <token>
            token = auth_header.split(' ')[1]
        except IndexError:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')

        if not token:
            return None

        try:
            # Strictly call Supabase to validate the token (Step away from "Django's end")
            from users.views import get_supabase_client # Import helper
            supabase = get_supabase_client()
            
            # get_user(token) calls the Supabase API. 
            # If token is invalid/expired/revoked, it raises an exception (or returns error).
            user_response = supabase.auth.get_user(token)
            user_data = user_response.user
            
            if not user_data:
                 raise exceptions.AuthenticationFailed('Invalid token: No user data returned from Supabase.')
                 
            # Sync Logic: Ensure local user exists
            # We map Supabase 'id' (UUID) to Django User 'id'
            user, created = User.objects.get_or_create(
                id=user_data.id, 
                defaults={
                    'email': user_data.email,
                    'username': user_data.email # Fallback username
                }
            )
            return (user, None)

        except Exception as e:
            # If Supabase returns 401 or any error, authentication fails.
            print(f"DEBUG: Supabase Validation Failed: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Supabase Validation Failed: {str(e)}')
