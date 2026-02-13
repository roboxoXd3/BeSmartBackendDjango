from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import RegisterView, LoginView, UserProfileView  # LogoutView removed/commented

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Not needed for Supabase (client handles refresh or we proxy it)
    # path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    # path('logout/', LogoutView.as_view(), name='auth_logout'), # Logout is client-side (clear token) or call Supabase signOut
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('profile/', UserProfileView.as_view(), name='user_profile_alias'),
]
