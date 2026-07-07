from django.core.wsgi import get_wsgi_application
import os
import threading
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
application = get_wsgi_application()

import logging
logger = logging.getLogger('besmart_backend')
logger.info("Test thread")

print(f"Active threads in worker {os.getpid()}:")
for thread in threading.enumerate():
    print(f" - {thread.name} ({thread.__class__.__name__})")
time.sleep(1)
