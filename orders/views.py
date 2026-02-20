from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models, transaction
from .models import Cart, CartItem, Order, OrderItem, Wishlist, ShippingAddress
from products.models import Product
from .serializers import (
    CartSerializer, CartItemSerializer, 
    OrderSerializer, CreateOrderSerializer,
    WishlistSerializer, ShippingAddressSerializer
)
from drf_spectacular.utils import extend_schema


# ──────────────────────────────────────────────
# Shipping Addresses
# ──────────────────────────────────────────────

class ShippingAddressListCreateView(generics.ListCreateAPIView):
    """GET  /api/shipping-addresses/  — list user addresses
       POST /api/shipping-addresses/  — create a new address"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ShippingAddress.objects.none()
        return ShippingAddress.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        is_default = serializer.validated_data.get('is_default', False)

        # If this is the user's first address, force default
        if not ShippingAddress.objects.filter(user=user).exists():
            is_default = True

        # If setting as default, clear others
        if is_default:
            ShippingAddress.objects.filter(user=user, is_default=True).update(is_default=False)

        serializer.save(user=user, is_default=is_default)


class ShippingAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/shipping-addresses/{id}/  — retrieve
       PATCH  /api/shipping-addresses/{id}/  — update
       DELETE /api/shipping-addresses/{id}/  — delete"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShippingAddressSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ShippingAddress.objects.none()
        return ShippingAddress.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        is_default = serializer.validated_data.get('is_default', None)
        if is_default:
            ShippingAddress.objects.filter(
                user=self.request.user, is_default=True
            ).update(is_default=False)
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        was_default = instance.is_default
        user = instance.user
        instance.delete()
        # If deleted address was default, promote the first remaining
        if was_default:
            first = ShippingAddress.objects.filter(user=user).first()
            if first:
                first.is_default = True
                first.save(update_fields=['is_default'])


class ShippingAddressSetDefaultView(views.APIView):
    """POST /api/shipping-addresses/{id}/set-default/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: {'type': 'object', 'properties': {
            'success': {'type': 'boolean'},
            'message': {'type': 'string'},
        }}},
    )
    @transaction.atomic
    def post(self, request, pk):
        address = get_object_or_404(
            ShippingAddress, pk=pk, user=request.user
        )
        ShippingAddress.objects.filter(
            user=request.user, is_default=True
        ).update(is_default=False)
        address.is_default = True
        address.save(update_fields=['is_default'])
        return Response({
            'success': True,
            'message': 'Default address updated',
        })


# ──────────────────────────────────────────────
# Cart
# ──────────────────────────────────────────────

class CartView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_object(self):
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return None
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class CartItemCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product_id = serializer.validated_data.get('product_id')
        quantity = serializer.validated_data.get('quantity', 1)
        selected_size = serializer.validated_data.get('selected_size', '')
        selected_color = serializer.validated_data.get('selected_color', '')
        
        # Check if item exists
        item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product_id=product_id,
            selected_size=selected_size,
            selected_color=selected_color,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

class CartItemUpdateView(generics.DestroyAPIView, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)


class CartClearView(views.APIView):
    """POST /api/cart/clear/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'message': {'type': 'string'}}}})
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        count, _ = CartItem.objects.filter(cart=cart).delete()
        return Response({"success": True, "message": "Cart cleared"})


class CartSummaryView(views.APIView):
    """GET /api/cart/summary/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').all()
        subtotal = sum(item.quantity * item.product.price for item in items)
        return Response({
            "item_count": sum(item.quantity for item in items),
            "subtotal": float(subtotal),
            "shipping_fee": 0,
            "total": float(subtotal),
            "currency": "NGN"
        })

class WishlistView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WishlistDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)


