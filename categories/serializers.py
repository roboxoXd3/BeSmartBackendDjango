from rest_framework import serializers
from .models import Category, Subcategory


class SubcategorySerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(source='category.id', read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'description', 'category_id', 'is_active',
                  'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
