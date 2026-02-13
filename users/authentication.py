from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
import jwt
from supabase import create_client, Client

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
            # Verify the token using Supabase JWT Secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Error decoding token.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token.')

        user_id = payload.get('sub')
        if not user_id:
            raise exceptions.AuthenticationFailed('User identifier not found in token.')

        try:
            # Sync Logic: Ensure local user exists
            user, created = User.objects.get_or_create(
                id=user_id, # Assuming User model uses UUID matching Supabase
                defaults={
                    'email': payload.get('email'),
                    'username': payload.get('email') # Fallback username
                }
            )
            return (user, None)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'User sync failed: {str(e)}')
