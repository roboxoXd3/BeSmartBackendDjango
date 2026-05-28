from django.urls import path
from .views import (
    RegisterView, LoginView, VendorLoginView, AdminLoginView, UserProfileView, LogoutView,
    PasswordResetView, PasswordChangeView, PasswordResetConfirmView,
    UploadAvatarView, UserAddressesView, UserPaymentMethodsView,
    TokenRefreshView, VerifyEmailView, ResendVerificationEmailView,
    AccountDeletionEligibilityView, AccountDeleteView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('vendor-login/', VendorLoginView.as_view(), name='auth_vendor_login'),
    path('admin-login/', AdminLoginView.as_view(), name='auth_admin_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='auth_resend_verify_email'),
    path('password-reset/', PasswordResetView.as_view(), name='auth_password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    path('change-password/', PasswordChangeView.as_view(), name='auth_password_change'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('profile/', UserProfileView.as_view(), name='user_profile_alias'),
    path('profile/upload-avatar/', UploadAvatarView.as_view(), name='user_upload_avatar'),
    path('account/deletion-eligibility/', AccountDeletionEligibilityView.as_view(), name='account-deletion-eligibility'),
    path('account/', AccountDeleteView.as_view(), name='account-delete'),
    path('addresses/', UserAddressesView.as_view(), name='user-addresses-list'),
    path('payment-methods/', UserPaymentMethodsView.as_view(), name='user-payment-methods-list'),
]
