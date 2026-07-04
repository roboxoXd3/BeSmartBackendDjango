import logging
import logging.config
import structlog
from besmart_backend.settings import LOGGING

LOGGING['handlers']['loki'] = {
    'class': 'logging_loki.LokiHandler',
    'url': 'http://localhost:3100/loki/api/v1/push',
    'tags': {'app': 'besmart_backend'},
    'version': '1',
    'formatter': 'json'
}
LOGGING['loggers']['django']['handlers'] = ['loki']

try:
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger("django")
    logger.info("Test Loki message")
    print("Log emitted successfully!")
except Exception as e:
    print(f"Exception: {e}")

