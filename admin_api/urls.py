from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet,    AdminActionLogListView,
    SystemStatsView, AdminRecentActivityView, AdminRevenueChartView,
    UserAdminViewSet, VendorAdminViewSet, AppSettingsViewSet,
    ProductAdminViewSet, OrderAdminViewSet,
    PayoutAdminViewSet, TransactionAdminViewSet, LoyaltyAdminViewSet,
    CategoryAdminViewSet, SubcategoryAdminViewSet, AdminSessionViewSet,
    AdminProductImageUploadView, AdminBannerImageUploadView,
    AdminVersionUpdateView, EscrowAdminViewSet, SupportTicketAdminViewSet,
    VendorBankAccountAdminViewSet, HeroSectionAdminViewSet,
    ContactInfoAdminViewSet, PromotionalBannerAdminViewSet, SupportInfoAdminViewSet,
    AdminCategoryImageUploadView,
    LoyaltyBadgeAdminViewSet, LoyaltyRewardAdminViewSet, LoyaltyEarningRuleAdminViewSet
)

router = DefaultRouter()
router.register(r'admin-users', AdminUserViewSet, basename='admin-user')
router.register(r'sessions', AdminSessionViewSet, basename='admin-sessions')
router.register(r'settings', AppSettingsViewSet, basename='app-settings')
router.register(r'users', UserAdminViewSet, basename='admin-users')
router.register(r'vendors', VendorAdminViewSet, basename='admin-vendors')
router.register(r'vendor-bank-accounts', VendorBankAccountAdminViewSet, basename='admin-vendor-bank-accounts')
router.register(r'products', ProductAdminViewSet, basename='admin-products')
router.register(r'orders', OrderAdminViewSet, basename='admin-orders')
router.register(r'payouts', PayoutAdminViewSet, basename='admin-payouts')
router.register(r'transactions', TransactionAdminViewSet, basename='admin-transactions')
router.register(r'loyalty', LoyaltyAdminViewSet, basename='admin-loyalty')
router.register(r'loyalty/badges', LoyaltyBadgeAdminViewSet, basename='admin-loyalty-badges')
router.register(r'loyalty/rewards', LoyaltyRewardAdminViewSet, basename='admin-loyalty-rewards')
router.register(r'loyalty/rules', LoyaltyEarningRuleAdminViewSet, basename='admin-loyalty-rules')
router.register(r'escrow', EscrowAdminViewSet, basename='admin-escrow')
router.register(r'support-tickets', SupportTicketAdminViewSet, basename='admin-support-tickets')
router.register(r'hero-sections', HeroSectionAdminViewSet, basename='admin-hero-sections')
router.register(r'contact-info', ContactInfoAdminViewSet, basename='admin-contact-info')
router.register(r'promotional-banners', PromotionalBannerAdminViewSet, basename='admin-promotional-banners')
router.register(r'support-info', SupportInfoAdminViewSet, basename='admin-support-info')
router.register(r'categories', CategoryAdminViewSet, basename='admin-categories')
router.register(r'subcategories', SubcategoryAdminViewSet, basename='admin-subcategories')
urlpatterns = [
    path('logs/', AdminActionLogListView.as_view(), name='admin-logs'),
    path('dashboard/stats/', SystemStatsView.as_view(), name='admin-system-stats'),
    path('dashboard/recent-activity/', AdminRecentActivityView.as_view(), name='admin-recent-activity'),
    path('dashboard/revenue-chart/', AdminRevenueChartView.as_view(), name='admin-revenue-chart'),
    path('products/<uuid:id>/images/', AdminProductImageUploadView.as_view(), name='admin-product-image-upload'),
    path('categories/<uuid:id>/images/', AdminCategoryImageUploadView.as_view(), name='admin-category-image-upload'),
    path('content/banners/<uuid:id>/images/', AdminBannerImageUploadView.as_view(), name='admin-banner-image-upload'),
    path('app-version/', AdminVersionUpdateView.as_view(), name='admin-app-version'),
    path('', include(router.urls)),
]
