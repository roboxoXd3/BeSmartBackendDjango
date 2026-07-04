import logging
import logging.config
import queue

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'loki': {
            '()': 'logging_loki.LokiQueueHandler',
            'queue': queue.Queue(-1),
            'url': 'http://localhost:3100/loki/api/v1/push',
            'tags': {'app': 'test'},
            'version': '1',
        }
    },
    'loggers': {
        'test': {
            'handlers': ['loki'],
            'level': 'INFO',
        }
    }
}

try:
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger("test")
    logger.info("Test Queue Loki message")
    print("Log emitted successfully with QueueHandler!")
except Exception as e:
    import traceback
    traceback.print_exc()

