from rest_framework import serializers
from .models import Product

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'images', 'rating', 'reviews', 
            'in_stock', 'discount_percentage', 'is_on_sale', 
            'sale_price', 'is_featured', 'is_new_arrival', 
            'sku', 'status', 'stock_quantity'
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
