import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
django.setup()
from django.test import Client
c = Client()
response = c.get('/prometheus/metrics')
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.content)}")
print(response.content[:200].decode('utf-8'))
