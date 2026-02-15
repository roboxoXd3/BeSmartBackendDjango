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
    VendorProductSizeChartAssignView,
)

router = DefaultRouter()
router.register(r'bank-accounts', VendorBankAccountViewSet, basename='vendor-bank-account')
router.register(r'size-charts', VendorSizeChartTemplateViewSet, basename='vendor-size-chart')

urlpatterns = [
    # Static paths first (before <uuid:id>/ patterns)
    path('', VendorListView.as_view(), name='vendor-list'),
    path('featured/', VendorFeaturedView.as_view(), name='vendor-featured'),
    path('search/', VendorSearchView.as_view(), name='vendor-search'),
    path('following/', VendorFollowedListView.as_view(), name='vendor-following'),
    path('register/', VendorRegisterView.as_view(), name='vendor-register'),
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
    path('dashboard/stats/', VendorDashboardStatsView.as_view(), name='vendor-dashboard-stats'),
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
