from rest_framework import serializers
from .models import Product, ProductReview, ProductQuestion

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'images', 'rating', 'reviews',
            'in_stock', 'discount_percentage', 'is_on_sale',
            'sale_price', 'is_featured', 'is_new_arrival',
            'sku', 'status', 'stock_quantity',
            'category_id', 'subcategory_id',
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


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
