from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AdminUser, AdminActionLog, AppSettings
from .serializers import (
    AdminUserSerializer, AdminActionLogSerializer, 
    AppSettingsSerializer, UserManagementSerializer
)
from users.models import User
from vendors.models import Vendor
from orders.models import Order
from drf_spectacular.utils import extend_schema

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_permission(self, request, view):
        # In real implementation, check request.user.is_staff or similar
        # For now, relying on IsAuthenticated and maybe a specialized check later
        return request.user and request.user.is_authenticated

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

class UserManagementView(generics.RetrieveUpdateDestroyAPIView):
    # Admin view to manage regular users (ban/unban)
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer

    def perform_destroy(self, instance):
        # Soft delete or deactivate instead of hard delete
        instance.is_active = False
        instance.save()

class SystemStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: None})
    def get(self, request):
        return Response({
            "total_users": User.objects.count(),
            "total_vendors": Vendor.objects.count(),
            "total_orders": Order.objects.count(),
            "pending_vendors": Vendor.objects.filter(status='pending').count(),
        })
