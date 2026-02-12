from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet, AdminActionLogListView, 
    AppSettingsViewSet, UserManagementView, SystemStatsView
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'settings', AppSettingsViewSet, basename='app-settings')

urlpatterns = [
    path('logs/', AdminActionLogListView.as_view(), name='admin-logs'),
    path('stats/', SystemStatsView.as_view(), name='admin-stats'),
    path('manage-users/<int:pk>/', UserManagementView.as_view(), name='admin-manage-user'),
    path('', include(router.urls)),
]
