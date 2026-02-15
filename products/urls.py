from django.urls import path
from .views import (
    ProductListView, ProductDetailView,
    FeaturedProductsView, NewArrivalsView, OnSaleProductsView, ProductSearchView,
    ProductSizeChartView, ProductViewTrackView,
    ProductReviewsListCreateView, CanReviewProductView,
    ProductQAListCreateView, ProductQAAnswerView, ProductQAHelpfulView,
    ImageSearchView,
    ProductDeliveryInfoView, ProductWarrantyInfoView,
    ProductOffersView, ProductHighlightsView,
    FeaturePostersView, ProductSpecificationsView,
    ProductRecommendationsView, ProductReviewsSummaryView,
)

urlpatterns = [
    # Static paths first (before <uuid:id>/ catch-all)
    path('', ProductListView.as_view(), name='product-list'),
    path('featured/', FeaturedProductsView.as_view(), name='product-featured'),
    path('new-arrivals/', NewArrivalsView.as_view(), name='product-new-arrivals'),
    path('on-sale/', OnSaleProductsView.as_view(), name='product-on-sale'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('search-by-image/', ImageSearchView.as_view(), name='product-image-search'),

    # Parameterized paths (uuid)
    path('<uuid:id>/delivery-info/', ProductDeliveryInfoView.as_view(), name='product-delivery-info'),
    path('<uuid:id>/warranty-info/', ProductWarrantyInfoView.as_view(), name='product-warranty-info'),
    path('<uuid:id>/offers/', ProductOffersView.as_view(), name='product-offers'),
    path('<uuid:id>/highlights/', ProductHighlightsView.as_view(), name='product-highlights'),
    path('<uuid:id>/feature-posters/', FeaturePostersView.as_view(), name='product-feature-posters'),
    path('<uuid:id>/specifications/', ProductSpecificationsView.as_view(), name='product-specifications'),
    path('<uuid:id>/recommendations/', ProductRecommendationsView.as_view(), name='product-recommendations'),
    path('<uuid:id>/reviews-summary/', ProductReviewsSummaryView.as_view(), name='product-reviews-summary'),
    path('<uuid:id>/can-review/', CanReviewProductView.as_view(), name='product-can-review'),
    path('<uuid:id>/reviews/', ProductReviewsListCreateView.as_view(), name='product-reviews'),
    path('<uuid:id>/qa/<uuid:qa_id>/answer/', ProductQAAnswerView.as_view(), name='product-qa-answer'),
    path('<uuid:id>/qa/<uuid:qa_id>/helpful/', ProductQAHelpfulView.as_view(), name='product-qa-helpful'),
    path('<uuid:id>/qa/', ProductQAListCreateView.as_view(), name='product-qa'),
    path('<uuid:id>/size-chart/', ProductSizeChartView.as_view(), name='product-size-chart'),
    path('<uuid:id>/view/', ProductViewTrackView.as_view(), name='product-view'),
    path('<uuid:id>/', ProductDetailView.as_view(), name='product-detail'),
]
