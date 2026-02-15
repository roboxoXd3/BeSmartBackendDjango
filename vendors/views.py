from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from products.models import Product
from products.serializers import ProductListSerializer
from .models import (
    Vendor, VendorReview, VendorBankAccount, VendorPayout,
    VendorFollow, PayoutTransaction, SubscriptionPlan, VendorSubscription,
    VendorSizeChartTemplate
)
from .serializers import (
    VendorSerializer, VendorRegisterSerializer, VendorReviewSerializer,
    VendorReviewCreateSerializer, VendorBankAccountSerializer, VendorPayoutSerializer,
    SubscriptionPlanSerializer, VendorSubscriptionSerializer,
    VendorSizeChartTemplateSerializer,
    VendorListSerializer, VendorDetailSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter

# ============ Customer-facing Vendor APIs (Phase 2) ============

def _approved_vendors():
    return Vendor.objects.filter(status='approved', is_active=True)

class VendorListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorListSerializer
    queryset = _approved_vendors().order_by('-is_featured', '-average_rating')

    @extend_schema(summary="List vendors", description="List approved vendors for customers.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VendorFeaturedView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorListSerializer
    queryset = _approved_vendors().filter(is_featured=True).order_by('-average_rating')
    pagination_class = None

    @extend_schema(summary="Featured vendors")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VendorSearchView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorListSerializer

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()
        qs = _approved_vendors()
        if q:
            qs = qs.filter(
                Q(business_name__icontains=q) |
                Q(business_description__icontains=q) |
                Q(business_email__icontains=q)
            )
        return qs.order_by('-is_featured', '-average_rating')

    @extend_schema(parameters=[OpenApiParameter('q', str, description='Search query')])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VendorDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorDetailSerializer
    queryset = _approved_vendors()
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    @extend_schema(summary="Get vendor detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VendorProductsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        vendor_id = self.kwargs.get('id')
        get_object_or_404(Vendor, id=vendor_id, status='approved', is_active=True)
        return Product.objects.filter(vendor_id=vendor_id, status='active', approval_status='approved')

    @extend_schema(summary="List vendor products")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VendorReviewsListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return VendorReviewCreateSerializer if self.request.method == 'POST' else VendorReviewSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        vendor_id = self.kwargs.get('id')
        get_object_or_404(Vendor, id=vendor_id, status='approved', is_active=True)
        return VendorReview.objects.filter(vendor_id=vendor_id).order_by('-created_at')

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, id=self.kwargs['id'], status='approved', is_active=True)
        if VendorReview.objects.filter(vendor=vendor, user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "You have already reviewed this vendor."})
        serializer.save(vendor=vendor, user=self.request.user)

    @extend_schema(summary="List vendor reviews (GET) or create review (POST)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class VendorReviewUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorReviewSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return VendorReview.objects.filter(user=self.request.user)

    @extend_schema(summary="Update or delete your vendor review")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class VendorFollowView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        """Gap 16: isFollowingVendor — check if current user follows this vendor."""
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        is_following = VendorFollow.objects.filter(user=request.user, vendor=vendor).exists()
        return Response({"is_following": is_following})

    def post(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        follow, created = VendorFollow.objects.get_or_create(user=request.user, vendor=vendor)
        return Response({"success": True, "message": "Following vendor." if created else "Already following."}, status=status.HTTP_200_OK)

    def delete(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        deleted, _ = VendorFollow.objects.filter(user=request.user, vendor=vendor).delete()
        return Response({"success": True, "message": "Unfollowed." if deleted else "Was not following."}, status=status.HTTP_200_OK)

    @extend_schema(summary="Follow vendor (POST), unfollow (DELETE), or check status (GET)")
    def get_serializer_class(self):
        return None


class VendorFollowedListView(generics.ListAPIView):
    """GET /api/vendors/following/
    Gap 17: getFollowedVendors — list all vendors the current user follows."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorListSerializer

    def get_queryset(self):
        followed_vendor_ids = VendorFollow.objects.filter(
            user=self.request.user,
        ).values_list('vendor_id', flat=True)
        return _approved_vendors().filter(id__in=followed_vendor_ids)


class VendorFollowersView(views.APIView):
    """GET /api/vendors/{id}/followers/
    Gap 18+19: getVendorFollowerCount + getVendorFollowers."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        follows = VendorFollow.objects.filter(vendor=vendor).select_related('user').order_by('-created_at')
        count = follows.count()
        followers = []
        for f in follows[:50]:  # Cap at 50
            followers.append({
                'user_id': str(f.user_id),
                'email': f.user.email if f.user else '',
                'followed_at': f.created_at.isoformat() if f.created_at else None,
            })
        return Response({'count': count, 'followers': followers})


class VendorMyReviewView(views.APIView):
    """GET /api/vendors/{id}/my-review/
    Gap 20: getUserReviewForVendor — get the current user's review for a vendor."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        review = VendorReview.objects.filter(vendor=vendor, user=request.user).first()
        if not review:
            return Response({'review': None})
        return Response({
            'review': {
                'id': str(review.id),
                'vendor_id': str(review.vendor_id),
                'user_id': str(review.user_id),
                'rating': review.rating,
                'review_text': review.review_text,
                'created_at': review.created_at.isoformat() if review.created_at else None,
                'updated_at': review.updated_at.isoformat() if review.updated_at else None,
            }
        })

class VendorProductSizeChartAssignView(views.APIView):
    """PATCH /api/vendors/products/{product_id}/size-chart/
    Gap 14: updateProductSizeChart — vendor assigns a size chart template to a product."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, product_id):
        vendor = get_object_or_404(Vendor, user=request.user, status='approved')
        product = get_object_or_404(Product, id=product_id, vendor_id=vendor.id)

        template_id = request.data.get('template_id')
        size_guide_type = request.data.get('size_guide_type', 'template')

        from django.db import connection
        with connection.cursor() as c:
            c.execute("""
                UPDATE products
                SET size_chart_template_id = %s, size_guide_type = %s
                WHERE id = %s
            """, [template_id, size_guide_type, str(product.id)])

        return Response({
            'success': True,
            'message': 'Product size chart updated.',
            'product_id': str(product.id),
            'template_id': template_id,
            'size_guide_type': size_guide_type,
        })


# ============ Vendor Portal (existing) ============

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
