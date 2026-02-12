from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView, 
    FeaturedProductsView, 
    NewArrivalsView, 
    OnSaleProductsView, 
    ProductSearchView
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<uuid:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('featured/', FeaturedProductsView.as_view(), name='product-featured'),
    path('new-arrivals/', NewArrivalsView.as_view(), name='product-new-arrivals'),
    path('on-sale/', OnSaleProductsView.as_view(), name='product-on-sale'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
]
