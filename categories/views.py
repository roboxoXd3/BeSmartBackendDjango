import uuid as uuid_module
from rest_framework import generics, permissions, filters, views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import connection
from .models import Category, Subcategory
from .serializers import CategorySerializer, SubcategorySerializer
from products.models import Product
from products.serializers import ProductListSerializer
from drf_spectacular.utils import extend_schema

class SubcategoryListView(generics.ListAPIView):
    """GET /api/subcategories/ — all active subcategories (Flutter fetches all at once
    and filters client-side by category_id)."""
    permission_classes = [permissions.AllowAny]
    serializer_class = SubcategorySerializer
    queryset = Subcategory.objects.filter(is_active=True).select_related('category').order_by('name')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategorySubcategoriesView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SubcategorySerializer

    def get_queryset(self):
        category = get_object_or_404(Category, id=self.kwargs['id'], is_active=True)
        return Subcategory.objects.filter(category=category, is_active=True).order_by('name')

    @extend_schema(summary="List category subcategories")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class CategoryProductsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        get_object_or_404(Category, id=self.kwargs['id'], is_active=True)
        return Product.objects.filter(category_id=self.kwargs['id'], status='active', approval_status='approved')

    @extend_schema(summary="List products in category")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @extend_schema(
        summary="List all categories",
        description="Get a list of active categories"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'


class CategorySizeChartView(views.APIView):
    """GET /api/categories/{id}/size-chart/
    Gap 13: getSizeChartByCategory — return size chart template for a category."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        category = get_object_or_404(Category, id=id, is_active=True)
        with connection.cursor() as c:
            c.execute("""
                SELECT id, name, category_id, subcategory, measurement_types,
                       measurement_instructions, template_data, size_recommendations,
                       is_active, approval_status, created_at, updated_at
                FROM vendor_size_chart_templates
                WHERE category_id = %s AND is_active = true AND approval_status = 'approved'
                ORDER BY created_at DESC
                LIMIT 1
            """, [str(category.id)])
            row = c.fetchone()
            cols = [col[0] for col in c.description] if c.description else []

        if not row:
            return Response(
                {"detail": "No size chart for this category."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = dict(zip(cols, row))
        for k, v in list(data.items()):
            if hasattr(v, 'isoformat'):
                data[k] = v.isoformat()
            elif isinstance(v, uuid_module.UUID):
                data[k] = str(v)

        template_data = data.get('template_data')
        data['entries'] = template_data.get('entries', []) if isinstance(template_data, dict) else []

        return Response(data)


class CategoryHasSizeChartView(views.APIView):
    """GET /api/categories/{id}/has-size-chart/
    Gap 15: hasSizeChartForCategory — boolean check."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        category = get_object_or_404(Category, id=id, is_active=True)
        with connection.cursor() as c:
            c.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM vendor_size_chart_templates
                    WHERE category_id = %s AND is_active = true AND approval_status = 'approved'
                )
            """, [str(category.id)])
            has_chart = c.fetchone()[0]
        return Response({"has_size_chart": has_chart})
