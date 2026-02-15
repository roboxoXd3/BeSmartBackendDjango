from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('methods/', views.PaymentMethodListView.as_view(), name='payment-methods'),
    path('methods/<uuid:pk>/', views.PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    path('methods/<uuid:pk>/set-default/', views.PaymentMethodSetDefaultView.as_view(), name='payment-method-set-default'),
    path('webhook/', views.PaymentWebhookView.as_view(), name='squad-webhook'),
    path('initiate/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    path('verify/<str:ref>/', views.VerifyPaymentView.as_view(), name='verify-payment'),
]
