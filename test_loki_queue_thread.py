import logging
import logging.config
import queue
import threading

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
logging.config.dictConfig(LOGGING)
print(f"Threads: {[t.name for t in threading.enumerate()]}")
