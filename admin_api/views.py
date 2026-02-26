from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AdminUser, AdminActionLog, AppSettings
from .serializers import (
    AdminUserSerializer, AdminActionLogSerializer, 
    AppSettingsSerializer, UserManagementSerializer,
    VendorAdminSerializer, PayoutAdminSerializer,
    TransactionAdminSerializer
)
from users.models import User
from vendors.models import Vendor
from orders.models import Order
from products.models import Product
from vendors.models import VendorPayout, EscrowTransaction, VendorFollow, PayoutTransaction
from products.serializers import ProductListSerializer, ProductDetailSerializer
from orders.serializers import OrderSerializer
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from rest_framework.decorators import action

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
    serializer_class = UserManagementSerializer

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
        user = self.get_object()
        action_type = request.data.get('action')
        if action_type == 'suspend':
            user.is_active = False
        elif action_type == 'activate':
            user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'status': 'user status updated', 'is_active': user.is_active})

class VendorAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorAdminSerializer

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
        vendor = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes')
        
        if new_status in dict(Vendor.STATUS_CHOICES).keys():
            vendor.status = new_status
        if admin_notes:
            vendor.admin_notes = admin_notes
            
        vendor.save()
        return Response({'status': 'vendor status updated', 'vendor_status': vendor.status})

class SystemStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Admin dashboard overall statistics",
        responses={200: inline_serializer(
            name="AdminStatsResponse",
            fields={
                "total_users": serializers.IntegerField(),
                "total_vendors": serializers.IntegerField(),
                "total_orders": serializers.IntegerField(),
                "pending_vendors": serializers.IntegerField(),
                "total_revenue": serializers.FloatField(),
                "pending_payouts": serializers.FloatField()
            }
        )}
    )
    def get(self, request):
        from django.db.models import Sum
        total_revenue = Order.objects.filter(status__in=['delivered', 'shipped', 'confirmed']).aggregate(total=Sum('total'))['total'] or 0.00
        total_payouts_pending = VendorPayout.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0.00
            
        return Response({
            "total_users": User.objects.count(),
            "total_vendors": Vendor.objects.count(),
            "total_orders": Order.objects.count(),
            "pending_vendors": Vendor.objects.filter(status='pending').count(),
            "total_revenue": float(total_revenue),
            "pending_payouts": float(total_payouts_pending)
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
        parameters=[OpenApiParameter("period", OpenApiTypes.STR, description="E.g., 7d, 30d, 90d, 1y")],
        responses={200: inline_serializer(
            name="AdminRevenueChartResponse",
            fields={
                "trend": serializers.ListField(child=serializers.DictField()),
                "period": serializers.CharField()
            }
        )}
    )
    def get(self, request):
        period = request.query_params.get('period', '30d')
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import TruncDate
        from django.db.models import Sum, Count
        
        days = 30
        if period == '7d': days = 7
        elif period == '90d': days = 90
        elif period == '1y': days = 365
        
        start_date = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(created_at__gte=start_date, status__in=['delivered', 'shipped', 'confirmed'])
        
        daily_sales = list(orders
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(revenue=Sum('total'), orders_count=Count('id'))
            .order_by('date'))
        
        formatted_daily_sales = [
            {"date": entry["date"].isoformat(), "revenue": float(entry["revenue"] or 0), "orders": entry["orders_count"]}
            for entry in daily_sales
        ]
        
        return Response({
            "trend": formatted_daily_sales,
            "period": period
        })

class ProductAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all().order_by('-added_date')

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
            return Response({'status': 'approval status updated', 'approval_status': product.approval_status})
        return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)

class OrderAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer

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
            return Response({'status': 'order status updated', 'order_status': order.status})
        return Response({'error': 'missing status'}, status=status.HTTP_400_BAD_REQUEST)

class PayoutAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = VendorPayout.objects.all().order_by('-requested_at')
    serializer_class = PayoutAdminSerializer

    @extend_schema(
        summary="Update payout status (process/complete/fail)",
        request=inline_serializer(
            name="PayoutStatusAdminRequest",
            fields={
                "status": serializers.ChoiceField(choices=["pending", "processing", "completed", "failed"]),
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
        payout = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes')
        
        from django.utils import timezone
        if new_status in ['pending', 'processing', 'completed', 'failed']:
            payout.status = new_status
            if new_status == 'completed':
                payout.completed_at = timezone.now()
            elif new_status == 'processing':
                payout.processed_at = timezone.now()
        
        if admin_notes is not None:
            payout.admin_notes = admin_notes
            
        payout.save()
        return Response({'status': 'payout updated', 'payout_status': payout.status})

class TransactionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = PayoutTransaction.objects.all().order_by('-created_at')
    serializer_class = TransactionAdminSerializer

class LoyaltyAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer # Or a dedicated Loyalty user serializer

    @extend_schema(
        summary="Add loyalty points to user",
        request=inline_serializer(
            name="LoyaltyPointsAdminRequest",
            fields={"points": serializers.IntegerField()}
        ),
        responses={200: inline_serializer(
            name="LoyaltyPointsAdminResponse",
            fields={
                "message": serializers.CharField(), 
                "loyalty_points_earned": serializers.IntegerField(required=False),
                "user": serializers.CharField(required=False)
            }
        )}
    )
    @action(detail=True, methods=['post'], url_path='points')
    def points(self, request, pk=None):
        user = self.get_object()
        points = int(request.data.get('points', 0))
        if points != 0 and hasattr(user, 'loyalty_points_earned'):
            user.loyalty_points_earned += points
            user.save(update_fields=['loyalty_points_earned'])
            return Response({'message': f'{points} points applied.', 'loyalty_points_earned': user.loyalty_points_earned})
        return Response({'message': f'{points} points (simulated).', 'user': user.id})
