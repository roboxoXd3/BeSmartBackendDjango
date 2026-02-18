from django.db import models
from django.contrib.auth import get_user_model
import uuid
from products.models import Product

User = get_user_model()

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    selected_size = models.CharField(max_length=50) # Assuming size is text
    selected_color = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist'
        unique_together = ('user', 'product')

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('returned', 'Returned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address_id = models.UUIDField(null=True, blank=True)
    payment_method_id = models.UUIDField(null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    order_number = models.CharField(max_length=100, null=True, blank=True)
    vendor_id = models.UUIDField(null=True, blank=True) # Link to Vendor
    
    # Tracking
    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    
    # Financials
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Payment & Loyalty info from schema
    squad_transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    squad_gateway_ref = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=50, default='pending')
    loyalty_points_earned = models.IntegerField(default=0)
    
    # Vendor & Escrow
    escrow_status = models.CharField(max_length=50, default='none')
    escrow_release_date = models.DateTimeField(null=True, blank=True)
    vendor_payout_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        prefix = 'ORD'
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return f"{prefix}{random_part}"

class ShippingAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    name = models.TextField()
    phone = models.TextField()
    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True, null=True)
    city = models.TextField()
    state = models.TextField()
    zip = models.TextField()
    country = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    type = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shipping_addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.address_line1}, {self.city}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_size = models.CharField(max_length=50)
    selected_color = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_items'
