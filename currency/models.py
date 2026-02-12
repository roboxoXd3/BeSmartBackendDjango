from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class CurrencyRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    currency_code = models.CharField(max_length=10, unique=True) # USD, EUR, GBP, NGN
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=10) # Rate relative to base currency (e.g. NGN)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'currency_rates'

class UserCurrencyPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='currency_preference')
    preferred_currency = models.CharField(max_length=10, default='NGN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_currency_preferences'
