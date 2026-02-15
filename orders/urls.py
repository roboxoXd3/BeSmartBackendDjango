from django.urls import path
from .views import (
    CartView, CartItemCreateView, CartItemUpdateView,
    CartClearView, CartSummaryView,
    WishlistView, WishlistDetailView,
    WishlistMoveToCartView, WishlistClearView,
    OrderListCreateView, OrderDetailView,
    OrderCancelView, OrderTrackView, OrderReorderView, OrderInvoiceView,
    OrderPaymentStatusView, OrderStatusUpdateView,
    ShippingAddressListCreateView,
    ShippingAddressDetailView,
    ShippingAddressSetDefaultView,
)

urlpatterns = [
    # Shipping Addresses
    path('shipping-addresses/', ShippingAddressListCreateView.as_view(), name='shipping-address-list'),
    path('shipping-addresses/<uuid:pk>/', ShippingAddressDetailView.as_view(), name='shipping-address-detail'),
    path('shipping-addresses/<uuid:pk>/set-default/', ShippingAddressSetDefaultView.as_view(), name='shipping-address-set-default'),

    # Cart
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),
    path('cart/summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('cart/items/', CartItemCreateView.as_view(), name='cart-add-item'),
    path('cart/items/<uuid:pk>/', CartItemUpdateView.as_view(), name='cart-item-detail'),

    # Wishlist
    path('wishlist/', WishlistView.as_view(), name='wishlist-list'),
    path('wishlist/clear/', WishlistClearView.as_view(), name='wishlist-clear'),
    path('wishlist/<uuid:pk>/move-to-cart/', WishlistMoveToCartView.as_view(), name='wishlist-move-to-cart'),
    path('wishlist/<uuid:pk>/', WishlistDetailView.as_view(), name='wishlist-detail'),

    # Orders
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<uuid:id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<uuid:id>/payment-status/', OrderPaymentStatusView.as_view(), name='order-payment-status'),
    path('orders/<uuid:id>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('orders/<uuid:id>/track/', OrderTrackView.as_view(), name='order-track'),
    path('orders/<uuid:id>/reorder/', OrderReorderView.as_view(), name='order-reorder'),
    path('orders/<uuid:id>/invoice/', OrderInvoiceView.as_view(), name='order-invoice'),
    path('orders/<uuid:id>/', OrderDetailView.as_view(), name='order-detail'),
]
