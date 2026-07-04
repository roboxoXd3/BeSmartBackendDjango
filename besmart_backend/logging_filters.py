import logging

class PrometheusEndpointFilter(logging.Filter):
    """
    Filter out logs for the Prometheus metrics endpoint to reduce noise,
    especially from the django.server logger.
    """
    def filter(self, record):
        try:
            # Check if the message contains the prometheus endpoint
            # This handles django.server which passes the request string in args
            msg = str(record.args[0]) if hasattr(record, 'args') and len(record.args) > 0 else record.getMessage()
            if '/prometheus/metrics' in msg:
                return False
        except Exception:
            pass
        return True
