from rest_framework import serializers
from .models import CurrencyRate, UserCurrencyPreference

class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ['id', 'from_currency', 'to_currency', 'rate', 'source', 'updated_at']

class UserCurrencyPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCurrencyPreference
        fields = ['preferred_currency']

class CurrencyConversionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    from_currency = serializers.CharField(max_length=10)
    to_currency = serializers.CharField(max_length=10)
