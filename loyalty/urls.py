from django.urls import path
from .views import (
    LoyaltyPointsView, LoyaltyTransactionListView, 
    LoyaltyRewardListView, RedeemRewardView, 
    LoyaltyVoucherListView, LoyaltyBadgeListView,
    ValidateVoucherView, UserBadgesView, BadgeProgressView, TierInfoView,
)

urlpatterns = [
    path('points/', LoyaltyPointsView.as_view(), name='loyalty-points'),
    path('transactions/', LoyaltyTransactionListView.as_view(), name='loyalty-transactions'),
    path('rewards/', LoyaltyRewardListView.as_view(), name='loyalty-rewards'),
    path('redeem/', RedeemRewardView.as_view(), name='loyalty-redeem'),
    path('vouchers/', LoyaltyVoucherListView.as_view(), name='loyalty-vouchers'),
    path('badges/', LoyaltyBadgeListView.as_view(), name='loyalty-badges'),
    path('validate-voucher/', ValidateVoucherView.as_view(), name='loyalty-validate-voucher'),
    path('user-badges/', UserBadgesView.as_view(), name='loyalty-user-badges'),
    path('badge-progress/', BadgeProgressView.as_view(), name='loyalty-badge-progress'),
    path('tier-info/', TierInfoView.as_view(), name='loyalty-tier-info'),
]
