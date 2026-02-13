from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer, LogoutSerializer, LoginSerializer
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer, LogoutSerializer, LoginSerializer
from drf_spectacular.utils import extend_schema
from django.conf import settings
from supabase import create_client, Client

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
        # Extract other fields for local profile creation if needed
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
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
                        "last_name": last_name
                    }
                }
            })
            
            # 2. Return the session/user data
            # Note: If email confirmation is enabled, session might be None
            user_data = auth_response.user
            session_data = auth_response.session
            
            if user_data:
                # Sync logic is handled deeply in Authentication class on NEXT request,
                # BUT for registration we might want to ensure it acts immediately if session exists.
                # However, usually we rely on the client to login again or use the session.
                
                # We can also manually create the user here to avoid race conditions
                user, created = User.objects.get_or_create(
                    id=user_data.id,
                    defaults={
                        'email': user_data.email, 
                        'first_name': first_name, 
                        'last_name': last_name,
                        'username': user_data.email  # Ensure username is set and unique
                    }
                )

            return Response({
                "message": "Registration successful. Please check your email for verification.",
                "user": {"id": user_data.id, "email": user_data.email},
                "session": session_data # May be None if email confirm enabled
            }, status=status.HTTP_201_CREATED)
            
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
        # We need to update the Profile object, not just the User object
        # This implementation needs to handle updating the related Profile
        instance = self.request.user.profile
        serializer = ProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return the full user object
        user_serializer = UserSerializer(self.request.user)
        return Response(user_serializer.data)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login User (Proxy to Supabase)",
        request=LoginSerializer,
        responses={200: serializers.Serializer}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # if not email or not password: # Handled by serializer
        #      return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

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
