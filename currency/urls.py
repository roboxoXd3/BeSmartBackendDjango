from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CurrencyRateListView, UserCurrencyPreferenceView,
    CurrencyConversionView, CurrencyExchangeRateView,
    CurrencyRateViewSet,
)

router = DefaultRouter()
router.register(r'rates-manage', CurrencyRateViewSet, basename='currency-rates-manage')

urlpatterns = [
    path('rates/', CurrencyRateListView.as_view(), name='currency-rates'),
    path('rate/', CurrencyExchangeRateView.as_view(), name='currency-exchange-rate'),
    path('convert/', CurrencyConversionView.as_view(), name='currency-convert'),
    path('preference/', UserCurrencyPreferenceView.as_view(), name='currency-preference'),
    path('', include(router.urls)),
]
