from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from .models import PromotionalBanner, SupportInfo, HeroSection, ContactInfo
from .serializers import (
    PromotionalBannerSerializer, SupportInfoSerializer,
    HeroSectionSerializer, ContactInfoSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter

class HeroSectionView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = HeroSectionSerializer

    @extend_schema(summary="Get hero section (homepage)")
    def get(self, request):
        obj = HeroSection.objects.filter(is_active=True).first()
        if not obj:
            return Response({"detail": "No hero section configured."}, status=404)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

class ContactInfoView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactInfoSerializer

    @extend_schema(summary="Get contact info")
    def get(self, request):
        obj = ContactInfo.objects.first()
        if not obj:
            return Response({"detail": "No contact info configured."}, status=404)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

class SupportInfoFilterView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SupportInfoSerializer
    pagination_class = None

    def get_queryset(self):
        qs = SupportInfo.objects.all().order_by('order_index')
        info_type = self.request.query_params.get('type', '').strip()
        if info_type:
            qs = qs.filter(type__iexact=info_type)
        return qs

    @extend_schema(parameters=[OpenApiParameter('type', str, description='Filter by type: faq, contact, policy')])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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
