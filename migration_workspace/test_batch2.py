import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "besmart_backend.settings")
django.setup()
from django.test import RequestFactory
from orders.views import OrderListCreateView
from orders.models import Order, OrderItem
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()
factory = RequestFactory()

user = User.objects.filter(is_active=True).first()
if not user:
    print("No active user found")
    exit()

product = Product.objects.first()
order = Order.objects.create(user=user, subtotal=10, shipping_fee=0, total=10)
OrderItem.objects.create(order=order, product=product, quantity=1, price=10)

print("Testing WEB-D-029: GET /api/orders/")
request = factory.get('/api/orders/')
request.user = user

response = OrderListCreateView.as_view()(request)
print("OrderListCreateView status:", response.status_code)
if response.status_code == 200 and len(response.data.get('results', [])) > 0:
    order_data = response.data['results'][0]
    keys = order_data.keys()
    print("Has order_items:", 'order_items' in keys)
    print("Has shipping_address:", 'shipping_address' in keys)
    print("Has payment_method:", 'payment_method' in keys)
    if order_data.get('order_items'):
        item_keys = order_data['order_items'][0].keys()
        print("Item has products:", 'products' in item_keys)
        print("Does not have product:", 'product' not in item_keys)

print("\nAll tests ran successfully!")
