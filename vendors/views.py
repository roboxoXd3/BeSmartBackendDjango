from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    Vendor, VendorReview, VendorBankAccount, VendorPayout, 
    PayoutTransaction, SubscriptionPlan, VendorSubscription, 
    VendorSizeChartTemplate
)
from .serializers import (
    VendorSerializer, VendorRegisterSerializer, VendorReviewSerializer,
    VendorBankAccountSerializer, VendorPayoutSerializer, 
    SubscriptionPlanSerializer, VendorSubscriptionSerializer,
    VendorSizeChartTemplateSerializer
)
from drf_spectacular.utils import extend_schema
from django.db.models import Sum, Count

class VendorRegisterView(generics.CreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorRegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VendorProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorSerializer

    def get_object(self):
        return get_object_or_404(Vendor, user=self.request.user)

class VendorDashboardStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        
        # Calculate stats
        # These fields are pre-calculated in model during order processing usually, 
        # or we calculate on fly here.
        # For now return model fields.
        return Response({
            "total_sales": vendor.total_sales,
            "total_orders": vendor.total_orders,
            "average_rating": vendor.average_rating,
            "total_reviews": vendor.total_reviews,
            "payout_balance": 0.00, # Placeholder, needs calculation logic
        })

class VendorBankAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorBankAccountSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorBankAccount.objects.none()
        return VendorBankAccount.objects.filter(vendor__user=self.request.user)

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)

class VendorPayoutListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorPayoutSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorPayout.objects.none()
        return VendorPayout.objects.filter(vendor__user=self.request.user).order_by('-requested_at')

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        
        # 1. Check Balance
        # Aggregate released escrow transactions
        released_earnings = VendorPayout.objects.filter(
             vendor=vendor, 
             escrow_transactions__status='released'
        ).aggregate(total=Sum('escrow_transactions__amount'))['total'] or 0
        
        # But wait, EscrowTransaction has a ForeignKey to Payout?
        # No, update: EscrowTransaction links to Order and Vendor. Payout links to Vendor and has `squad_transaction_ref`.
        # When creating a Payout, we should associate 'released' escrow transactions to it? 
        # Or does `payout_balance` calculation differ?
        # Usually: Available Balance = (Sum of 'released' EscrowTransactions) - (Sum of 'completed'/'processing' Payouts)
        
        from django.db.models import Sum
        from decimal import Decimal
        from .models import EscrowTransaction
        
        released = EscrowTransaction.objects.filter(
            vendor=vendor, 
            status='released'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        paid_out = VendorPayout.objects.filter(
            vendor=vendor,
            status__in=['pending', 'processing', 'completed']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        available_balance = released - paid_out
        
        amount = serializer.validated_data.get('amount')
        if amount > available_balance:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Insufficient funds. Available balance: {available_balance}")

        # 2. Get Bank Account
        bank_account = serializer.validated_data.get('bank_account')
        if not bank_account:
            # Default to primary
            bank_account = vendor.bank_accounts.filter(is_primary=True).first()
            if not bank_account:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("No bank account specified and no primary account found.")
        
        # 3. Initiate Transfer
        from payments.services.squad_service import SquadTransferService
        transfer_service = SquadTransferService()
        
        transaction_ref = f"PAYOUT_{vendor.id}_{timezone.now().timestamp()}"
        
        try:
            # Verify account first? (Should be done on adding bank account)
            # Initiate transfer
            response = transfer_service.initiate_transfer(
                bank_code=bank_account.bank_code,
                account_number=bank_account.account_number,
                account_name=bank_account.account_name,
                amount=amount,
                transaction_ref=transaction_ref,
                currency=bank_account.currency,
                remark=f"Payout for {vendor.business_name}"
            )
            
            if response.get('status') == 200 and not response.get('error'):
                 # Squad might return success even if pending
                 serializer.save(
                     vendor=vendor, 
                     status='processing',
                     squad_transaction_ref=transaction_ref,
                     bank_account=bank_account
                 )
            else:
                 from rest_framework.exceptions import APIException
                 raise APIException(f"Transfer failed: {response.get('message')}")
                 
        except Exception as e:
             from rest_framework.exceptions import APIException
             raise APIException(f"Payout processing error: {str(e)}")

class SubscriptionPlanListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer

class VendorSubscriptionView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorSubscriptionSerializer

    def get_object(self):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        # Return latest active subscription or None (404)
        return get_object_or_404(VendorSubscription, vendor=vendor, status='active')

class VendorSizeChartTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorSizeChartTemplateSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorSizeChartTemplate.objects.none()
        return VendorSizeChartTemplate.objects.filter(vendor__user=self.request.user)

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)
