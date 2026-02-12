from rest_framework import serializers
from .models import PromotionalBanner, SupportInfo

class PromotionalBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionalBanner
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']

class SupportInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportInfo
        fields = '__all__'
        read_only_fields = ['created_at']
