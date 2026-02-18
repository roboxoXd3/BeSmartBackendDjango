from django.urls import path
from .views import (
    RegisterView, LoginView, UserProfileView, LogoutView,
    PasswordResetView, PasswordChangeView,
    TokenRefreshView,
    AccountDeletionEligibilityView, AccountDeleteView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password/reset/', PasswordResetView.as_view(), name='auth_password_reset'),
    path('password/change/', PasswordChangeView.as_view(), name='auth_password_change'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('profile/', UserProfileView.as_view(), name='user_profile_alias'),
    path('account/deletion-eligibility/', AccountDeletionEligibilityView.as_view(), name='account-deletion-eligibility'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
]
