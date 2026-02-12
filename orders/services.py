from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from orders.models import Order, OrderItem
from payments.models import Payment
from payments.services.squad_service import SquadPaymentService


class OrderService:
    """Business logic for order management"""
    
    @staticmethod
    def create_order_from_cart(user, cart_items, shipping_address):
        """
        Create order from cart items
        
        Args:
            user: User object
            cart_items: List of cart items
            shipping_address: Dict with shipping details
        
        Returns:
            Order object
        """
        with transaction.atomic():
            # Calculate total
            total_amount = Decimal('0.00')
            
            # Generate unique order number
            order = Order(user=user)
            order.order_number = order.generate_order_number()
            order.shipping_address = shipping_address
            order.status = 'pending_payment'
            order.payment_status = 'unpaid'
            
            # Validate stock and calculate total
            order_items_data = []
            for cart_item in cart_items:
                product = cart_item.product
                quantity = cart_item.quantity
                
                # Check stock availability
                if product.stock < quantity:
                    raise ValueError(f"Insufficient stock for {product.name}")
                
                # Calculate subtotal
                subtotal = product.price * quantity
                total_amount += subtotal
                
                order_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.price,
                    'subtotal': subtotal
                })
            
            # Save order
            order.total_amount = total_amount
            order.save()
            
            # Create order items
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    **item_data
                )
            
            return order
    
    @staticmethod
    def initiate_payment_for_order(order):
        """
        Initiate payment for an order
        
        Args:
            order: Order object
        
        Returns:
            Payment object with checkout_url
        """
        # Generate unique transaction reference
        transaction_ref = f"PAY_{order.order_number}_{timezone.now().timestamp()}"
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=order.user,
            transaction_ref=transaction_ref,
            amount=order.total_amount,
            currency=order.currency or 'NGN', # Ensure currency fallback
            status='pending',
            metadata={
                'order_number': order.order_number,
                'order_id': str(order.id),
            }
        )
        
        # Call Squad API
        squad_service = SquadPaymentService()
        
        try:
            response = squad_service.initiate_payment(
                amount=order.total_amount,
                email=order.user.email,
                transaction_ref=transaction_ref,
                currency=order.currency or 'NGN',
                metadata={
                    'order_id': str(order.id),
                    'user_id': str(order.user.id),
                }
            )
            
            if response.get('status') == 200:
                data = response.get('data', {})
                payment.checkout_url = data.get('checkout_url')
                payment.status = 'processing'
                payment.save()
                
                return payment
            else:
                payment.mark_as_failed()
                raise Exception(response.get('message', 'Payment initiation failed'))
                
        except Exception as e:
            payment.mark_as_failed()
            raise e
    
    @staticmethod
    def handle_successful_payment(payment):
        """
        Handle successful payment processing
        
        Args:
            payment: Payment object
        """
        with transaction.atomic():
            # Update payment
            payment.mark_as_success()
            
            # Update order
            order = payment.order
            order.status = 'confirmed'
            order.payment_status = 'paid'
            order.save()
            
            # Deduct inventory
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                product.save()
            
            # Create escrow transaction (if vendor system)
            from vendors.models import EscrowTransaction, Vendor
            from django.db.models import Sum

            # Group items by vendor
            vendor_items = {}
            for item in order.items.all():
                # Product has vendor_id UUID field
                if hasattr(item.product, 'vendor_id') and item.product.vendor_id:
                    vendor_id = item.product.vendor_id
                    if vendor_id not in vendor_items:
                        vendor_items[vendor_id] = []
                    vendor_items[vendor_id].append(item)
            
            # Create escrow transaction for each vendor
            for vendor_id, items in vendor_items.items():
                try:
                    vendor = Vendor.objects.get(id=vendor_id)
                except Vendor.DoesNotExist:
                    continue
                    
                vendor_total = sum(item.subtotal for item in items)
                
                # Calculate platform fee (e.g., 10% commission)
                commission_amount = vendor_total * (vendor.commission_rate / Decimal('100.00'))
                payout_amount = vendor_total - commission_amount
                
                EscrowTransaction.objects.create(
                    order=order,
                    vendor=vendor,
                    amount=payout_amount,
                    status='held',
                    # Release date could be set here based on settings, e.g., 7 days
                    release_date=timezone.now() + timezone.timedelta(days=7) 
                )

            # Send confirmation email
            # EmailService.send_order_confirmation(order)
