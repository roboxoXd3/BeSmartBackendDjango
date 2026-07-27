import logging

# Endpoints hit repeatedly by monitoring probes (scrapers, healthchecks) that would
# otherwise flood Loki and distort log-rate panels/alerts with noise unrelated to
# real traffic.
NOISY_MONITORING_PATHS = ('/prometheus/metrics', '/health/')


class NoisyEndpointFilter(logging.Filter):
    """
    Filter out access logs for noisy monitoring endpoints (Prometheus scrapes,
    healthchecks) to reduce log noise -- especially from the django.server logger.

    Uses record.getMessage() (formats record.msg % record.args) rather than
    inspecting record.args directly -- different loggers put the path in
    different argument positions (django.server's access log embeds it in a
    full request-line string at args[0]; django.request's warning/error log
    for non-2xx responses -- e.g. this filter's own motivating case, a 503
    from a failing /health/ check -- passes it as args[1], '%s: %s' %
    (reason_phrase, path)). getMessage() renders either shape into one string
    that always contains the path if the logger put it there at all.
    """
    def filter(self, record):
        try:
            msg = record.getMessage()
            if any(path in msg for path in NOISY_MONITORING_PATHS):
                return False
        except Exception:
            pass
        return True


# Kept for backwards compatibility with any external references to the old name.
PrometheusEndpointFilter = NoisyEndpointFilter
