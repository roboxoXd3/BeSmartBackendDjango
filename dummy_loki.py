from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
class DummyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"Received POST: {post_data}")
        self.send_response(204)
        self.end_headers()

server = HTTPServer(('localhost', 3101), DummyHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

import logging
import logging.config
import queue
import time

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'loki': {
            '()': 'logging_loki.LokiQueueHandler',
            'queue': queue.Queue(-1),
            'url': 'http://localhost:3101/loki/api/v1/push',
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
logger = logging.getLogger("test")
logger.info("Test Queue Loki message")
time.sleep(2)
