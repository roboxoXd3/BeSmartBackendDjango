from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class CurrencyRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_currency = models.TextField()
    to_currency = models.TextField()
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    source = models.TextField(default='manual')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'currency_rates'
        managed = False

class UserCurrencyPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='currency_preference')
    preferred_currency = models.TextField(default='NGN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_currency_preferences'
        managed = False
