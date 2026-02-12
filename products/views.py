from rest_framework import generics, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductListSerializer, ProductDetailSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().filter(status='active', approval_status='approved')
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = {
        'category_id': ['exact'],
        'is_featured': ['exact'],
        'is_new_arrival': ['exact'],
        'is_on_sale': ['exact'],
        'price': ['gte', 'lte'],
        'brand': ['exact', 'icontains'],
        'vendor_id': ['exact'],
    }
    
    # Search fields (Search vector in DB is more complex, using simple icontains for now)
    search_fields = ['name', 'description', 'brand', 'sku']
    
    # Ordering fields
    ordering_fields = ['price', 'added_date', 'rating', 'orders_count']
    ordering = ['-added_date']

    @extend_schema(
        summary="List all products",
        description="Get a list of products with filtering, searching and sorting capabilities.",
        parameters=[
            OpenApiParameter(name='price__gte', description='Minimum price', required=False, type=float),
            OpenApiParameter(name='price__lte', description='Maximum price', required=False, type=float),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = 'id'

class FeaturedProductsView(generics.ListAPIView):
    queryset = Product.objects.filter(is_featured=True, status='active', approval_status='approved')
    serializer_class = ProductListSerializer
    pagination_class = None # Usually featured list is small

class NewArrivalsView(generics.ListAPIView):
    queryset = Product.objects.filter(is_new_arrival=True, status='active', approval_status='approved').order_by('-added_date')
    serializer_class = ProductListSerializer
    pagination_class = None

class OnSaleProductsView(generics.ListAPIView):
    queryset = Product.objects.filter(is_on_sale=True, status='active', approval_status='approved')
    serializer_class = ProductListSerializer

class ProductSearchView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'brand']
    
    def get_queryset(self):
        # Could implement more specific AI search logic here later
        return Product.objects.filter(status='active', approval_status='approved')
