from django.urls import path
from .views import (
    CartView, CartItemCreateView, CartItemUpdateView,
    WishlistView, WishlistDetailView,
    OrderListCreateView, OrderDetailView
)

urlpatterns = [
    # Cart
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/', CartItemCreateView.as_view(), name='cart-add-item'),
    path('cart/items/<uuid:pk>/', CartItemUpdateView.as_view(), name='cart-item-detail'),
    
    # Wishlist
    path('wishlist/', WishlistView.as_view(), name='wishlist-list'),
    path('wishlist/<uuid:pk>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    
    # Orders
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<uuid:id>/', OrderDetailView.as_view(), name='order-detail'),
]
