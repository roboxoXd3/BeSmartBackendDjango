import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "besmart_backend.settings")
django.setup()
from django.test import RequestFactory
from products.views import ProductListView, ProductDetailView, ProductReviewsListCreateView, ProductQAListCreateView
from categories.views import CategoryListView
from products.models import Product

factory = RequestFactory()

print("Testing WEB-D-001: ProductListView")
request = factory.get('/api/products/?ordering=-reviews')
response = ProductListView.as_view()(request)
print("ProductListView Status:", response.status_code)
data = response.data
if isinstance(data, dict):
    data = data.get('results', [])
if len(data) > 0:
    keys = data[0].keys()
    print("Has sizes:", 'sizes' in keys)
    print("Has base_currency:", 'base_currency' in keys)
    print("Has cod_allowed:", 'cod_allowed' in keys)
    print("Has ratings:", 'ratings' in keys)
    print("Has category:", 'category' in keys)

print("\nTesting WEB-D-002: ProductDetailView")
product = Product.objects.filter(status='active', approval_status='approved').first()
if product:
    request = factory.get(f'/api/products/{product.id}/')
    response = ProductDetailView.as_view()(request, id=product.id)
    print("ProductDetailView Status:", response.status_code)
else:
    print("No active product found")

print("\nTesting WEB-D-050: CategoryListView")
request = factory.get('/api/categories/')
response = CategoryListView.as_view()(request)
print("CategoryListView Status:", response.status_code)

print("\nTesting WEB-D-007: ProductReviewsListCreateView (GET)")
if product:
    request = factory.get(f'/api/products/{product.id}/reviews/')
    response = ProductReviewsListCreateView.as_view()(request, id=product.id)
    print("ProductReviewsListCreateView Status:", response.status_code)

print("\nTesting WEB-D-009: ProductQAListCreateView (GET)")
if product:
    request = factory.get(f'/api/products/{product.id}/qa/')
    response = ProductQAListCreateView.as_view()(request, id=product.id)
    print("ProductQAListCreateView Status:", response.status_code)

print("\nAll tests ran successfully!")
