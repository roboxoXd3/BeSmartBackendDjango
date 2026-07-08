from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from besmart_backend.utils.logger import get_logger

logger = get_logger(__name__)
from django.shortcuts import get_object_or_404
from .models import AdminUser, AdminActionLog, AppSettings, AdminSession
from .serializers import (
    AdminUserSerializer, AdminActionLogSerializer,
    AppSettingsSerializer, UserManagementSerializer, UserAdminCreateUpdateSerializer,
    VendorAdminSerializer, PayoutAdminSerializer,
    TransactionAdminSerializer, OrderAdminSerializer,
    CategoryAdminSerializer, SubcategoryAdminSerializer,
    AdminSessionSerializer, EscrowAdminSerializer,
    SupportTicketAdminSerializer, SupportMessageAdminSerializer,
    VendorBankAccountAdminSerializer, LoyaltyPointsAdminSerializer,
    LoyaltyTransactionAdminSerializer, LoyaltyBadgeAdminSerializer, 
    LoyaltyRewardAdminSerializer, LoyaltyEarningRuleAdminSerializer
)
from content.models import PromotionalBanner, HeroSection, ContactInfo, SupportInfo
from content.serializers import (
    PromotionalBannerSerializer, HeroSectionSerializer,
    ContactInfoSerializer, SupportInfoSerializer
)
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser
from categories.models import Category, Subcategory
from loyalty.models import (
    LoyaltyPoints, LoyaltyTransaction, LoyaltyBadge, LoyaltyReward, LoyaltyEarningRule
)
from django.db import transaction
from users.models import User
from vendors.models import Vendor
from orders.models import Order
from products.models import Product
from vendors.models import VendorPayout, EscrowTransaction, VendorFollow, PayoutTransaction
from products.serializers import ProductListSerializer, ProductDetailSerializer
from orders.serializers import OrderSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin/staff users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer

class AdminSessionViewSet(viewsets.ModelViewSet):
    """
    Internal API for the Next.js admin BFF to manage admin sessions.
    Lookup field is session_token.
    """
    permission_classes = [permissions.AllowAny]
    queryset = AdminSession.objects.all()
    serializer_class = AdminSessionSerializer
    lookup_field = 'session_token'

class AdminActionLogListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = AdminActionLog.objects.all().order_by('-created_at')
    serializer_class = AdminActionLogSerializer

class AppSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class UserAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by('-date_joined')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserAdminCreateUpdateSerializer
        return UserManagementSerializer

    @extend_schema(
        summary="Update user status (suspend/activate)",
        request=inline_serializer(
            name="UserStatusRequest",
            fields={"action": serializers.ChoiceField(choices=["suspend", "activate"])}
        ),
        responses={200: inline_serializer(
            name="UserStatusResponse",
            fields={"status": serializers.CharField(), "is_active": serializers.BooleanField()}
        )}
    )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        logger.info("admin_user_status_update_started", admin_id=request.user.id, target_user_id=pk)
        user = self.get_object()
        action_type = request.data.get('action')
        if action_type == 'suspend':
            user.is_active = False
        elif action_type == 'activate':
            user.is_active = True
        user.save(update_fields=['is_active'])
        logger.info("admin_updated_user_status", admin_id=request.user.id, target_user_id=user.id, new_status=action_type)
        return Response({'status': 'user status updated', 'is_active': user.is_active})

class VendorAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['total_sales', 'created_at', 'average_rating']

    @extend_schema(summary="Get pending vendor approvals")
    @action(detail=False, methods=['get'], url_path='pending-approvals')
    def pending_approvals(self, request):
        vendors = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(vendors, many=True)
        return Response({'data': serializer.data})

    @extend_schema(
        summary="Update vendor status (approve/reject/suspend)",
        request=inline_serializer(
            name="VendorStatusRequest",
            fields={
                "status": serializers.ChoiceField(choices=[c[0] for c in Vendor.STATUS_CHOICES]),
                "admin_notes": serializers.CharField(required=False, allow_blank=True)
            }
        ),
        responses={200: inline_serializer(
            name="VendorStatusResponse",
            fields={"status": serializers.CharField(), "vendor_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        logger.info("admin_vendor_status_update_started", admin_id=request.user.id, target_vendor_id=pk)
        vendor = self.get_object()
        new_status = request.data.get('status')
        # Map 'notes' to 'admin_notes' if provided (frontend compatibility)
        admin_notes = request.data.get('admin_notes') or request.data.get('notes')
        
        if new_status in dict(Vendor.STATUS_CHOICES).keys():
            vendor.status = new_status
        if admin_notes:
            vendor.admin_notes = admin_notes
            
        vendor.save()
        logger.info("admin_updated_vendor_status", admin_id=request.user.id, target_vendor_id=vendor.id, new_status=new_status, has_notes=bool(admin_notes))
        return Response({'status': 'vendor status updated', 'vendor_status': vendor.status})

class SystemStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Admin dashboard overall statistics",
        responses={200: inline_serializer(
            name="AdminStatsResponse",
            fields={
                "success": serializers.BooleanField(),
                "data": inline_serializer(
                    name="AdminStatsData",
                    fields={
                        "totalUsers": serializers.IntegerField(),
                        "totalVendors": serializers.IntegerField(),
                        "totalOrders": serializers.IntegerField(),
                        "totalProducts": serializers.IntegerField(),
                        "pendingVendors": serializers.IntegerField(),
                        "totalRevenue": serializers.FloatField(),
                        "avgOrderValue": serializers.FloatField(),
                        "pendingPayouts": serializers.FloatField(),
                        "ordersChange": serializers.FloatField(),
                        "vendorsChange": serializers.FloatField(),
                        "revenueChange": serializers.FloatField(),
                        "avgOrderValueChange": serializers.FloatField(),
                    }
                )
            }
        )}
    )
    def get(self, request):
        from django.core.cache import cache
        cache_key = 'admin_system_stats'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({"success": True, "data": cached_data})

        from django.db.models import Sum, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        
        order_aggs = Order.objects.filter(status__in=['delivered', 'shipped', 'confirmed']).aggregate(total_revenue=Sum('total'), avg_value=Avg('total'))
        total_revenue = order_aggs['total_revenue'] or 0.00
        avg_order_value = order_aggs['avg_value'] or 0.00
        
        total_payouts_pending = VendorPayout.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0.00
        
        # Previous period
        prev_orders = Order.objects.filter(created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago).count()
        curr_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
        orders_change = ((curr_orders - prev_orders) / max(prev_orders, 1)) * 100
        
        prev_vendors = Vendor.objects.filter(created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago).count()
        curr_vendors = Vendor.objects.filter(created_at__gte=thirty_days_ago).count()
        vendors_change = ((curr_vendors - prev_vendors) / max(prev_vendors, 1)) * 100
        
        prev_order_aggs = Order.objects.filter(created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago, status__in=['delivered', 'shipped', 'confirmed']).aggregate(total_revenue=Sum('total'), avg_value=Avg('total'))
        prev_revenue = prev_order_aggs['total_revenue'] or 0.00
        revenue_change = ((float(total_revenue) - float(prev_revenue)) / max(float(prev_revenue), 1)) * 100

        prev_aov = prev_order_aggs['avg_value'] or 0.00
        aov_change = ((float(avg_order_value) - float(prev_aov)) / max(float(prev_aov), 1)) * 100
            
        data = {
            "totalUsers": User.objects.count(),
            "totalVendors": Vendor.objects.count(),
            "totalOrders": Order.objects.count(),
            "totalProducts": Product.objects.count(),
            "pendingVendors": Vendor.objects.filter(status='pending').count(),
            "totalRevenue": round(float(total_revenue), 2),
            "avgOrderValue": round(float(avg_order_value), 2),
            "pendingPayouts": round(float(total_payouts_pending), 2),
            "ordersChange": round(float(orders_change), 2),
            "vendorsChange": round(float(vendors_change), 2),
            "revenueChange": round(float(revenue_change), 2),
            "avgOrderValueChange": round(float(aov_change), 2),
        }
        cache.set(cache_key, data, timeout=300)  # Cache for 5 mins
        
        return Response({
            "success": True,
            "data": data
        })

class AdminRecentActivityView(views.APIView):
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        summary="Recent activity for admin dashboard",
        parameters=[OpenApiParameter("limit", OpenApiTypes.INT, description="Number of items")],
        responses={200: inline_serializer(
            name="AdminRecentActivityResponse",
            fields={
                "recent_orders": serializers.ListField(child=serializers.DictField()),
                "recent_signups": serializers.ListField(child=serializers.DictField())
            }
        )}
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        recent_orders = Order.objects.all().order_by('-created_at')[:limit]
        recent_signups = User.objects.all().order_by('-date_joined')[:limit]
        
        # Format explicitly to avoid creating new serializers just for the dashboard widget
        orders_data = [{
            "id": o.id,
            "order_number": o.order_number,
            "total": float(o.total),
            "status": o.status,
            "created_at": o.created_at.isoformat()
        } for o in recent_orders]
        
        users_data = [{
            "id": u.id,
            "email": u.email,
            "date_joined": u.date_joined.isoformat()
        } for u in recent_signups]
        
        return Response({
            "recent_orders": orders_data,
            "recent_signups": users_data
        })

class AdminRevenueChartView(views.APIView):
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        summary="Time series revenue for admin dashboard",
        parameters=[
            OpenApiParameter("period", OpenApiTypes.STR, description="E.g., 7d, 30d, 90d, 1y"),
            OpenApiParameter("start_date", OpenApiTypes.DATE, description="Custom start date (YYYY-MM-DD)"),
            OpenApiParameter("end_date", OpenApiTypes.DATE, description="Custom end date (YYYY-MM-DD)"),
            OpenApiParameter("vendor_id", OpenApiTypes.UUID, description="Filter by vendor"),
        ],
        responses={200: inline_serializer(
            name="AdminRevenueChartResponse",
            fields={
                "trend": serializers.ListField(child=serializers.DictField()),
                "category_breakdown": serializers.ListField(child=serializers.DictField()),
                "period": serializers.CharField(),
                "start_date": serializers.CharField(),
                "end_date": serializers.CharField(),
                "total_revenue": serializers.FloatField(),
                "total_orders": serializers.IntegerField()
            }
        )}
    )
    def get(self, request):
        period = request.query_params.get('period', '30d')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        vendor_id = request.query_params.get('vendor_id')
        
        from django.core.cache import cache
        cache_key = f'admin_revenue_chart_{period}_{start_date_str}_{end_date_str}_{vendor_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        from django.utils import timezone
        from datetime import timedelta, datetime
        from django.db.models.functions import TruncDate
        from django.db.models import Sum, Count, F
        
        end_date = timezone.now()
        if end_date_str:
            try:
                end_date = timezone.make_aware(datetime.strptime(end_date_str, "%Y-%m-%d"))
            except ValueError:
                pass

        if start_date_str:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
            except ValueError:
                start_date = end_date - timedelta(days=30)
        else:
            days = 30
            if period == '7d': days = 7
            elif period == '90d': days = 90
            elif period == '1y': days = 365
            start_date = end_date - timedelta(days=days)
        
        orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date, status__in=['delivered', 'shipped', 'confirmed'])
        if vendor_id:
            orders = orders.filter(items__product__vendor_id=vendor_id).distinct()
        
        daily_sales = list(orders
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(revenue=Sum('total'), orders_count=Count('id'))
            .order_by('date'))
        
        formatted_daily_sales = [
            {"date": entry["date"].isoformat(), "revenue": float(entry["revenue"] or 0), "orders": entry["orders_count"]}
            for entry in daily_sales
        ]
        
        category_breakdown = list(orders.values(cat_id=F('items__product__category_id'))
                                  .annotate(revenue=Sum(F('items__price') * F('items__quantity')))
                                  .order_by('-revenue'))
        
        # Fetch category names
        from categories.models import Category
        category_ids = [c['cat_id'] for c in category_breakdown if c['cat_id']]
        category_map = {cat.id: cat.name for cat in Category.objects.filter(id__in=category_ids)}

        formatted_category_breakdown = [
            {
                "category": category_map.get(cat['cat_id'], 'Unknown'),
                "revenue": float(cat['revenue'] or 0)
            }
            for cat in category_breakdown
        ]
        
        resp_data = {
            "trend": formatted_daily_sales,
            "category_breakdown": formatted_category_breakdown,
            "period": period,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_revenue": sum(d['revenue'] for d in formatted_daily_sales),
            "total_orders": sum(d['orders'] for d in formatted_daily_sales)
        }
        cache.set(cache_key, resp_data, timeout=300) # Cache for 5 mins
        return Response(resp_data)

class ProductAdminFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name='category_id')
    vendor = django_filters.UUIDFilter(field_name='vendor_id')

    class Meta:
        model = Product
        fields = ['approval_status', 'status']

class ProductAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all().order_by('-added_date')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductAdminFilter
    search_fields = ['name', 'description']
    ordering_fields = ['added_date', 'price', 'stock']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @extend_schema(summary="Get pending product approvals")
    @action(detail=False, methods=['get'], url_path='pending-approvals')
    def pending_approvals(self, request):
        products = self.get_queryset().filter(approval_status='pending')
        serializer = self.get_serializer(products, many=True)
        return Response({'data': serializer.data})

    @extend_schema(
        summary="Approve a product",
        request=inline_serializer(
            name="ProductApproveRequest",
            fields={"action": serializers.CharField(required=False)}
        ),
        responses={200: inline_serializer(
            name="ProductStatusAdminResponse",
            fields={"status": serializers.CharField(), "approval_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve(self, request, pk=None):
        product = self.get_object()
        product.approval_status = 'approved'
        product.save(update_fields=['approval_status'])
        logger.info("admin_approved_product", admin_id=request.user.id, product_id=product.id)
        return Response({'status': 'approval status updated', 'approval_status': product.approval_status})

    @extend_schema(
        summary="Reject a product",
        request=inline_serializer(
            name="ProductRejectRequest",
            fields={
                "action": serializers.CharField(required=False),
                "notes": serializers.CharField(required=False, allow_blank=True)
            }
        ),
        responses={200: inline_serializer(
            name="ProductStatusAdminResponse",
            fields={"status": serializers.CharField(), "approval_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject(self, request, pk=None):
        product = self.get_object()
        product.approval_status = 'rejected'
        if 'notes' in request.data:
            # Note: We might need a notes field on the product model or admin log
            pass
        product.save(update_fields=['approval_status'])
        logger.info("admin_rejected_product", admin_id=request.user.id, product_id=product.id)
        return Response({'status': 'approval status updated', 'approval_status': product.approval_status})

    @extend_schema(
        summary="Update product status (approve/reject)",
        request=inline_serializer(
            name="ProductStatusAdminRequest",
            fields={"approval_status": serializers.ChoiceField(choices=["approved", "rejected", "pending"])}
        ),
        responses={200: inline_serializer(
            name="ProductStatusAdminResponse",
            fields={"status": serializers.CharField(), "approval_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        product = self.get_object()
        new_status = request.data.get('approval_status')
        if new_status in ['approved', 'rejected', 'pending']:
            product.approval_status = new_status
            product.save(update_fields=['approval_status'])
            logger.info("admin_updated_product_status", admin_id=request.user.id, product_id=product.id, new_status=new_status)
            return Response({'status': 'approval status updated', 'approval_status': product.approval_status})
        return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)

class OrderAdminFilter(django_filters.FilterSet):
    dateFrom = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    dateTo = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    minAmount = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    maxAmount = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    vendorId = django_filters.UUIDFilter(field_name='items__product__vendor_id')
    user_id = django_filters.UUIDFilter(field_name='user_id')

    class Meta:
        model = Order
        fields = ['status']

class OrderAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Order.objects.select_related('user').prefetch_related('items', 'items__product').all().order_by('-created_at').distinct()
    serializer_class = OrderAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderAdminFilter
    search_fields = ['order_number', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'total']

    @extend_schema(
        summary="Update order status",
        request=inline_serializer(
            name="OrderStatusAdminRequest",
            fields={"status": serializers.CharField()}
        ),
        responses={200: inline_serializer(
            name="OrderStatusAdminResponse",
            fields={"status": serializers.CharField(), "order_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            logger.info("admin_updated_order_status", admin_id=request.user.id, order_id=order.id, new_status=new_status)
            return Response({'status': 'order status updated', 'order_status': order.status})
        return Response({'error': 'missing status'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get order summary for a user",
        parameters=[OpenApiParameter("user_id", OpenApiTypes.UUID, description="User ID")],
        responses={200: inline_serializer(
            name="UserOrderSummaryResponse",
            fields={"orders_count": serializers.IntegerField(), "total_spent": serializers.FloatField()}
        )}
    )
    @action(detail=False, methods=['get'], url_path='user-summary')
    def user_summary(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        orders = self.get_queryset().filter(user_id=user_id)
        from django.db.models import Sum, Count
        aggs = orders.aggregate(count=Count('id'), total=Sum('total'))
        
        return Response({
            'orders_count': aggs['count'] or 0,
            'total_spent': float(aggs['total'] or 0.0)
        })

class PayoutAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = VendorPayout.objects.all().order_by('-requested_at')
    serializer_class = PayoutAdminSerializer

    @extend_schema(
        summary="Update payout status (process/complete/fail)",
        request=inline_serializer(
            name="PayoutStatusAdminRequest",
            fields={
                "status": serializers.ChoiceField(choices=["pending", "processing", "completed", "failed", "cancelled"]),
                "admin_notes": serializers.CharField(required=False, allow_blank=True)
            }
        ),
        responses={200: inline_serializer(
            name="PayoutStatusAdminResponse",
            fields={"status": serializers.CharField(), "payout_status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        logger.info("admin_payout_status_update_started", admin_id=request.user.id, target_payout_id=pk)
        payout = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes')
        
        from django.utils import timezone
        if new_status in ['pending', 'processing', 'completed', 'failed', 'cancelled']:
            payout.status = new_status
            if new_status == 'completed':
                payout.completed_at = timezone.now()
            elif new_status == 'processing':
                payout.processed_at = timezone.now()
        
        if admin_notes is not None:
            payout.admin_notes = admin_notes
            
        payout.save()
        logger.info("admin_updated_payout_status", admin_id=request.user.id, payout_id=payout.id, new_status=new_status)
        return Response({'status': 'payout updated', 'payout_status': payout.status})

    @extend_schema(
        summary="Trigger explicit Squad transfer for a payout",
        request=inline_serializer(
            name="PayoutProcessAdminRequest",
            fields={"admin_notes": serializers.CharField(required=False, allow_blank=True)}
        ),
        responses={200: inline_serializer(
            name="PayoutProcessAdminResponse",
            fields={"status": serializers.CharField(), "message": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post'], url_path='process-transfer')
    def process_transfer(self, request, pk=None):
        logger.info("admin_payout_transfer_started", admin_id=request.user.id, target_payout_id=pk)
        payout = self.get_object()
        
        if payout.status in ['completed', 'processing']:
            return Response({'error': f'Payout is already {payout.status}'}, status=status.HTTP_400_BAD_REQUEST)
            
        bank_account = payout.vendor.bank_accounts.filter(is_primary=True).first()
        if not bank_account:
            bank_account = payout.vendor.bank_accounts.first()
            
        if not bank_account:
            return Response({'error': 'Vendor has no configured bank accounts'}, status=status.HTTP_400_BAD_REQUEST)
            
        from payments.services.squad_service import SquadTransferService
        import uuid
        
        transfer_svc = SquadTransferService()
        ref = f"PAY-{str(payout.id)[:8]}-{uuid.uuid4().hex[:8]}"
        
        result = transfer_svc.initiate_transfer(
            transaction_ref=ref,
            amount=payout.amount,
            bank_code=bank_account.bank_code,
            account_number=bank_account.account_number,
            account_name=bank_account.account_name,
            remark=f"Payout for {payout.vendor.business_name}"
        )
        
        if result.get('success'):
            from django.utils import timezone
            payout.status = 'processing'
            payout.processed_at = timezone.now()
            if 'admin_notes' in request.data:
                payout.admin_notes = request.data['admin_notes']
            payout.save()
            
            from vendors.models import PayoutTransaction
            PayoutTransaction.objects.create(
                payout=payout,
                vendor=payout.vendor,
                amount=payout.amount,
                transaction_type='payout',
                reference_id=ref,
                gateway='squad',
                status='pending',
                description='Squad transfer initiated'
            )
            
            logger.info("admin_initiated_squad_transfer", admin_id=request.user.id, payout_id=payout.id, ref=ref)
            return Response({'status': 'processing', 'message': 'Transfer initiated successfully'})
        else:
            logger.error("admin_squad_transfer_failed", admin_id=request.user.id, payout_id=payout.id, error=result.get('message'))
            return Response({'error': result.get('message', 'Transfer failed')}, status=status.HTTP_400_BAD_REQUEST)

class TransactionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = PayoutTransaction.objects.all().order_by('-created_at')
    serializer_class = TransactionAdminSerializer

class EscrowAdminFilter(django_filters.FilterSet):
    class Meta:
        model = EscrowTransaction
        fields = ['status', 'vendor_id', 'order_id']

class EscrowAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = EscrowTransaction.objects.all().order_by('-created_at')
    serializer_class = EscrowAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EscrowAdminFilter
    search_fields = ['reference_id', 'vendor__business_name']
    ordering_fields = ['created_at', 'amount']

    @extend_schema(
        summary="Release an escrow transaction",
        responses={200: inline_serializer(name="EscrowReleaseResponse", fields={"status": serializers.CharField()})}
    )
    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        from django.utils import timezone
        from django.db import transaction
        with transaction.atomic():
            escrow = self.get_object()
            if escrow.status != 'held':
                return Response({'error': f'Escrow is already {escrow.status}'}, status=status.HTTP_400_BAD_REQUEST)
            escrow.status = 'released'
            escrow.release_date = timezone.now()
            escrow.save()
            vendor = escrow.vendor
            vendor.available_balance += escrow.amount
            vendor.save()
        return Response({'status': 'escrow released'})

    @extend_schema(
        summary="Hold an escrow transaction",
        responses={200: inline_serializer(name="EscrowHoldResponse", fields={"status": serializers.CharField()})}
    )
    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        escrow = self.get_object()
        if escrow.status == 'held':
            return Response({'error': 'Escrow is already held'}, status=status.HTTP_400_BAD_REQUEST)
        escrow.status = 'held'
        escrow.save()
        return Response({'status': 'escrow held'})

    @extend_schema(
        summary="Refund an escrow transaction",
        responses={200: inline_serializer(name="EscrowRefundResponse", fields={"status": serializers.CharField()})}
    )
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        escrow = self.get_object()
        if escrow.status == 'refunded':
            return Response({'error': 'Escrow is already refunded'}, status=status.HTTP_400_BAD_REQUEST)
        escrow.status = 'refunded'
        escrow.save()
        return Response({'status': 'escrow refunded'})

from support.models import SupportTicket

class SupportTicketAdminFilter(django_filters.FilterSet):
    class Meta:
        model = SupportTicket
        fields = ['status', 'priority', 'vendor_id', 'user_id', 'assigned_to', 'resolved_by']

class SupportTicketAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = SupportTicket.objects.select_related('vendor', 'user', 'assigned_to', 'resolved_by').prefetch_related('messages').all().order_by('-created_at')
    serializer_class = SupportTicketAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SupportTicketAdminFilter
    search_fields = ['subject', 'vendor__business_name', 'user__email']
    ordering_fields = ['created_at', 'updated_at', 'status']
    
    @extend_schema(
        summary="Reply to a support ticket",
        request=inline_serializer(
            name="SupportTicketReplyAdminRequest",
            fields={"message": serializers.CharField()}
        ),
        responses={200: SupportMessageAdminSerializer}
    )
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        message_text = request.data.get('message')
        if not message_text:
            return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        from support.models import SupportMessage
        message = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            sender_role='admin',
            message=message_text
        )
        
        # Extract AdminUser instance for assigned_to
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            if not ticket.assigned_to:
                ticket.assigned_to = admin_user
        except AdminUser.DoesNotExist:
            pass
            
        if ticket.status == 'open':
            ticket.status = 'in_progress'
        ticket.save()
        
        return Response(SupportMessageAdminSerializer(message).data)

from vendors.models import VendorBankAccount

class VendorBankAccountAdminFilter(django_filters.FilterSet):
    class Meta:
        model = VendorBankAccount
        fields = ['vendor_id', 'is_default']

class VendorBankAccountAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = VendorBankAccount.objects.select_related('vendor').all().order_by('-created_at')
    serializer_class = VendorBankAccountAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VendorBankAccountAdminFilter
    search_fields = ['vendor__business_name', 'account_name', 'account_number', 'bank_name']
    ordering_fields = ['created_at', 'vendor__business_name']

class CategoryAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategoryAdminSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class HeroSectionAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = HeroSection.objects.all().order_by('-id')
    serializer_class = HeroSectionSerializer

class ContactInfoAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ContactInfo.objects.all().order_by('-id')
    serializer_class = ContactInfoSerializer

class PromotionalBannerAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = PromotionalBanner.objects.all().order_by('priority')
    serializer_class = PromotionalBannerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'subtitle', 'link_url']

    def perform_create(self, serializer):
        try:
            admin_user = AdminUser.objects.get(user=self.request.user)
            serializer.save(created_by=admin_user)
        except AdminUser.DoesNotExist:
            serializer.save()

class SupportInfoAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = SupportInfo.objects.all().order_by('order_index')
    serializer_class = SupportInfoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type']
    search_fields = ['title', 'subtitle']

class SubcategoryAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Subcategory.objects.all().order_by('name')
    serializer_class = SubcategoryAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class LoyaltyAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer

    @extend_schema(
        summary="Add/Deduct loyalty points for a user",
        request=inline_serializer(
            name="LoyaltyPointsAdminRequest",
            fields={
                "points": serializers.IntegerField(),
                "description": serializers.CharField(required=False, allow_blank=True)
            }
        ),
        responses={200: inline_serializer(
            name="LoyaltyPointsAdminResponse",
            fields={
                "message": serializers.CharField(),
                "points_balance": serializers.IntegerField(),
                "user": serializers.CharField()
            }
        )}
    )
    @action(detail=True, methods=['post'], url_path='points')
    def points(self, request, pk=None):
        user = self.get_object()
        points_change = int(request.data.get('points', 0))
        description = request.data.get('description', 'Admin manual adjustment')
        
        if points_change == 0:
            loyalty, _ = LoyaltyPoints.objects.get_or_create(user=user)
            return Response({'message': 'No change applied.', 'points_balance': loyalty.points_balance, 'user': str(user.id)})

        with transaction.atomic():
            loyalty, _ = LoyaltyPoints.objects.get_or_create(user=user)
            loyalty.points_balance += points_change
            if points_change > 0:
                loyalty.lifetime_points += points_change
            loyalty.save()

            LoyaltyTransaction.objects.create(
                user=user,
                points_change=points_change,
                transaction_type='adjustment',
                reference_type='admin',
                description=description,
                points_balance_after=loyalty.points_balance
            )

        return Response({
            'message': f'{points_change} points applied.',
            'points_balance': loyalty.points_balance,
            'user': str(user.id)
        })

    @extend_schema(
        summary="Get aggregate loyalty analytics",
        responses={200: inline_serializer(
            name="LoyaltyAnalyticsResponse",
            fields={
                "total_points_issued": serializers.IntegerField(),
                "total_points_redeemed": serializers.IntegerField(),
                "total_active_users": serializers.IntegerField(),
                "tier_distribution": serializers.DictField(),
                "voucher_stats": serializers.DictField(),
                "thirty_day_trend": serializers.ListField(child=serializers.DictField()),
                "top_5_rewards": serializers.ListField(child=serializers.DictField()),
                "last_10_redemptions": serializers.ListField(child=serializers.DictField())
            }
        )}
    )
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        from loyalty.models import LoyaltyVoucher
        
        issued = LoyaltyTransaction.objects.filter(transaction_type='earn').aggregate(Sum('points_change'))['points_change__sum'] or 0
        redeemed = LoyaltyTransaction.objects.filter(transaction_type='redeem').aggregate(Sum('points_change'))['points_change__sum'] or 0
        
        if redeemed < 0:
            redeemed = abs(redeemed)
            
        active_users = LoyaltyPoints.objects.count()

        tier_distribution = dict(LoyaltyPoints.objects.values_list('tier').annotate(count=Count('id')))
        voucher_stats = dict(LoyaltyVoucher.objects.values_list('status').annotate(count=Count('id')))
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        trend = LoyaltyTransaction.objects.filter(created_at__gte=thirty_days_ago)\
            .values('created_at__date', 'transaction_type')\
            .annotate(total=Sum('points_change'))
            
        thirty_day_trend = [
            {
                'date': item['created_at__date'].isoformat(),
                'type': item['transaction_type'],
                'total': abs(item['total'])
            } for item in trend
        ]
        
        top_rewards_query = LoyaltyVoucher.objects.values('reward__name')\
            .annotate(count=Count('id')).order_by('-count')[:5]
        top_5_rewards = [{'reward_name': r['reward__name'], 'count': r['count']} for r in top_rewards_query]
        
        last_redemptions = LoyaltyVoucher.objects.filter(status='used')\
            .select_related('user', 'reward').order_by('-used_at')[:10]
        last_10_redemptions = [
            {
                'voucher_code': v.voucher_code,
                'reward_name': v.reward.name,
                'user_email': v.user.email,
                'used_at': v.used_at.isoformat() if v.used_at else None
            } for v in last_redemptions
        ]

        return Response({
            'total_points_issued': issued,
            'total_points_redeemed': redeemed,
            'total_active_users': active_users,
            'tier_distribution': tier_distribution,
            'voucher_stats': voucher_stats,
            'thirty_day_trend': thirty_day_trend,
            'top_5_rewards': top_5_rewards,
            'last_10_redemptions': last_10_redemptions
        })

    @extend_schema(
        summary="List all users with their loyalty points",
        responses={200: LoyaltyPointsAdminSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def users(self, request):
        queryset = LoyaltyPoints.objects.select_related('user').all().order_by('-points_balance')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LoyaltyPointsAdminSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = LoyaltyPointsAdminSerializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(tags=['Admin Loyalty - Badges'], summary="List all loyalty badges"),
    retrieve=extend_schema(tags=['Admin Loyalty - Badges'], summary="Get a loyalty badge"),
    create=extend_schema(tags=['Admin Loyalty - Badges'], summary="Create a loyalty badge"),
    update=extend_schema(tags=['Admin Loyalty - Badges'], summary="Update a loyalty badge"),
    partial_update=extend_schema(tags=['Admin Loyalty - Badges'], summary="Partially update a loyalty badge"),
    destroy=extend_schema(tags=['Admin Loyalty - Badges'], summary="Delete a loyalty badge"),
)
class LoyaltyBadgeAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LoyaltyBadge.objects.all().order_by('display_order')
    serializer_class = LoyaltyBadgeAdminSerializer

@extend_schema_view(
    list=extend_schema(tags=['Admin Loyalty - Rewards'], summary="List all loyalty rewards"),
    retrieve=extend_schema(tags=['Admin Loyalty - Rewards'], summary="Get a loyalty reward"),
    create=extend_schema(tags=['Admin Loyalty - Rewards'], summary="Create a loyalty reward"),
    update=extend_schema(tags=['Admin Loyalty - Rewards'], summary="Update a loyalty reward"),
    partial_update=extend_schema(tags=['Admin Loyalty - Rewards'], summary="Partially update a loyalty reward"),
    destroy=extend_schema(tags=['Admin Loyalty - Rewards'], summary="Delete a loyalty reward"),
)
class LoyaltyRewardAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LoyaltyReward.objects.all().order_by('display_order')
    serializer_class = LoyaltyRewardAdminSerializer

class LoyaltyTransactionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LoyaltyTransaction.objects.all().order_by('-created_at')
    serializer_class = LoyaltyTransactionAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_id', 'transaction_type']
    ordering_fields = ['created_at', 'points_change']

@extend_schema_view(
    list=extend_schema(tags=['Admin Loyalty - Rules'], summary="List all loyalty earning rules"),
    retrieve=extend_schema(tags=['Admin Loyalty - Rules'], summary="Get an earning rule"),
    create=extend_schema(tags=['Admin Loyalty - Rules'], summary="Create an earning rule"),
    update=extend_schema(tags=['Admin Loyalty - Rules'], summary="Update an earning rule"),
    partial_update=extend_schema(tags=['Admin Loyalty - Rules'], summary="Partially update an earning rule"),
    destroy=extend_schema(tags=['Admin Loyalty - Rules'], summary="Delete an earning rule"),
)
class LoyaltyEarningRuleAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LoyaltyEarningRule.objects.all().order_by('-created_at')
    serializer_class = LoyaltyEarningRuleAdminSerializer

class AdminProductImageUploadView(views.APIView):
    """POST /api/admin/products/{id}/images/ and DELETE /api/admin/products/{id}/images/"""
    permission_classes = [IsAdminUser]
    from rest_framework.parsers import JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Upload product image (Admin)",
        request=inline_serializer("AdminProductImageUploadReq", {"image": serializers.ImageField()}),
        responses={200: inline_serializer("AdminProductImageUploadResp", {"status": serializers.CharField(), "image_url": serializers.CharField()})}
    )
    def post(self, request, id):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=id)
        # We can store in product-images/ path
        path = f"product-images/{product.id}/{image_file.name}"
        saved_path = default_storage.save(path, image_file)
        image_url = default_storage.url(saved_path)

        # Append to product's images array
        # Try to parse string if it was somehow stored as a string
        images_list = product.images or []
        if isinstance(images_list, str):
            try:
                import ast
                parsed = ast.literal_eval(images_list)
                images_list = parsed if isinstance(parsed, list) else [images_list]
            except:
                images_list = [images_list]

        if image_url not in images_list:
            images_list.append(image_url)
            
        product.images = list(images_list)
        product.save(update_fields=['images'])

        return Response({'status': 'Image uploaded successfully', 'image_url': image_url})

    @extend_schema(
        summary="Remove product image (Admin)",
        request=inline_serializer("AdminProductImageDeleteReq", {"image_url": serializers.CharField()}),
        responses={200: inline_serializer("AdminProductImageDeleteResp", {"status": serializers.CharField()})}
    )
    def delete(self, request, id):
        image_url = request.data.get('image_url')
        if not image_url:
            return Response({'error': 'image_url is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        product = get_object_or_404(Product, id=id)
        
        images_list = product.images or [] or []
        if isinstance(images_list, str):
            try:
                import ast
                parsed = ast.literal_eval(images_list)
                images_list = parsed if isinstance(parsed, list) else [images_list]
            except:
                images_list = [images_list]
                
        if image_url in images_list:
            images_list.remove(image_url)
            product.images = list(images_list)
            product.save(update_fields=['images'])
            
            # Optional: Delete from storage
            try:
                # Extract path from URL if possible
                pass
            except Exception:
                pass
                
            return Response({'status': 'Image removed successfully'})
        return Response({'error': 'Image URL not found in product'}, status=status.HTTP_404_NOT_FOUND)


class AdminBannerImageUploadView(views.APIView):
    """POST /api/admin/content/banners/{id}/images/ and DELETE /api/admin/content/banners/{id}/images/"""
    permission_classes = [IsAdminUser]
    from rest_framework.parsers import JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Upload banner background image (Admin)",
        request=inline_serializer("AdminBannerImageUploadReq", {"image": serializers.ImageField()}),
        responses={200: inline_serializer("AdminBannerImageUploadResp", {"status": serializers.CharField(), "image_url": serializers.CharField()})}
    )
    def post(self, request, id):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        banner = get_object_or_404(PromotionalBanner, id=id)
        path = f"banners/{banner.id}/{image_file.name}"
        saved_path = default_storage.save(path, image_file)
        image_url = default_storage.url(saved_path)

        banner.background_image_url = image_url
        banner.save(update_fields=['background_image_url'])

        return Response({'status': 'Banner image uploaded successfully', 'image_url': image_url})

    @extend_schema(
        summary="Remove banner background image (Admin)",
        responses={200: inline_serializer("AdminBannerImageDeleteResp", {"status": serializers.CharField()})}
    )
    def delete(self, request, id):
        banner = get_object_or_404(PromotionalBanner, id=id)
        if banner.background_image_url:
            banner.background_image_url = None
            banner.save(update_fields=['background_image_url'])
            return Response({'status': 'Banner image removed successfully'})
        return Response({'error': 'Banner has no background image'}, status=status.HTTP_400_BAD_REQUEST)

def _parse_version(v: str):
    """Helper to convert '1.0.5' into (1, 0, 5) for comparison"""
    try:
        return tuple(int(x) for x in v.strip().split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)

class VersionCheckView(views.APIView):
    """
    Public API for the mobile app to check if an update is available.
    POST /api/version-check/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.Serializer # For spectacular

    @extend_schema(
        summary="Check for app update",
        request=inline_serializer(
            name="VersionCheckRequest",
            fields={
                "platform": serializers.ChoiceField(choices=["android", "iOS"]),
                "version": serializers.CharField()
            }
        ),
        responses={200: inline_serializer(
            name="VersionCheckResponse",
            fields={
                "status": serializers.IntegerField(),
                "data": inline_serializer(
                    name="VersionCheckData",
                    fields={
                        "isUpdateAvailable": serializers.BooleanField(),
                        "playStoreUrl": serializers.CharField(allow_blank=True),
                        "appStoreUrl": serializers.CharField(allow_blank=True),
                    }
                )
            }
        )}
    )
    def post(self, request):
        platform = request.data.get('platform')
        version = request.data.get('version')
        
        if not platform or not version:
            return Response({"error": "platform and version are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        platform_lower = platform.lower()
        if platform_lower not in ['android', 'ios']:
            return Response({"error": "platform must be 'android' or 'iOS'"}, status=status.HTTP_400_BAD_REQUEST)

        # Get settings
        version_setting = AppSettings.objects.filter(setting_key=f"app_version_{platform_lower}").first()
        urls_setting = AppSettings.objects.filter(setting_key="app_store_urls").first()

        latest_version = version_setting.setting_value.get('version', '1.0.0') if version_setting else '1.0.0'
        
        urls_data = urls_setting.setting_value if urls_setting else {}
        play_store_url = urls_data.get('playStoreUrl', '')
        app_store_url = urls_data.get('appStoreUrl', '')

        # Compare versions
        is_update_available = _parse_version(version) < _parse_version(latest_version)

        # Build response
        if not is_update_available:
            play_store_url = ""
            app_store_url = ""

        return Response({
            "status": 200,
            "data": {
                "isUpdateAvailable": is_update_available,
                "playStoreUrl": play_store_url,
                "appStoreUrl": app_store_url
            }
        })


class AdminVersionUpdateView(views.APIView):
    """
    Internal API for the admin to manage app versions.
    GET /api/admin/app-version/
    PUT /api/admin/app-version/
    """
    permission_classes = [IsAdminUser]
    serializer_class = serializers.Serializer # For spectacular

    @extend_schema(
        summary="Get current app versions (Admin)",
        responses={200: inline_serializer(
            name="AdminAppVersionGetResponse",
            fields={
                "success": serializers.BooleanField(),
                "data": inline_serializer(
                    name="AdminAppVersionData",
                    fields={
                        "android": serializers.DictField(),
                        "ios": serializers.DictField(),
                        "urls": serializers.DictField()
                    }
                )
            }
        )}
    )
    def get(self, request):
        android = AppSettings.objects.filter(setting_key="app_version_android").first()
        ios = AppSettings.objects.filter(setting_key="app_version_ios").first()
        urls = AppSettings.objects.filter(setting_key="app_store_urls").first()

        return Response({
            "success": True,
            "data": {
                "android": android.setting_value if android else {"version": "1.0.0"},
                "ios": ios.setting_value if ios else {"version": "1.0.0"},
                "urls": urls.setting_value if urls else {"playStoreUrl": "", "appStoreUrl": ""}
            }
        })

    @extend_schema(
        summary="Update app versions (Admin)",
        request=inline_serializer(
            name="AdminAppVersionPutRequest",
            fields={
                "android": serializers.CharField(required=False),
                "ios": serializers.CharField(required=False),
                "playStoreUrl": serializers.CharField(required=False, allow_blank=True),
                "appStoreUrl": serializers.CharField(required=False, allow_blank=True)
            }
        )
    )
    def put(self, request):
        data = request.data
        
        if 'android' in data:
            android_setting, _ = AppSettings.objects.get_or_create(setting_key="app_version_android", defaults={"setting_value": {}})
            android_setting.setting_value = {"version": data['android']}
            android_setting.save()

        if 'ios' in data:
            ios_setting, _ = AppSettings.objects.get_or_create(setting_key="app_version_ios", defaults={"setting_value": {}})
            ios_setting.setting_value = {"version": data['ios']}
            ios_setting.save()

        if 'playStoreUrl' in data or 'appStoreUrl' in data:
            urls_setting, _ = AppSettings.objects.get_or_create(setting_key="app_store_urls", defaults={"setting_value": {}})
            current_urls = urls_setting.setting_value
            if 'playStoreUrl' in data:
                current_urls['playStoreUrl'] = data['playStoreUrl']
            if 'appStoreUrl' in data:
                current_urls['appStoreUrl'] = data['appStoreUrl']
            urls_setting.setting_value = current_urls
            urls_setting.save()
            
        return self.get(request)

class AdminCategoryImageUploadView(views.APIView):
    """POST /api/admin/categories/{id}/images/ and DELETE /api/admin/categories/{id}/images/"""
    permission_classes = [IsAdminUser]
    from rest_framework.parsers import JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Upload category image (Admin)",
        request=inline_serializer("AdminCategoryImageUploadReq", {"image": serializers.ImageField()}),
        responses={200: inline_serializer("AdminCategoryImageUploadResp", {"status": serializers.CharField(), "image_url": serializers.CharField()})}
    )
    def post(self, request, id):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        category = get_object_or_404(Category, id=id)
        path = f"category-images/{category.id}/{image_file.name}"
        saved_path = default_storage.save(path, image_file)
        image_url = default_storage.url(saved_path)

        category.image_url = image_url
        category.save(update_fields=['image_url'])

        logger.info("admin_uploaded_category_image", admin_id=request.user.id, category_id=category.id)
        return Response({'status': 'uploaded', 'image_url': image_url})

    @extend_schema(
        summary="Delete category image (Admin)",
        request=inline_serializer("AdminCategoryImageDeleteReq", {"image_url": serializers.CharField()}),
        responses={200: inline_serializer("AdminCategoryImageDeleteResp", {"status": serializers.CharField()})}
    )
    def delete(self, request, id):
        image_url = request.data.get('image_url')
        if not image_url:
            return Response({'error': 'image_url required'}, status=status.HTTP_400_BAD_REQUEST)
            
        category = get_object_or_404(Category, id=id)
        if category.image_url == image_url:
            category.image_url = None
            category.save(update_fields=['image_url'])
            logger.info("admin_deleted_category_image", admin_id=request.user.id, category_id=category.id)
            return Response({'status': 'deleted'})
        return Response({'error': 'Image not found in category'}, status=status.HTTP_404_NOT_FOUND)
