from rest_framework import serializers
from payments.models import Payment, Refund, PaymentMethod
from orders.models import Order


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_ref', 'amount', 'currency',
            'status', 'payment_method', 'checkout_url',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'transaction_ref', 'checkout_url', 'created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    email = serializers.EmailField(required=False)
    currency = serializers.CharField(max_length=10, required=False, default='NGN')

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
            if order.payment_status == 'paid':
                raise serializers.ValidationError("Order already paid")
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")


class VerifyPaymentSerializer(serializers.Serializer):
    transaction_ref = serializers.CharField()


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'refund_type', 'amount', 'reason', 'status', 'created_at']
