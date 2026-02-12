from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendorRegisterView, VendorProfileView, VendorDashboardStatsView,
    VendorPayoutListView, VendorBankAccountViewSet, SubscriptionPlanListView,
    VendorSubscriptionView, VendorSizeChartTemplateViewSet
)

router = DefaultRouter()
router.register(r'bank-accounts', VendorBankAccountViewSet, basename='vendor-bank-account')
router.register(r'size-charts', VendorSizeChartTemplateViewSet, basename='vendor-size-chart')

urlpatterns = [
    path('register/', VendorRegisterView.as_view(), name='vendor-register'),
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
    path('dashboard/stats/', VendorDashboardStatsView.as_view(), name='vendor-dashboard-stats'),
    path('payouts/', VendorPayoutListView.as_view(), name='vendor-payouts'),
    path('subscriptions/plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('subscriptions/current/', VendorSubscriptionView.as_view(), name='vendor-subscription-current'),
    path('', include(router.urls)),
]
