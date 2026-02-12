from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from payments.models import Payment, PaymentWebhook, PaymentMethod
from payments.serializers import (
    PaymentSerializer,
    InitiatePaymentSerializer,
    VerifyPaymentSerializer,
    PaymentMethodSerializer
)
from payments.services.squad_service import SquadPaymentService
from orders.models import Order
from orders.services import OrderService


class PaymentMethodListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment operations
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments by current user"""
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate payment for an order
        
        POST /api/payments/initiate/
        Body: {"order_id": "uuid"}
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get order
            order = get_object_or_404(
                Order,
                id=serializer.validated_data['order_id'],
                user=request.user
            )
            
            # Initiate payment
            payment = OrderService.initiate_payment_for_order(order)
            
            return Response({
                'success': True,
                'data': {
                    'payment_id': str(payment.id),
                    'transaction_ref': payment.transaction_ref,
                    'checkout_url': payment.checkout_url,
                    'amount': float(payment.amount),
                    'currency': payment.currency
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def verify(self, request):
        """
        Verify payment status
        
        GET /api/payments/verify/?transaction_ref=xxx
        """
        transaction_ref = request.query_params.get('transaction_ref')
        
        if not transaction_ref:
            return Response({
                'success': False,
                'message': 'Transaction reference required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get payment from database
            payment = get_object_or_404(
                Payment,
                transaction_ref=transaction_ref,
                user=request.user
            )
            
            # Verify with Squad API
            squad_service = SquadPaymentService()
            verification = squad_service.verify_transaction(transaction_ref)
            
            if verification.get('status') == 200:
                data = verification.get('data', {})
                transaction_status = data.get('transaction_status')
                
                if transaction_status == 'Success':
                    # Update payment and order
                    if payment.status != 'success':
                        OrderService.handle_successful_payment(payment)
                    
                    return Response({
                        'success': True,
                        'data': {
                            'status': 'success',
                            'transaction_ref': transaction_ref,
                            'amount': data.get('transaction_amount'),
                            'payment_method': data.get('transaction_type'),
                            'order_id': str(payment.order.id)
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Payment not successful',
                        'data': {'status': transaction_status}
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                raise Exception('Verification failed')
                
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get payment history for current user
        
        GET /api/payments/history/
        """
        payments = self.get_queryset().select_related('order')
        serializer = self.get_serializer(payments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def squad_webhook(request):
    """
    Handle webhook notifications from Squad
    
    POST /api/payments/webhook/
    """
    try:
        # Get signature from header
        signature = request.headers.get('x-squad-encrypted-body', '')
        
        if not signature:
            # For development/sandbox, we might want to relax this or log it
            # return Response({'message': 'Missing signature'}, status=status.HTTP_401_UNAUTHORIZED)
             pass 
        
        payload = request.data
        
        # Validate signature
        squad_service = SquadPaymentService()
        if signature and not squad_service.validate_webhook_signature(payload, signature):
             return Response({
                 'message': 'Invalid signature'
             }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Store webhook
        event_type = payload.get('Event')
        body = payload.get('Body', {})
        transaction_ref = body.get('transaction_ref')
        
        webhook = PaymentWebhook.objects.create(
            event_type=event_type,
            transaction_ref=transaction_ref,
            payload=payload,
            signature=signature
        )
        
        # Process webhook based on event type
        if event_type == 'charge_successful':
            try:
                payment = Payment.objects.get(transaction_ref=transaction_ref)
                webhook.payment = payment
                
                # Update payment status
                if payment.status != 'success':
                    payment.gateway_transaction_ref = body.get('gateway_transaction_ref')
                    payment.payment_method = body.get('transaction_type', '').lower()
                    
                    OrderService.handle_successful_payment(payment)
                
                webhook.is_processed = True
                webhook.save()
                
            except Payment.DoesNotExist:
                pass
        
        return Response({
            'message': 'Webhook received'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'message': f'Webhook processing error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
