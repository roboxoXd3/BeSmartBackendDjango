from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet,    AdminActionLogListView,
    SystemStatsView, AdminRecentActivityView, AdminRevenueChartView,
    PlatformSettingsView, AppConfigSettingsView, AdminCurrencyRatesView, AdminUpdateCurrencyRatesView,
    UserAdminViewSet, VendorAdminViewSet, AppSettingsViewSet,
    ProductAdminViewSet, OrderAdminViewSet,
    PayoutAdminViewSet, TransactionAdminViewSet, LoyaltyAdminViewSet
)

router = DefaultRouter()
router.register(r'admin-users', AdminUserViewSet, basename='admin-user')
router.register(r'settings', AppSettingsViewSet, basename='app-settings')
router.register(r'users', UserAdminViewSet, basename='admin-users')
router.register(r'vendors', VendorAdminViewSet, basename='admin-vendors')
router.register(r'products', ProductAdminViewSet, basename='admin-products')
router.register(r'orders', OrderAdminViewSet, basename='admin-orders')
router.register(r'payouts', PayoutAdminViewSet, basename='admin-payouts')
router.register(r'transactions', TransactionAdminViewSet, basename='admin-transactions')
router.register(r'loyalty', LoyaltyAdminViewSet, basename='admin-loyalty')

urlpatterns = [
    path('logs/', AdminActionLogListView.as_view(), name='admin-logs'),
    path('dashboard/stats/', SystemStatsView.as_view(), name='admin-system-stats'),
    path('dashboard/recent-activity/', AdminRecentActivityView.as_view(), name='admin-recent-activity'),
    path('dashboard/revenue-chart/', AdminRevenueChartView.as_view(), name='admin-revenue-chart'),
    path('settings/platform/', PlatformSettingsView.as_view(), name='admin-settings-platform'),
    path('settings/app-settings/', AppConfigSettingsView.as_view(), name='admin-settings-app'),
    path('settings/currency-rates/', AdminCurrencyRatesView.as_view(), name='admin-settings-currency-rates'),
    path('settings/update-rates/', AdminUpdateCurrencyRatesView.as_view(), name='admin-settings-update-rates'),
    path('', include(router.urls)),
]
