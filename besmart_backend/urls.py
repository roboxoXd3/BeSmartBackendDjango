from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Application APIs
    path('api/users/', include('users.urls')),
    path('api/auth/', include('users.urls')), # Auth might be handled in users or separate
    path('api/products/', include('products.urls')),
    path('api/', include('orders.urls')), # Includes /cart, /wishlist, /orders
    path('api/payments/', include('payments.urls')),
    path('api/loyalty/', include('loyalty.urls')),
    path('api/vendors/', include('vendors.urls')),
    path('api/admin/', include('admin_api.urls')),
    path('api/support/', include('support.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/subcategories/', include('categories.subcategory_urls')),
    path('api/currency/', include('currency.urls')),
    path('api/content/', include('content.urls')),
    path('api/reviews/', include('products.review_urls')),
    path('api/search/analytics/', include('search.urls')),
    path('api/ai/', include('ai_services.urls')),
]
