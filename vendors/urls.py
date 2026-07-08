from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendorRegisterView, VendorProfileView, VendorDashboardStatsView,
    VendorPayoutListView, VendorBankAccountViewSet, SubscriptionPlanListView,
    VendorSubscriptionView, VendorSizeChartTemplateViewSet,
    VendorListView, VendorFeaturedView, VendorSearchView, VendorDetailView,
    VendorProductsView, VendorReviewsListCreateView,
    VendorReviewUpdateDeleteView, VendorFollowView,
    VendorFollowedListView, VendorFollowersView, VendorMyReviewView,
    VendorKYCStatusView, VendorKYCUploadView, VendorResubmitView,
    VendorAnalyticsSalesView, VendorAnalyticsMetricsView,
    VendorCustomerLocationsView, VendorOwnProductViewSet,
    VendorOrderViewSet, VendorEscrowViewSet, VendorTransactionViewSet,
    VendorPayoutSummaryView,
    VendorProductReviewViewSet, VendorProductQAViewSet,
    VendorProductSizeChartAssignView, VendorSessionViewSet,
    VendorAnalyticsTrackView, VendorAnalyticsFunnelView, VendorAnalyticsPerformanceView,
    VendorAnalyticsViewsOverTimeView
)

router = DefaultRouter()
router.register(r'own-products', VendorOwnProductViewSet, basename='vendor-own-product')
router.register(r'orders', VendorOrderViewSet, basename='vendor-orders')
router.register(r'escrow', VendorEscrowViewSet, basename='vendor-escrow')
router.register(r'transactions', VendorTransactionViewSet, basename='vendor-transactions')
router.register(r'bank-accounts', VendorBankAccountViewSet, basename='vendor-bank-account')
router.register(r'size-charts', VendorSizeChartTemplateViewSet, basename='vendor-size-chart')
router.register(r'reviews', VendorProductReviewViewSet, basename='vendor-reviews-mgmt')
router.register(r'product-qa', VendorProductQAViewSet, basename='vendor-product-qa')
router.register(r'sessions', VendorSessionViewSet, basename='vendor-sessions')

urlpatterns = [
    # Static paths first (before <uuid:id>/ patterns)
    path('', VendorListView.as_view(), name='vendor-list'),
    path('featured/', VendorFeaturedView.as_view(), name='vendor-featured'),
    path('search/', VendorSearchView.as_view(), name='vendor-search'),
    path('following/', VendorFollowedListView.as_view(), name='vendor-following'),
    path('register/', VendorRegisterView.as_view(), name='vendor-register'),
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
    path('kyc-status/', VendorKYCStatusView.as_view(), name='vendor-kyc-status'),
    path('resubmit/', VendorResubmitView.as_view(), name='vendor-resubmit'),
    path('kyc/upload/', VendorKYCUploadView.as_view(), name='vendor-kyc-upload'),
    path('dashboard/stats/', VendorDashboardStatsView.as_view(), name='vendor-dashboard-stats'),
    path('dashboard/sales-trend/', VendorAnalyticsSalesView.as_view(), name='vendor-sales-trend'),
    path('analytics/sales/', VendorAnalyticsSalesView.as_view(), name='vendor-analytics-sales'),
    path('analytics/metrics/', VendorAnalyticsMetricsView.as_view(), name='vendor-analytics-metrics'),
    path('analytics/track/', VendorAnalyticsTrackView.as_view(), name='vendor-analytics-track'),
    path('analytics/funnel/', VendorAnalyticsFunnelView.as_view(), name='vendor-analytics-funnel'),
    path('analytics/performance/', VendorAnalyticsPerformanceView.as_view(), name='vendor-analytics-performance'),
    path('analytics/views-over-time/', VendorAnalyticsViewsOverTimeView.as_view(), name='vendor-analytics-views-over-time'),
    path('stats/customer-locations/', VendorCustomerLocationsView.as_view(), name='vendor-customer-locations'),
    path('payouts/summary/', VendorPayoutSummaryView.as_view(), name='vendor-payouts-summary'),
    path('payouts/', VendorPayoutListView.as_view(), name='vendor-payouts'),
    path('subscriptions/plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('subscriptions/current/', VendorSubscriptionView.as_view(), name='vendor-subscription-current'),
    path('products/<uuid:product_id>/size-chart/', VendorProductSizeChartAssignView.as_view(), name='vendor-product-size-chart'),
    path('reviews/<uuid:id>/', VendorReviewUpdateDeleteView.as_view(), name='vendor-review-detail'),

    # Parameterized paths (uuid)
    path('<uuid:id>/products/', VendorProductsView.as_view(), name='vendor-products'),
    path('<uuid:id>/reviews/', VendorReviewsListCreateView.as_view(), name='vendor-reviews'),
    path('<uuid:id>/my-review/', VendorMyReviewView.as_view(), name='vendor-my-review'),
    path('<uuid:id>/follow/', VendorFollowView.as_view(), name='vendor-follow'),
    path('<uuid:id>/followers/', VendorFollowersView.as_view(), name='vendor-followers'),
    path('<uuid:id>/', VendorDetailView.as_view(), name='vendor-detail'),

    # Router (bank-accounts, size-charts)
    path('', include(router.urls)),
]