class WishlistMoveToCartView(views.APIView):
    """POST /api/wishlist/{id}/move-to-cart/ — {id} is wishlist item id"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def post(self, request, pk):
        wishlist_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
        product = wishlist_item.product
        size = product.sizes[0] if product.sizes else 'One Size'
        color = list(product.colors.keys())[0] if isinstance(product.colors, dict) and product.colors else 'Default'
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, selected_size=size, selected_color=color,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        wishlist_item.delete()
        from .serializers import CartItemSerializer
        return Response({
            "success": True,
            "message": "Item moved to cart",
            "cart_item": CartItemSerializer(cart_item).data
        })


class WishlistClearView(views.APIView):
    """DELETE /api/wishlist/clear/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={204: None})
    def delete(self, request):
        Wishlist.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        address = get_object_or_404(ShippingAddress, id=data['address_id'], user=request.user)

        # Gap 27: Support both cart-based and direct-items order creation
        direct_items = data.get('items')
        if direct_items:
            # Direct item list provided — build order from it
            order_products = []
            for item_data in direct_items:
                product = get_object_or_404(Product, id=item_data['product_id'], status='active', approval_status='approved')
                order_products.append({
                    'product': product,
                    'quantity': item_data['quantity'],
                    'price': product.price,
                    'selected_size': item_data.get('selected_size', ''),
                    'selected_color': item_data.get('selected_color', ''),
                })
            if not order_products:
                return Response({"error": "No valid items provided"}, status=status.HTTP_400_BAD_REQUEST)
            subtotal = sum(p['quantity'] * p['price'] for p in order_products)
        else:
            # Original cart-based flow
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = list(cart.items.select_related('product').all())
            if not cart_items:
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            subtotal = sum(item.quantity * item.product.price for item in cart_items)
            order_products = None  # Marker for cart-based

        shipping_fee = 0
        discount_amount = 0

        used_voucher = None
        if data.get('loyalty_voucher_code'):
            from loyalty.models import LoyaltyVoucher
            from django.utils import timezone
            v = LoyaltyVoucher.objects.filter(
                user=request.user, voucher_code=data['loyalty_voucher_code'].strip().upper(),
                status='active', expires_at__gt=timezone.now()
            ).first()
            if v and float(subtotal) >= float(v.minimum_order_amount):
                if v.discount_type == 'discount_percentage':
                    discount_amount = subtotal * (float(v.discount_value) / 100)
                else:
                    discount_amount = float(v.discount_value)
                used_voucher = v

        total = subtotal - discount_amount + shipping_fee

        # Gap 24: Accept Squad payment fields
        squad_transaction_ref = data.get('squad_transaction_ref', '') or ''
        squad_gateway_ref = data.get('squad_gateway_ref', '')
        payment_status_val = data.get('payment_status', 'pending') or 'pending'
        escrow_status_val = data.get('escrow_status', 'none') or 'none'
        order_status = 'confirmed' if payment_status_val == 'paid' else 'pending'

        from django.utils import timezone
        order = Order.objects.create(
            user=request.user, address_id=address.id,
            payment_method_id=data.get('payment_method_id'),
            shipping_method=data.get('shipping_method', 'cash_on_delivery'),
            subtotal=subtotal, shipping_fee=shipping_fee, discount_amount=discount_amount, total=total,
            order_number=Order().generate_order_number(), notes=data.get('notes'),
            squad_transaction_ref=squad_transaction_ref,
            payment_status=payment_status_val,
            escrow_status=escrow_status_val,
            status=order_status,
        )

        if order_products is not None:
            # Direct items
            for p in order_products:
                OrderItem.objects.create(
                    order=order, product=p['product'], quantity=p['quantity'],
                    price=p['price'], selected_size=p['selected_size'], selected_color=p['selected_color']
                )
        else:
            # Cart-based
            for item in cart_items:
                OrderItem.objects.create(
                    order=order, product=item.product, quantity=item.quantity,
                    price=item.product.price, selected_size=item.selected_size, selected_color=item.selected_color
                )
            cart.items.all().delete()

        if used_voucher:
            used_voucher.status = 'used'
            used_voucher.used_at = timezone.now()
            used_voucher.order = order
            used_voucher.save(update_fields=['status', 'used_at', 'order_id'])

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = 'id'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)


