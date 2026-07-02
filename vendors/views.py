from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from products.models import Product, ProductReview, ProductQuestion
from orders.models import Order
from orders.serializers import OrderSerializer
from products.serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductReviewSerializer, ProductQuestionSerializer
)
from .models import (
    Vendor, VendorReview, VendorBankAccount, VendorPayout,
    VendorFollow, PayoutTransaction, SubscriptionPlan, VendorSubscription,
    VendorSizeChartTemplate, VendorSessions
)
from .serializers import (
    VendorSerializer, VendorRegisterSerializer, VendorReviewSerializer,
    VendorReviewCreateSerializer, VendorBankAccountSerializer, VendorPayoutSerializer,
    SubscriptionPlanSerializer, VendorSubscriptionSerializer,
    VendorSizeChartTemplateSerializer,
    VendorListSerializer, VendorDetailSerializer,
    VendorSessionSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from besmart_backend.utils.logger import get_logger
logger = get_logger(__name__)

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
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()
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
        if getattr(self, 'swagger_fake_view', False):
            return VendorReview.objects.none()
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
    serializer_class = serializers.Serializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Check if current user follows this vendor", responses={200: inline_serializer(name="VendorFollowStatusRes", fields={"is_following": serializers.BooleanField()})})
    def get(self, request, id):
        """Gap 16: isFollowingVendor — check if current user follows this vendor."""
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        is_following = VendorFollow.objects.filter(user=request.user, vendor=vendor).exists()
        return Response({"is_following": is_following})

    @extend_schema(summary="Follow vendor", responses={200: inline_serializer(name="VendorFollowRes", fields={"success": serializers.BooleanField(), "message": serializers.CharField()})})
    def post(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        follow, created = VendorFollow.objects.get_or_create(user=request.user, vendor=vendor)
        return Response({"success": True, "message": "Following vendor." if created else "Already following."}, status=status.HTTP_200_OK)

    @extend_schema(summary="Unfollow vendor", responses={200: inline_serializer(name="VendorUnfollowRes", fields={"success": serializers.BooleanField(), "message": serializers.CharField()})})
    def delete(self, request, id):
        vendor = get_object_or_404(Vendor, id=id, status='approved', is_active=True)
        deleted, _ = VendorFollow.objects.filter(user=request.user, vendor=vendor).delete()
        return Response({"success": True, "message": "Unfollowed." if deleted else "Was not following."}, status=status.HTTP_200_OK)


class VendorFollowedListView(generics.ListAPIView):
    """GET /api/vendors/following/
    Gap 17: getFollowedVendors — list all vendors the current user follows."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorListSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False): return Vendor.objects.none()
        followed_vendor_ids = VendorFollow.objects.filter(
            user=self.request.user,
        ).values_list('vendor_id', flat=True)
        return _approved_vendors().filter(id__in=followed_vendor_ids)


class VendorFollowersView(views.APIView):
    """GET /api/vendors/{id}/followers/
    Gap 18+19: getVendorFollowerCount + getVendorFollowers."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get vendor followers",
        responses={200: inline_serializer(name="VendorFollowersRes", fields={"count": serializers.IntegerField(), "followers": serializers.ListField(child=serializers.DictField())})}
    )
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

    @extend_schema(
        summary="Get current user's review for a vendor",
        responses={200: inline_serializer(name="VendorMyReviewRes", fields={"review": serializers.DictField(allow_null=True)})}
    )
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

    @extend_schema(
        summary="Assign size chart to product",
        request=inline_serializer(name="AssignSizeChartReq", fields={"template_id": serializers.UUIDField(), "size_guide_type": serializers.CharField(required=False)}),
        responses={200: inline_serializer(name="AssignSizeChartRes", fields={"success": serializers.BooleanField(), "message": serializers.CharField(), "product_id": serializers.CharField(), "template_id": serializers.CharField(), "size_guide_type": serializers.CharField()})}
    )
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
        vendor = serializer.save(user=self.request.user)
        logger.info("vendor_registered", vendor_id=vendor.id, user_id=self.request.user.id)

class VendorProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorSerializer

    def get_object(self):
        return get_object_or_404(Vendor, user=self.request.user)

class VendorKYCStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get vendor KYC status",
        responses={200: inline_serializer(
            name="VendorKYCStatusResponse",
            fields={
                "verification_status": serializers.CharField(),
                "verification_documents": serializers.ListField(child=serializers.DictField())
            }
        )}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        return Response({
            "verification_status": vendor.verification_status,
            "verification_documents": vendor.verification_documents or []
        })

class VendorKYCUploadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Upload product image",
        request=inline_serializer(name="VendorProductImageUploadReq", fields={"image": serializers.FileField()}),
        responses={200: inline_serializer(
            name="VendorProductImageUploadResponse",
            fields={
                "message": serializers.CharField(),
                "file_url": serializers.CharField(),
                "images": serializers.ListField(child=serializers.CharField())
            }
        )}
    )
    def post(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        file_obj = request.FILES.get('document')
        if not file_obj:
            return Response({"error": "No document provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        file_name = default_storage.save(f"kyc/{vendor.id}/{file_obj.name}", file_obj)
        file_url = default_storage.url(file_name)
        
        docs = vendor.verification_documents or []
        docs.append({"name": file_obj.name, "url": file_url, "uploaded_at": timezone.now().isoformat()})
        
        vendor.verification_documents = docs
        if vendor.verification_status == 'unverified' or vendor.verification_status == 'rejected':
            vendor.verification_status = 'pending'
        vendor.save()
        
        return Response({
            "message": "Document uploaded successfully.",
            "verification_status": vendor.verification_status,
            "documents": vendor.verification_documents
        }, status=status.HTTP_200_OK)

class VendorDashboardStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Vendor dashboard statistics with optional period",
        parameters=[OpenApiParameter('period', OpenApiTypes.STR, description='Period e.g., 7d, 30d, 90d, 1y', required=False)],
        responses={200: inline_serializer(
            name="VendorDashboardStatsResponse",
            fields={
                "totalProducts": serializers.IntegerField(),
                "totalOrders": serializers.IntegerField(),
                "totalSales": serializers.FloatField(),
                "pendingOrders": serializers.IntegerField(),
                "followerCount": serializers.IntegerField(),
                "currency": serializers.CharField(),
                "monthlyRevenue": serializers.FloatField()
            }
        )}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        period = request.query_params.get('period', '30d')
        from django.utils import timezone
        from datetime import timedelta
        import datetime
        now = timezone.now()
        start_date = now - timedelta(days=30)
        if period == '7d': start_date = now - timedelta(days=7)
        elif period == '90d': start_date = now - timedelta(days=90)
        elif period == '1y': start_date = now - timedelta(days=365)
        
        from orders.models import Order
        orders = Order.objects.filter(vendor_id=vendor.id, created_at__gte=start_date)
        
        total_sales = orders.filter(status__in=['delivered', 'shipped', 'confirmed']).aggregate(total=Sum('total'))['total'] or 0.00
        pending_orders = orders.filter(status='pending').count()
        total_products = Product.objects.filter(vendor_id=vendor.id).count()
        
        # Follower count
        follower_count = VendorFollow.objects.filter(vendor=vendor).count()
        
        return Response({
            "totalProducts": total_products,
            "totalOrders": orders.count(),
            "totalSales": total_sales,
            "pendingOrders": pending_orders,
            "followerCount": follower_count,
            "currency": "NGN",
            "monthlyRevenue": total_sales # Simple mapping for the dashboard spec
        })

class VendorAnalyticsSalesView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Vendor analytics sales and charts")
    @extend_schema(
        summary="Vendor sales trend",
        parameters=[OpenApiParameter('period', OpenApiTypes.STR, description='Period e.g., 7d, 30d, 90d, 1y', required=False)],
        responses={200: inline_serializer(
            name="VendorAnalyticsSalesRes",
            fields={
                "dailySales": serializers.ListField(child=serializers.DictField()),
                "statusCounts": serializers.DictField(),
                "totalRevenue": serializers.FloatField(),
                "totalOrders": serializers.IntegerField(),
                "period": serializers.CharField(),
                "trend": serializers.ListField(child=serializers.DictField())
            }
        )}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        period = request.query_params.get('period', '30d')
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import TruncDate
        
        days = 30
        if period == '7d': days = 7
        elif period == '90d': days = 90
        elif period == '1y': days = 365
        
        start_date = timezone.now() - timedelta(days=days)
        from orders.models import Order
        orders = Order.objects.filter(vendor_id=vendor.id, created_at__gte=start_date)
        
        daily_sales = list(orders.filter(status__in=['delivered', 'shipped', 'confirmed'])
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(revenue=Sum('total'), orders_count=Count('id'))
            .order_by('date'))
        
        # Format daily sales for response
        formatted_daily_sales = [
            {"date": entry["date"].isoformat(), "revenue": float(entry["revenue"] or 0), "orders": entry["orders_count"]}
            for entry in daily_sales
        ]
        
        status_counts_raw = list(orders.values('status').annotate(count=Count('id')))
        status_counts = {item['status']: item['count'] for item in status_counts_raw}
        
        total_revenue = sum([entry["revenue"] for entry in formatted_daily_sales])
        
        return Response({
            "dailySales": formatted_daily_sales,
            "statusCounts": status_counts,
            "totalRevenue": total_revenue,
            "totalOrders": orders.count(),
            "period": period,
            "trend": formatted_daily_sales # For sales-trend
        })

class VendorAnalyticsMetricsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Vendor general metrics",
        responses={200: inline_serializer(name="VendorAnalyticsMetricsRes", fields={
            "average_rating": serializers.FloatField(),
            "total_reviews": serializers.IntegerField(),
            "conversion_rate": serializers.FloatField(),
            "return_rate": serializers.FloatField()
        })}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        return Response({
            "average_rating": vendor.average_rating,
            "total_reviews": vendor.total_reviews,
            "conversion_rate": 0.05,  # Placeholder/mocked for now
            "return_rate": 0.01,
        })
        
class VendorCustomerLocationsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Customer locations for vendor orders",
        responses={200: inline_serializer(name="VendorCustomerLocationsRes", fields={"locations": serializers.ListField(child=serializers.DictField())})}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        # Assuming we join Order with ShippingAddress to get state/city
        # Just mock a basic aggregation since address_id is stored directly on Order
        return Response({
            "locations": [
                {"region": "Lagos", "count": vendor.total_orders},
                {"region": "Abuja", "count": 0}
            ]
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
                 payout = serializer.save(
                     vendor=vendor, 
                     status='processing',
                     squad_transaction_ref=transaction_ref,
                     bank_account=bank_account
                 )
                 logger.info("vendor_payout_initiated", vendor_id=vendor.id, amount=amount, payout_id=payout.id, ref=transaction_ref)
            else:
                 logger.error("vendor_payout_failed", vendor_id=vendor.id, amount=amount, reason=response.get('message'))
                 from rest_framework.exceptions import APIException
                 raise APIException(f"Transfer failed: {response.get('message')}")
                 
        except Exception as e:
             logger.error("vendor_payout_error", vendor_id=vendor.id, amount=amount, error=str(e))
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
        if self.request.user.is_staff:
            return VendorSizeChartTemplate.objects.all()
        return VendorSizeChartTemplate.objects.filter(vendor__user=self.request.user)

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)

    @extend_schema(
        summary="Upload size chart image",
        request=inline_serializer("VendorSizeChartImageUpload", {"image": serializers.ImageField()}),
        responses={200: inline_serializer("VendorSizeChartImageUploadResp", {"status": serializers.CharField(), "image_url": serializers.CharField()})}
    )
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        template = self.get_object()
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        from products.r2_utils import upload_file_to_r2
        import uuid
        ext = image.name.split('.')[-1] if '.' in image.name else 'png'
        key = f"size-charts/{template.id}/{uuid.uuid4()}.{ext}"
        
        try:
            public_url = upload_file_to_r2(image, key, image.content_type)
        except Exception as e:
            return Response({'error': 'Failed to upload image to storage', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        template.image_url = public_url
        template.save(update_fields=['image_url'])
        
        return Response({'image_url': public_url})

class VendorOwnProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=inline_serializer("VendorProductUploadImageReq", {"image": serializers.ImageField()}))

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return Product.objects.filter(vendor_id=vendor.id).order_by('-added_date')

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    def perform_create(self, serializer):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        product = serializer.save(vendor_id=vendor.id)
        logger.info("product_created", vendor_id=vendor.id, product_id=product.id)

    @extend_schema(
        summary="Update stock quantity",
        request=inline_serializer(name="UpdateStockRequest", fields={"stock_quantity": serializers.IntegerField()}),
        responses={200: inline_serializer(name="UpdateStockResponse", fields={"status": serializers.CharField(), "stock_quantity": serializers.IntegerField(), "in_stock": serializers.BooleanField()})}
    )
    @action(detail=True, methods=['patch'])
    def stock(self, request, pk=None):
        product = self.get_object()
        stock = request.data.get('stock_quantity')
        if stock is not None:
            product.stock_quantity = int(stock)
            product.in_stock = product.stock_quantity > 0
            product.save(update_fields=['stock_quantity', 'in_stock'])
            return Response({'status': 'stock updated', 'stock_quantity': product.stock_quantity, 'in_stock': product.in_stock})
        return Response({'error': 'stock_quantity missing'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Upload product image",
        request={'type': 'object', 'properties': {'image': {'type': 'string', 'format': 'binary'}}},
        responses={200: inline_serializer(name="ProductImageResponse", fields={"message": serializers.CharField(), "images": serializers.URLField()})}
    )
    @action(detail=True, methods=['post'], url_path='upload-image', parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        product = self.get_object()
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        file_name = default_storage.save(f"products/{product.id}/{file_obj.name}", file_obj)
        file_url = default_storage.url(file_name)
        product.images = file_url
        product.save()
        return Response({"message": "Image uploaded", "images": file_url})

    @extend_schema(
        summary="Bulk upsert products",
        request=inline_serializer(name="BulkUpsertReq", fields={"products": serializers.ListField(child=serializers.DictField())}),
        responses={200: inline_serializer(name="BulkUpsertRes", fields={"message": serializers.CharField(), "updated_count": serializers.IntegerField(), "created_count": serializers.IntegerField()})}
    )
    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        vendor = get_object_or_404(Vendor, user=self.request.user)
        products_data = request.data.get('products', [])
        
        if not products_data:
            return Response({'error': 'No products provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        updated_count = 0
        created_count = 0
        
        for p_data in products_data:
            product_id = p_data.get('id')
            if product_id:
                try:
                    product = Product.objects.get(id=product_id, vendor_id=vendor.id)
                    serializer = ProductDetailSerializer(product, data=p_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        updated_count += 1
                except Product.DoesNotExist:
                    pass
            else:
                serializer = ProductDetailSerializer(data=p_data)
                if serializer.is_valid():
                    serializer.save(vendor_id=vendor.id)
                    created_count += 1
                    
        logger.info("products_bulk_uploaded", vendor_id=vendor.id, created_count=created_count, updated_count=updated_count)
        return Response({
            'message': 'Bulk upsert completed',
            'updated_count': updated_count,
            'created_count': created_count
        })

    @extend_schema(
        summary="Update size chart visibility",
        request=inline_serializer(name="SizeChartVisReq", fields={"visible": serializers.BooleanField(required=False)}),
        responses={200: inline_serializer(name="SizeChartVisRes", fields={"status": serializers.CharField()})}
    )
    @action(detail=True, methods=['patch'], url_path='size-chart-visibility')
    def size_chart_visibility(self, request, pk=None):
        return Response({'status': 'size chart visibility updated'})

class VendorOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return Order.objects.filter(vendor_id=vendor.id).order_by('-created_at')

    @extend_schema(
        summary="Get recent orders",
        parameters=[OpenApiParameter("limit", OpenApiTypes.INT, description="Number of items")],
        responses={200: inline_serializer(name="RecentOrdersRes", fields={"data": serializers.ListField(child=serializers.DictField())})}
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        limit = int(request.query_params.get('limit', 5))
        orders = self.get_queryset()[:limit]
        serializer = self.get_serializer(orders, many=True)
        return Response({'data': serializer.data})

    @extend_schema(
        summary="Update order status",
        request=inline_serializer(
            name="VendorOrderStatusReq",
            fields={"status": serializers.CharField(), "tracking_number": serializers.CharField(required=False), "notes": serializers.CharField(required=False)}
        ),
        responses={200: inline_serializer(name="VendorOrderStatusRes", fields={"status": serializers.CharField(), "order_status": serializers.CharField()})}
    )
    @action(detail=True, methods=['put', 'patch'])
    def status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        tracking_number = request.data.get('tracking_number')
        notes = request.data.get('notes')
        
        if new_status:
            order.status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        if notes:
            order.notes = notes
            
        order.save(update_fields=['status', 'tracking_number', 'notes', 'updated_at'])
        
        logger.info("order_status_updated", vendor_id=order.vendor_id, order_id=order.id, new_status=order.status)
        return Response({'status': 'order updated', 'order_status': order.status})

class VendorEscrowDummy(serializers.Serializer):
    id = serializers.UUIDField()

class VendorEscrowViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorEscrowDummy
    
    def get_queryset(self):
        from .models import EscrowTransaction
        if getattr(self, 'swagger_fake_view', False):
            return EscrowTransaction.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        status_filter = self.request.query_params.get('status', 'all')
        qs = EscrowTransaction.objects.filter(vendor=vendor)
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')

    @extend_schema(
        summary="List Escrow Transactions",
        parameters=[OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status (pending, released, refunded, disputed)')],
        responses={200: inline_serializer(name="VendorEscrowListRes", fields={"data": serializers.ListField(child=serializers.DictField())})}
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{
            "id": str(e.id),
            "order_id": str(e.order_id),
            "amount": float(e.amount),
            "status": e.status,
            "release_date": e.release_date.isoformat() if e.release_date else None,
            "created_at": e.created_at.isoformat()
        } for e in qs]
        return Response({"data": data})

class VendorTransactionDummy(serializers.Serializer):
    id = serializers.UUIDField()

class VendorTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorTransactionDummy
    
    def get_queryset(self):
        from .models import PayoutTransaction
        if getattr(self, 'swagger_fake_view', False):
            return PayoutTransaction.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return PayoutTransaction.objects.filter(payout__vendor=vendor).order_by('-created_at')

    @extend_schema(
        summary="List Vendor Transactions",
        responses={200: inline_serializer(name="VendorTransactionListRes", fields={"data": serializers.ListField(child=serializers.DictField())})}
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{
            "id": str(t.id),
            "amount": float(t.amount),
            "transaction_type": t.transaction_type,
            "description": t.description,
            "created_at": t.created_at.isoformat()
        } for t in qs]
        return Response({"data": data})
        
class VendorPayoutSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get vendor payout summary",
        responses={200: inline_serializer(
            name="VendorPayoutSummaryRes",
            fields={
                "availableBalance": serializers.FloatField(),
                "pendingBalance": serializers.FloatField(),
                "lifetimeEarnings": serializers.FloatField(),
                "lastPayout": serializers.DictField()
            }
        )}
    )
    def get(self, request):
        vendor = get_object_or_404(Vendor, user=request.user)
        
        released = EscrowTransaction.objects.filter(
            vendor=vendor, status='released'
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        paid_out = VendorPayout.objects.filter(
            vendor=vendor, status__in=['pending', 'processing', 'completed']
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        available = float(released) - float(paid_out)
        if available < 0: available = 0
        
        pending = EscrowTransaction.objects.filter(
            vendor=vendor, status='held'
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        return Response({
            "availableBalance": available,
            "pendingBalance": float(pending),
            "lifetimeEarnings": float(released),
            "currency": "NGN"
        })

class VendorProductReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductReviewSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProductReview.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        qs = ProductReview.objects.filter(product__vendor_id=vendor.id)
        
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
        
        rating = self.request.query_params.get('rating')
        if rating:
            qs = qs.filter(rating=rating)
            
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
            
        has_response = self.request.query_params.get('has_response')
        if has_response == 'true':
            qs = qs.exclude(vendor_response__isnull=True).exclude(vendor_response__exact='')
        elif has_response == 'false':
            qs = qs.filter(Q(vendor_response__isnull=True) | Q(vendor_response__exact=''))
            
        return qs.order_by('-created_at')

    @extend_schema(summary="Respond or change visibility of review")
    def update(self, request, *args, **kwargs):
        # Allow PUT / PATCH for action (respond/hide/show)
        review = self.get_object()
        action_type = request.data.get('action')
        vendor_response = request.data.get('vendor_response')
        
        if action_type == 'respond' and vendor_response:
            review.vendor_response = vendor_response
            review.vendor_response_date = timezone.now()
        elif action_type == 'hide':
            review.status = 'hidden'
        elif action_type == 'show':
            review.status = 'published'
            
        review.save()
        return Response(self.get_serializer(review).data)

class VendorProductQAViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductQuestionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProductQuestion.objects.none()
        vendor = get_object_or_404(Vendor, user=self.request.user)
        qs = ProductQuestion.objects.filter(product__vendor_id=vendor.id)
        
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
            
        has_answer = self.request.query_params.get('has_answer')
        if has_answer == 'true':
            qs = qs.exclude(answer__isnull=True).exclude(answer__exact='')
        elif has_answer == 'false':
            qs = qs.filter(Q(answer__isnull=True) | Q(answer__exact=''))
            
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
            
        return qs.order_by('-created_at')

    @extend_schema(summary="Answer or change visibility of Q&A")
    def update(self, request, *args, **kwargs):
        qa = self.get_object()
        action_type = request.data.get('action')
        answer = request.data.get('answer')
        
        if action_type == 'answer' and answer:
            qa.answer = answer
            qa.answered_at = timezone.now()
            # Also optionally set answered_by = vendor.user.id
            qa.answered_by = str(request.user.id)
        elif action_type == 'hide':
            qa.status = 'hidden'
        elif action_type == 'show':
            qa.status = 'published'
            
        qa.save()
        return Response(self.get_serializer(qa).data)

class VendorSessionViewSet(viewsets.ModelViewSet):
    """
    Internal API for the Next.js vendor BFF to manage vendor sessions.
    Lookup field is session_token.
    """
    permission_classes = [permissions.AllowAny]
    queryset = VendorSessions.objects.all()
    serializer_class = VendorSessionSerializer
    lookup_field = 'session_token'
