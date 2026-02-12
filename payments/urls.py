from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments import views

router = DefaultRouter()
router.register(r'methods', views.PaymentMethodListView, basename='payment-methods')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', views.squad_webhook, name='squad-webhook'),
]
