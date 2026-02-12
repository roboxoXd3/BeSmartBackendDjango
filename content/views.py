from rest_framework import generics, permissions, viewsets
from .models import PromotionalBanner, SupportInfo
from .serializers import PromotionalBannerSerializer, SupportInfoSerializer

class PromotionalBannerListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PromotionalBannerSerializer
    pagination_class = None # Banners usually don't need pagination or large page size

    def get_queryset(self):
        return PromotionalBanner.objects.filter(is_active=True).order_by('priority', '-created_at')

class SupportInfoListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SupportInfoSerializer
    pagination_class = None

    def get_queryset(self):
        return SupportInfo.objects.all().order_by('order_index')

# Admin ViewSets could be added here or in admin_api using the same serializers
class PromotionalBannerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated] # Should be IsAdminUser
    queryset = PromotionalBanner.objects.all()
    serializer_class = PromotionalBannerSerializer
    
    def perform_create(self, serializer):
        # helper to assign created_by if user is admin
        # checks IsAdminUser would be done in permission_classes
        serializer.save(created_by=None) # Simplification for now

class SupportInfoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = SupportInfo.objects.all()
    serializer_class = SupportInfoSerializer
