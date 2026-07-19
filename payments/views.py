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

from besmart_backend.utils.logger import get_logger
logger = get_logger(__name__)
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
        if getattr(self, 'swagger_fake_view', False):
            from .models import Payment
            return Payment.objects.none()
        return self.request.user.payments.all() # Assuming related_name='payments'

class InitiatePaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Initiate Squad Payment", tags=["Payments"], request=InitiatePaymentSerializer, responses={200: None})
    def post(self, request):
        logger.info("payment_initiation_started")
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        currency = serializer.validated_data.get('currency', 'NGN')
        callback_url = serializer.validated_data.get('callback_url')
        is_recurring = serializer.validated_data.get('is_recurring', False)

        # Always derive amount and email from the verified order — never trust client
        order = get_object_or_404(Order, id=order_id, user=request.user)
        amount = float(order.total)
        email = serializer.validated_data.get('email') or request.user.email
        
        logger.info("payment_order_validated", order_id=order.id, amount=amount, email=email)

        # Generate a unique transaction reference
        transaction_ref = f"BESMART-{uuid.uuid4().hex[:16].upper()}"

        # Call Squad API using the service to ensure consistent config and recurring flag
        from .services.squad_service import SquadPaymentService
        squad_service = SquadPaymentService()
        
        try:
            logger.info("payment_gateway_request_started", transaction_ref=transaction_ref)
            # TODO: We originally enforced is_recurring=True so the token is saved for future charges.
            # Since the current Squad merchant account does not support it and returns 400 Bad Request,
            # it has been disabled. Once the account is authorized for recurring billing, you can
            # change the default back to True in the serializer or enforce it here again.
            squad_response = squad_service.initiate_payment(
                amount=Decimal(str(amount)),
                email=email,
                transaction_ref=transaction_ref,
                currency=currency,
                callback_url=callback_url,
                is_recurring=is_recurring
            )

            if squad_response.get('status') == 200:
                checkout_url = squad_response['data']['checkout_url']
                transaction_ref = squad_response['data'].get('transaction_ref', transaction_ref)
            else:
                logger.error("payment_initiation_failed", order_id=order.id, reason=squad_response.get('message', 'gateway error'))
                return Response({
                    'status': 'error',
                    'message': squad_response.get('message', 'Payment gateway error'),
                }, status=status.HTTP_502_BAD_GATEWAY)

        except Exception as e:
            logger.error("payment_initiation_error", order_id=order.id, error=str(e))
            return Response({
                'status': 'error',
                'message': f'Could not reach payment gateway: {str(e)}',
            }, status=status.HTTP_502_BAD_GATEWAY)


        # Save transaction ref on the order
        order.squad_transaction_ref = transaction_ref
        order.save(update_fields=['squad_transaction_ref'])
        
        logger.info("payment_initiated", order_id=order.id, amount=amount, currency=currency, transaction_ref=transaction_ref)

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
        logger.info("payment_verification_started", transaction_ref=transaction_ref)

        squad_secret_key = getattr(settings, 'SQUAD_SECRET_KEY', '')
        squad_base_url = getattr(settings, 'SQUAD_BASE_URL', 'https://api-d.squadco.com')

        try:
            logger.info("payment_gateway_verify_started", transaction_ref=transaction_ref)
            squad_response = http_requests.get(
                f"{squad_base_url}/transaction/verify/{transaction_ref}",
                headers={
                    'Authorization': f'Bearer {squad_secret_key}',
                    'Content-Type': 'application/json',
                },
                timeout=15,
            )
            squad_data = squad_response.json()
            payment_status = squad_data.get('data', {}).get('transaction_status', '')
            gateway_ref = squad_data.get('data', {}).get('gateway_transaction_ref', '')
            is_successful = payment_status.lower() == 'success'
            logger.info("payment_gateway_verify_completed", transaction_ref=transaction_ref, payment_status=payment_status, is_successful=is_successful)
        except Exception as e:
            logger.error("payment_verification_error", transaction_ref=transaction_ref, error=str(e))
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
                    logger.info("payment_verified", order_id=order.id, transaction_ref=transaction_ref)
                return Response({
                    "status": "success",
                    "message": "Payment verified and order confirmed",
                    "gateway_ref": gateway_ref,
                })
            except Order.DoesNotExist:
                logger.warning("payment_verification_order_not_found", transaction_ref=transaction_ref)
                return Response(
                    {"status": "error", "message": "Order not found for this reference"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        logger.error("payment_verification_failed", transaction_ref=transaction_ref, payment_status=payment_status)
        return Response(
            {"status": "error", "message": f"Payment not successful. Status: {payment_status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

from .services.squad_service import SquadPaymentService
from decimal import Decimal

class PaymentWebhookView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        squad_service = SquadPaymentService()
        signature = request.headers.get('x-squad-encrypted-body')
        
        # Validate signature
        if not signature or not squad_service.validate_webhook_signature(request.body, signature):
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        event = request.data.get('Event', '')
        body = request.data.get('Body', {}) or {}

        if event == 'charge_successful':
            transaction_ref = body.get('transaction_ref')
            token_id = body.get('payment_information', {}).get('token_id')

            logger.info("payment_webhook_received", transaction_ref=transaction_ref)
            PaymentWebhook.objects.create(transaction_ref=transaction_ref, webhook_data=request.data)

            if transaction_ref:
                try:
                    order = Order.objects.get(squad_transaction_ref=transaction_ref)
                    if order.payment_status != 'paid':
                        order.payment_status = 'paid'
                        order.status = 'confirmed'
                        order.squad_gateway_ref = body.get('gateway_transaction_ref', '')
                        order.save()
                    
                    if token_id:
                        # Save token to user's payment methods
                        from .models import PaymentMethod
                        PaymentMethod.objects.get_or_create(
                            user=order.user,
                            squad_token=token_id,
                            defaults={
                                'provider': 'squad',
                                'payment_type': 'card',
                                'is_default': not PaymentMethod.objects.filter(user=order.user, is_default=True).exists()
                            }
                        )
                except Order.DoesNotExist:
                    pass

        elif event in ('transfer_successful', 'transfer_failed'):
            from django.utils import timezone
            from django.db import transaction as db_transaction
            from django.db.models import F
            from vendors.models import VendorPayout, PayoutTransaction, Vendor

            transaction_ref = (
                body.get('transaction_reference')
                or body.get('transaction_ref')
                or request.data.get('transaction_reference')
            )
            logger.info("transfer_webhook_received", event=event, transaction_ref=transaction_ref)
            PaymentWebhook.objects.create(transaction_ref=transaction_ref, webhook_data=request.data)

            if transaction_ref:
                with db_transaction.atomic():
                    payout = (
                        VendorPayout.objects.select_for_update()
                        .filter(squad_transaction_ref=transaction_ref)
                        .select_related('vendor')
                        .first()
                    )
                    if not payout:
                        txn = (
                            PayoutTransaction.objects.filter(reference_id=transaction_ref)
                            .select_related('payout', 'payout__vendor')
                            .first()
                        )
                        if txn and txn.payout_id:
                            payout = (
                                VendorPayout.objects.select_for_update()
                                .filter(pk=txn.payout_id)
                                .select_related('vendor')
                                .first()
                            )

                    if not payout:
                        pass
                    elif event == 'transfer_successful':
                        # Only complete from processing; ignore retries / late events
                        if payout.status == 'processing':
                            payout.status = 'completed'
                            payout.completed_at = timezone.now()
                            payout.failure_reason = None
                            payout.save(update_fields=['status', 'completed_at', 'failure_reason'])
                            Vendor.objects.filter(id=payout.vendor_id).update(
                                total_paid_out=F('total_paid_out') + payout.amount
                            )
                            PayoutTransaction.objects.create(
                                payout=payout,
                                amount=-payout.amount,
                                transaction_type='withdrawal',
                                reference_id=transaction_ref,
                                description=f'Payout completed - {payout.vendor.business_name}',
                            )
                    else:
                        # Failure: only from processing. Do not bump pending_payouts —
                        # process_transfer never decremented it on initiate.
                        if payout.status == 'processing':
                            reason = body.get('reason') or body.get('message') or 'Transfer failed'
                            payout.status = 'failed'
                            payout.failure_reason = reason
                            payout.completed_at = timezone.now()
                            payout.save(update_fields=['status', 'failure_reason', 'completed_at'])

        return Response({"status": "received"}, status=status.HTTP_200_OK)

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

class ChargeTokenView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=inline_serializer("ChargeTokenReq", fields={"order_id": serializers.UUIDField(), "payment_method_id": serializers.UUIDField()}), responses={200: None})
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_method_id = request.data.get('payment_method_id')
        
        if not order_id or not payment_method_id:
            return Response({"error": "Missing order_id or payment_method_id"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
        
        if not payment_method.squad_token:
            return Response({"error": "Payment method does not have a valid token"}, status=status.HTTP_400_BAD_REQUEST)

        amount = float(order.total)
        transaction_ref = f"BESMART-REC-{uuid.uuid4().hex[:12].upper()}"

        squad_service = SquadPaymentService()
        try:
            squad_response = squad_service.charge_card_with_token(
                amount=Decimal(str(amount)),
                token_id=payment_method.squad_token,
                transaction_ref=transaction_ref
            )
            
            if squad_response.get('status') == 200 and squad_response.get('data', {}).get('transaction_status') == 'success':
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.squad_transaction_ref = transaction_ref
                order.squad_gateway_ref = squad_response['data'].get('gateway_transaction_ref', '')
                order.save()
                return Response({"status": "success", "message": "Charge successful"})
            else:
                return Response({"error": "Charge failed", "details": squad_response}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("token_charge_failed", order_id=order.id, error=str(e))
            return Response({"error": f"Charge failed: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)
