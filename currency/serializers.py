from rest_framework import serializers
from .models import CurrencyRate, UserCurrencyPreference

class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'
        read_only_fields = ['last_updated']

class UserCurrencyPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCurrencyPreference
        fields = ['preferred_currency'] # User only updates this field
        read_only_fields = ['created_at', 'updated_at', 'user']

class CurrencyConversionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    from_currency = serializers.CharField(max_length=10)
    to_currency = serializers.CharField(max_length=10)
    converted_amount = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    rate = serializers.DecimalField(max_digits=20, decimal_places=10, read_only=True)
