from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress
from products.serializers import ProductListSerializer
from payments.models import PaymentMethod
from payments.serializers import PaymentMethodSerializer


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

    @extend_schema_field(serializers.IntegerField())
    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    @extend_schema_field(serializers.FloatField())
    def get_total_price(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'products', 'quantity', 'price', 'selected_size', 'selected_color']

class OrderListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        iterable = data.all() if hasattr(data, 'all') else data
        address_ids = {order.address_id for order in iterable if order.address_id}
        pm_ids = {order.payment_method_id for order in iterable if order.payment_method_id}
        
        if address_ids:
            self.context['prefetched_addresses'] = {
                a.id: ShippingAddressSerializer(a).data 
                for a in ShippingAddress.objects.filter(id__in=address_ids)
            }
        
        if pm_ids:
            self.context['prefetched_payment_methods'] = {
                p.id: PaymentMethodSerializer(p).data 
                for p in PaymentMethod.objects.filter(id__in=pm_ids)
            }
            
        return super().to_representation(data)

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(source='items', many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        list_serializer_class = OrderListSerializer
        fields = '__all__'
        read_only_fields = ['user', 'order_number', 'created_at', 'updated_at', 'status']

    @extend_schema_field(ShippingAddressSerializer)
    def get_shipping_address(self, obj):
        if not obj.address_id:
            return None
        prefetched = self.context.get('prefetched_addresses')
        if prefetched is not None:
            return prefetched.get(obj.address_id)
        try:
            addr = ShippingAddress.objects.get(id=obj.address_id)
            return ShippingAddressSerializer(addr).data
        except ShippingAddress.DoesNotExist:
            return None

    @extend_schema_field(PaymentMethodSerializer)
    def get_payment_method(self, obj):
        if not obj.payment_method_id:
            return None
        prefetched = self.context.get('prefetched_payment_methods')
        if prefetched is not None:
            return prefetched.get(obj.payment_method_id)
        try:
            pm = PaymentMethod.objects.get(id=obj.payment_method_id)
            return PaymentMethodSerializer(pm).data
        except PaymentMethod.DoesNotExist:
            return None

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