class OrderCancelView(views.APIView):
    """POST /api/orders/{id}/cancel/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def post(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        if order.status not in ('pending', 'processing', 'confirmed'):
            return Response({"error": "Order cannot be cancelled"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])
        return Response({
            "success": True,
            "order": OrderSerializer(order).data,
            "message": "Order cancelled successfully"
        })


class OrderPaymentStatusView(views.APIView):
    """PATCH /api/orders/{id}/payment-status/
    Gap 25: updatePaymentStatus — update payment status after Squad callback."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {
            'payment_status': {'type': 'string'},
            'squad_gateway_ref': {'type': 'string'},
            'escrow_status': {'type': 'string'},
        }},
        responses={200: {'type': 'object'}},
    )
    def patch(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        payment_status_val = request.data.get('payment_status')
        squad_gateway_ref = request.data.get('squad_gateway_ref')
        escrow_status_val = request.data.get('escrow_status')

        update_fields = ['updated_at']
        if payment_status_val:
            order.payment_status = payment_status_val
            update_fields.append('payment_status')
            # Auto-confirm order when payment is successful
            if payment_status_val == 'paid' and order.status == 'pending':
                order.status = 'confirmed'
                update_fields.append('status')
        if squad_gateway_ref:
            order.squad_transaction_ref = squad_gateway_ref
            update_fields.append('squad_transaction_ref')
        if escrow_status_val:
            order.escrow_status = escrow_status_val
            update_fields.append('escrow_status')

        order.save(update_fields=update_fields)
        return Response({
            'success': True,
            'order': OrderSerializer(order).data,
        })


class OrderStatusUpdateView(views.APIView):
    """PATCH /api/orders/{id}/status/
    Gap 26: updateOrderStatus — general status update.
    Awards loyalty points automatically when status becomes 'delivered'."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {'status': {'type': 'string'}}},
        responses={200: {'type': 'object'}},
    )
    @transaction.atomic
    def patch(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        new_status = request.data.get('status', '').strip()
        valid_statuses = dict(Order.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Choices: {list(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = order.status
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])

        points_awarded = 0
        if new_status == 'delivered' and previous_status != 'delivered':
            points_awarded = self._award_loyalty_points(order)

        resp = {
            'success': True,
            'order': OrderSerializer(order).data,
        }
        if points_awarded:
            resp['loyalty_points_awarded'] = points_awarded
        return Response(resp)

    @staticmethod
    def _award_loyalty_points(order):
        """Award loyalty points for a delivered order based on earning rules
        and the user's tier multiplier."""
        from loyalty.models import LoyaltyPoints, LoyaltyTransaction, LoyaltyEarningRule
        from django.utils import timezone

        rule = LoyaltyEarningRule.objects.filter(
            rule_type='order_purchase',
            is_active=True,
        ).filter(
            models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=timezone.now()),
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=timezone.now()),
        ).order_by('-multiplier').first()

        if not rule:
            points_per_unit = 1.0
            rule_multiplier = 1.0
            min_order = 0
        else:
            points_per_unit = float(rule.points_per_currency_unit)
            rule_multiplier = float(rule.multiplier)
            min_order = float(rule.minimum_order_amount)

        order_total = float(order.total)
        if order_total < min_order:
            return 0

        tier_multipliers = {'bronze': 1.0, 'silver': 1.25, 'gold': 1.5, 'platinum': 2.0}
        lp, _ = LoyaltyPoints.objects.get_or_create(user=order.user)
        tier_mult = tier_multipliers.get(lp.tier or 'bronze', 1.0)

        raw_points = int(order_total * points_per_unit * rule_multiplier * tier_mult)
        if raw_points <= 0:
            return 0

        lp.points_balance = (lp.points_balance or 0) + raw_points
        lp.lifetime_points = (lp.lifetime_points or 0) + raw_points

        tiers = [('bronze', 0), ('silver', 500), ('gold', 2000), ('platinum', 5000)]
        new_tier = 'bronze'
        for t_name, t_threshold in reversed(tiers):
            if lp.lifetime_points >= t_threshold:
                new_tier = t_name
                break
        if new_tier != (lp.tier or 'bronze'):
            lp.tier = new_tier
            lp.tier_updated_at = timezone.now()

        lp.save()

        LoyaltyTransaction.objects.create(
            user=order.user,
            points_change=raw_points,
            transaction_type='earn',
            reference_type='order',
            reference_id=order.id,
            description=f'Earned {raw_points} points for order #{order.order_number}',
            points_balance_after=lp.points_balance,
        )

        return raw_points


class OrderTrackView(views.APIView):
    """GET /api/orders/{id}/track/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        from django.utils import timezone
        status_display = dict(Order.STATUS_CHOICES).get(order.status, order.status.title())
        timeline = [{"status": order.status, "timestamp": order.created_at.isoformat(), "description": f"Order {status_display.lower()}"}]
        if order.status in ('shipped', 'delivered') and order.updated_at:
            timeline.append({"status": order.status, "timestamp": order.updated_at.isoformat(), "description": f"Order {status_display.lower()}"})
        return Response({
            "order_id": str(order.id),
            "status": order.status,
            "status_display": status_display,
            "tracking_number": order.tracking_number or "",
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "timeline": timeline
        })


class OrderReorderView(views.APIView):
    """POST /api/orders/{id}/reorder/ — create new order from same items"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={201: OrderSerializer})
    @transaction.atomic
    def post(self, request, id):
        src_order = get_object_or_404(Order, id=id, user=request.user)
        address = ShippingAddress.objects.filter(user=request.user, is_default=True).first() or ShippingAddress.objects.filter(user=request.user).first()
        if not address:
            return Response({"error": "No shipping address. Add one first."}, status=status.HTTP_400_BAD_REQUEST)
        items = list(src_order.items.select_related('product').all())
        if not items:
            return Response({"error": "Original order has no items"}, status=status.HTTP_400_BAD_REQUEST)
        subtotal = sum(i.quantity * i.price for i in items)
        order = Order.objects.create(
            user=request.user, address_id=address.id,
            subtotal=subtotal, shipping_fee=0, discount_amount=0, total=subtotal,
            order_number=Order().generate_order_number(), shipping_method=src_order.shipping_method or 'cash_on_delivery'
        )
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.price, selected_size=item.selected_size, selected_color=item.selected_color)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderInvoiceView(views.APIView):
    """GET /api/orders/{id}/invoice/ — JSON invoice data"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: {'type': 'object'}})
    def get(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        address = ShippingAddress.objects.filter(id=order.address_id).first()
        items = [{"product_name": i.product.name, "quantity": i.quantity, "price": float(i.price), "total": float(i.quantity * i.price)} for i in order.items.select_related('product').all()]
        return Response({
            "order_id": str(order.id),
            "order_number": order.order_number,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "address": ShippingAddressSerializer(address).data if address else None,
            "items": items,
            "subtotal": float(order.subtotal),
            "shipping_fee": float(order.shipping_fee),
            "discount_amount": float(order.discount_amount),
            "total": float(order.total)
        })
