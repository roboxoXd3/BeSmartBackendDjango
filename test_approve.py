import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
django.setup()

from products.models import Product
from admin_api.views import ProductAdminViewSet

p = Product.objects.create(name="Test Product", price=10.0, approval_status='pending')
print(f"Created product {p.id} with status {p.approval_status}")

# Fetch using the same queryset logic as the viewset
from products.views import get_optimized_product_queryset
qs = get_optimized_product_queryset(Product.objects.all())
p_fetched = qs.get(id=p.id)

print(f"Fetched product status before: {p_fetched.approval_status}")
p_fetched.approval_status = 'approved'
p_fetched.save(update_fields=['approval_status'])

# Re-fetch raw
p_refetched = Product.objects.get(id=p.id)
print(f"Re-fetched product status after: {p_refetched.approval_status}")

# Clean up
p.delete()
