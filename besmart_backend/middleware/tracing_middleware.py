import uuid
import structlog
from opentelemetry import trace
from django.utils.deprecation import MiddlewareMixin

logger = structlog.get_logger(__name__)

class TracingMiddleware(MiddlewareMixin):
    """
    Middleware to inject OpenTelemetry trace and span IDs, 
    as well as user_id and request_id into the structlog context.
    """
    def process_request(self, request):
        # Clear the structlog context for the new request to prevent cross-request contamination
        structlog.contextvars.clear_contextvars()
        
        request_id = str(uuid.uuid4())
        
        # Get OpenTelemetry trace/span IDs if available
        span = trace.get_current_span()
        trace_id = ""
        span_id = ""
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, "032x")
            span_id = format(ctx.span_id, "016x")
            
        # Bind core identifiers
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            path=request.path,
            method=request.method,
        )

    def process_response(self, request, response):
        # The user object is typically attached to the request by the authentication middleware or DRF
        user_id = "anonymous"
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)
            
        # Log the completed HTTP request with the context variables
        logger.info(
            "http_request",
            status_code=response.status_code,
            user_id=user_id,
        )
        return response
