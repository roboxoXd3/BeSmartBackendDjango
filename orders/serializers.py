from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress
from products.serializers import ProductListSerializer


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'user_id', 'name', 'phone',
            'address_line1', 'address_line2',
            'city', 'state', 'zip', 'country',
            'is_default', 'type', 'created_at',
        ]
        read_only_fields = ['id', 'user_id', 'created_at']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'selected_size', 'selected_color']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'updated_at']

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'selected_size', 'selected_color']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user', 'order_number', 'created_at', 'updated_at', 'status']

class OrderItemInputSerializer(serializers.Serializer):
    """For direct item-list order creation (Gap 27: cart mismatch)."""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    selected_size = serializers.CharField(required=False, default='', allow_blank=True)
    selected_color = serializers.CharField(required=False, default='', allow_blank=True)


class CreateOrderSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    payment_method_id = serializers.UUIDField(required=False, allow_null=True)
    shipping_method = serializers.ChoiceField(
        choices=['cash_on_delivery', 'credit_card', 'debit_card', 'upi', 'net_banking'],
        default='cash_on_delivery'
    )
    loyalty_voucher_code = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    # Gap 24: Squad payment fields
    squad_transaction_ref = serializers.CharField(required=False, allow_blank=True)
    squad_gateway_ref = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    escrow_status = serializers.CharField(required=False, allow_blank=True)
    # Gap 27: Direct items list (alternative to cart-based flow)
    items = OrderItemInputSerializer(many=True, required=False)