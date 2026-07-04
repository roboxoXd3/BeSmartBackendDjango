import logging
import structlog
import uuid

from besmart_backend.settings import LOGGING
import logging.config

logging.config.dictConfig(LOGGING)

structlog.contextvars.bind_contextvars(
    request_id=str(uuid.uuid4()),
    trace_id="abc",
    span_id="def",
    path="/api/users/",
    method="GET",
)

logger = structlog.get_logger("besmart_backend.middleware.tracing_middleware")
logger.info("http_request", status_code=200, user_id="123")
