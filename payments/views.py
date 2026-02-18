from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import PaymentMethod, PaymentWebhook
from .serializers import PaymentMethodSerializer, InitiatePaymentSerializer, VerifyPaymentSerializer
from orders.models import Order
from drf_spectacular.utils import extend_schema
import uuid
import requests as http_requests

class PaymentMethodListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentMethod.objects.none()
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/payments/methods/{id}/
    Gaps 21+22: updatePaymentMethod + deletePaymentMethod."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentMethodSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentMethod.objects.none()
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        was_default = instance.is_default
        user = instance.user
        instance.delete()
        # If deleted card was default, promote the first remaining
        if was_default:
            first = PaymentMethod.objects.filter(user=user).first()
            if first:
                first.is_default = True
                first.save(update_fields=['is_default'])


class PaymentMethodSetDefaultView(views.APIView):
    """POST /api/payments/methods/{id}/set-default/
    Gap 23: setDefaultPaymentMethod."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: {'type': 'object'}})
    def post(self, request, pk):
        from django.db import transaction
        method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
        with transaction.atomic():
            PaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
            method.is_default = True
            method.save(update_fields=['is_default'])
        return Response({'success': True, 'message': 'Default payment method updated.'})


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
        currency = serializer.validated_data.get('currency', 'NGN')

        # Always derive amount and email from the verified order — never trust client
        order = get_object_or_404(Order, id=order_id, user=request.user)
        amount = float(order.total)
        email = serializer.validated_data.get('email') or request.user.email

        # Generate a unique transaction reference
        transaction_ref = f"BESMART-{uuid.uuid4().hex[:16].upper()}"

        # Call Squad API server-side (secret key stays on server)
        squad_secret_key = getattr(settings, 'SQUAD_SECRET_KEY', '')
        squad_base_url = getattr(settings, 'SQUAD_BASE_URL', 'https://api-d.squadco.com')

        # Convert amount to smallest currency unit (kobo for NGN)
        amount_in_kobo = int(amount * 100)

        try:
            squad_response = http_requests.post(
                f"{squad_base_url}/transaction/initiate",
                json={
                    'amount': amount_in_kobo,
                    'email': email,
                    'currency': currency,
                    'initiate_type': 'inline',
                    'transaction_ref': transaction_ref,
                },
                headers={
                    'Authorization': f'Bearer {squad_secret_key}',
                    'Content-Type': 'application/json',
                },
                timeout=30,
            )
            squad_data = squad_response.json()

            if squad_response.status_code == 200 and squad_data.get('status') == 200:
                checkout_url = squad_data['data']['checkout_url']
                transaction_ref = squad_data['data'].get('transaction_ref', transaction_ref)
            else:
                # Squad API call failed — return error with Squad's message
                return Response({
                    'status': 'error',
                    'message': squad_data.get('message', 'Payment gateway error'),
                }, status=status.HTTP_502_BAD_GATEWAY)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Could not reach payment gateway: {str(e)}',
            }, status=status.HTTP_502_BAD_GATEWAY)

        # Save transaction ref on the order
        order.squad_transaction_ref = transaction_ref
        order.save(update_fields=['squad_transaction_ref'])

        return Response({
            "status": "success",
            "message": "Payment initiated",
            "data": {
                "transaction_ref": transaction_ref,
                "checkout_url": checkout_url,
            }
        })

class VerifyPaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request, ref):
        transaction_ref = ref

        squad_secret_key = getattr(settings, 'SQUAD_SECRET_KEY', '')
        squad_base_url = getattr(settings, 'SQUAD_BASE_URL', 'https://api-d.squadco.com')

        try:
            squad_response = http_requests.get(
                f"{squad_base_url}/transaction/verify/{transaction_ref}",
                headers={
                    'Authorization': f'Bearer {squad_secret_key}',
                    'Content-Type': 'application/json',
                },
                timeout=20,
            )
            squad_data = squad_response.json()
            payment_status = squad_data.get('data', {}).get('transaction_status', '')
            gateway_ref = squad_data.get('data', {}).get('gateway_transaction_ref', '')
            is_successful = payment_status.lower() == 'success'
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Could not reach payment gateway: {str(e)}',
            }, status=status.HTTP_502_BAD_GATEWAY)

        if is_successful:
            try:
                order = Order.objects.get(squad_transaction_ref=transaction_ref)
                if order.payment_status != 'paid':
                    order.payment_status = 'paid'
                    order.status = 'confirmed'
                    if gateway_ref:
                        order.squad_gateway_ref = gateway_ref
                    order.save()
                return Response({
                    "status": "success",
                    "message": "Payment verified and order confirmed",
                    "gateway_ref": gateway_ref,
                })
            except Order.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Order not found for this reference"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"status": "error", "message": f"Payment not successful. Status: {payment_status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
