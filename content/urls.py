from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PromotionalBannerListView, SupportInfoListView, SupportInfoFilterView,
    PromotionalBannerViewSet, SupportInfoViewSet,
    HeroSectionView, ContactInfoView,
)

router = DefaultRouter()
router.register(r'banners-manage', PromotionalBannerViewSet, basename='content-banners-manage')
router.register(r'support-manage', SupportInfoViewSet, basename='content-support-manage')

urlpatterns = [
    path('hero-section/', HeroSectionView.as_view(), name='content-hero-section'),
    path('contact-info/', ContactInfoView.as_view(), name='content-contact-info'),
    path('support-info/', SupportInfoFilterView.as_view(), name='content-support-info'),
    path('banners/', PromotionalBannerListView.as_view(), name='content-banners'),
    path('faqs/', SupportInfoListView.as_view(), name='content-faqs'),
    path('', include(router.urls)),
]
