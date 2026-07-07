import threading
import os

print(f"File evaluated in PID: {os.getpid()}, Active threads: {threading.active_count()}")

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Hello World"]

