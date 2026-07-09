from rest_framework import serializers
from .models import Product, ProductReview, ProductQuestion

class ProductListSerializer(serializers.ModelSerializer):
    ratings = serializers.FloatField(source='rating', read_only=True)
    category = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'images', 'rating', 'ratings', 'reviews',
            'in_stock', 'discount_percentage', 'is_on_sale',
            'sale_price', 'is_featured', 'is_new_arrival',
            'sku', 'status', 'stock_quantity',
            'category_id', 'subcategory_id', 'category',
            'sizes', 'base_currency', 'cod_allowed',
            'description', 'approval_status', 'rejection_reason',
            'video_url', 'colors', 'subtitle', 'brand',
            'vendor_id', 'vendor_name', 'mrp', 'currency', 'created_at',
        ]
        
    def get_vendor_name(self, obj):
        if hasattr(obj, 'vendor_name_annotated'):
            return obj.vendor_name_annotated
        if not obj.vendor_id:
            return None
        from vendors.models import Vendor
        try:
            vendor = Vendor.objects.get(id=obj.vendor_id)
            return vendor.business_name
        except Vendor.DoesNotExist:
            return None
        
    def get_category(self, obj):
        if hasattr(obj, 'category_name'):
            return obj.category_name
        if not obj.category_id:
            return None
        from categories.models import Category
        try:
            cat = Category.objects.get(id=obj.category_id)
            return cat.name
        except Category.DoesNotExist:
            return None

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['approval_status', 'vendor_id']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.email', read_only=True)
    class Meta:
        model = ProductReview
        fields = ['id', 'product_id', 'user_id', 'user_name', 'order_id', 'rating', 'title', 'content', 'images', 'verified_purchase', 'helpful_count', 'reported_count', 'status', 'vendor_response', 'created_at', 'updated_at']


class ProductReviewCreateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField()
    content = serializers.CharField()
    images = serializers.ListField(child=serializers.URLField(), required=False, default=list)


class ProductQuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.email', read_only=True)
    class Meta:
        model = ProductQuestion
        fields = ['id', 'product_id', 'user_id', 'user_name', 'question', 'answer', 'answered_by', 'answered_at', 'is_helpful_count', 'is_verified', 'status', 'vendor_response', 'created_at', 'updated_at']


class ProductQuestionCreateSerializer(serializers.Serializer):
    question = serializers.CharField()
