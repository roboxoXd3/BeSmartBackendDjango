from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PromotionalBannerListView, SupportInfoListView,
    PromotionalBannerViewSet, SupportInfoViewSet
)

router = DefaultRouter()
router.register(r'banners-manage', PromotionalBannerViewSet, basename='content-banners-manage')
router.register(r'support-manage', SupportInfoViewSet, basename='content-support-manage')

urlpatterns = [
    path('banners/', PromotionalBannerListView.as_view(), name='content-banners'),
    path('faqs/', SupportInfoListView.as_view(), name='content-faqs'),
    path('', include(router.urls)),
]
