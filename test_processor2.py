import logging
import structlog
from structlog.stdlib import ProcessorFormatter

formatter = ProcessorFormatter(processor=structlog.processors.JSONRenderer())

record = logging.LogRecord(
    name="django.server",
    level=logging.INFO,
    pathname="test.py",
    lineno=1,
    msg='"GET /prometheus/metrics HTTP/1.1" %s %s',
    args=(200, 14910),
    exc_info=None,
)

try:
    formatted = formatter.format(record)
    print(f"Result: {formatted}")
except Exception as e:
    import traceback
    traceback.print_exc()

