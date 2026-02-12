from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Storing image URL as text to match existing DB schema initially
    images = models.TextField(default='https://example.com/default.jpg') 
    # Use ArrayField because DB column is ARRAY type
    sizes = ArrayField(models.TextField(), default=list, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews = models.IntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    category_id = models.UUIDField(null=True, blank=True) # Foreign Key logic to be added later or linked to Category model
    brand = models.TextField(null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    added_date = models.DateTimeField(auto_now_add=True)
    vendor_id = models.UUIDField(null=True, blank=True) # Foreign key to Vendor
    approval_status = models.CharField(max_length=20, default='approved')
    sku = models.TextField(unique=True, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    colors = models.JSONField(default=dict) # Should be valid JSON
    
    class Meta:
        db_table = 'products'
        ordering = ['-added_date']

    def __str__(self):
        return self.name
