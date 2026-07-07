from django.core.wsgi import get_wsgi_application
import os
import threading
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
print(f"Loading Django app in PID: {os.getpid()}, Threads: {threading.active_count()}")
application = get_wsgi_application()
