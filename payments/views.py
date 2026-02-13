from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PaymentMethod, PaymentWebhook
from .serializers import PaymentMethodSerializer, InitiatePaymentSerializer, VerifyPaymentSerializer
from orders.models import Order
from drf_spectacular.utils import extend_schema
import uuid

class PaymentMethodListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentMethod.objects.none()
        return PaymentMethod.objects.filter(user=self.request.user)

from .serializers import PaymentSerializer
from rest_framework import viewsets

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return self.request.user.payments.all() # Assuming related_name='payments'
        # Or Payment.objects.filter(user=self.request.user)

class InitiatePaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=InitiatePaymentSerializer, responses={200: None})
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        amount = serializer.validated_data['amount']
        email = serializer.validated_data['email']
        
        # Verify order exists
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Mock interaction with Payment Gateway (Squad)
        # In real implementation, this would make a request to Squad API
        transaction_ref = f"SQ-{uuid.uuid4()}"
        checkout_url = f"https://sandbox.squadco.com/pay?ref={transaction_ref}"
        
        # Update order with transaction ref
        order.squad_transaction_ref = transaction_ref
        order.save()

        return Response({
            "status": "success",
            "message": "Payment initiated",
            "data": {
                "transaction_ref": transaction_ref,
                "checkout_url": checkout_url, # Frontend redirects here
            }
        })

class VerifyPaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request, ref):
        transaction_ref = ref
        
        # Mock verification logic
        # 1. Call Squad API to verify transaction_ref
        # 2. Check status matches 'success'
        
        # Simulating success
        success = True 
        
        if success:
            try:
                order = Order.objects.get(squad_transaction_ref=transaction_ref)
                if order.payment_status != 'paid':
                    order.payment_status = 'paid'
                    order.status = 'confirmed' # Move from pending to confirmed
                    order.save()
                    return Response({"status": "success", "message": "Payment verified and order confirmed"})
                return Response({"status": "success", "message": "Payment already verified"})
            except Order.DoesNotExist:
                return Response({"status": "error", "message": "Order not found for ref"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"status": "error", "message": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(views.APIView):
    permission_classes = [permissions.AllowAny] # Webhooks come from external service

    @extend_schema(exclude=True)
    def post(self, request):
        # Validate signature usually
        data = request.data
        # Log webhook
        PaymentWebhook.objects.create(
            transaction_ref=data.get('transaction_ref', 'unknown'),
            webhook_data=data
        )
        
        # Process event (e.g. update order status if not already updated)
        # This duplicates Verify logic but acts as backup
        
        return Response({"status": "received"}, status=status.HTTP_200_OK)
