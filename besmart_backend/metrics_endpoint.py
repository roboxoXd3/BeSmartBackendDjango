"""
Auth wrapper for the Prometheus scrape endpoint (/prometheus/metrics).

The endpoint lists every view with its traffic and error counts, so it isn't
public. Scrapers (Grafana Cloud's hosted "Metrics Endpoint" job) authenticate
with METRICS_TOKEN, either as `Authorization: Bearer <token>` or as the
password of HTTP Basic auth (any username).
"""
import base64
import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django_prometheus.exports import ExportToDjangoView


def _presented_token(request):
    header = request.headers.get('Authorization', '')
    scheme, _, credentials = header.partition(' ')
    scheme = scheme.lower()
    if scheme == 'bearer':
        return credentials.strip()
    if scheme == 'basic':
        try:
            decoded = base64.b64decode(credentials.strip()).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            return None
        return decoded.partition(':')[2]
    return None


def metrics_view(request):
    token = getattr(settings, 'METRICS_TOKEN', None)
    if not token:
        # Unconfigured: open for local development only, invisible elsewhere.
        if settings.DEBUG:
            return ExportToDjangoView(request)
        return HttpResponseNotFound()

    presented = _presented_token(request)
    if not presented or not hmac.compare_digest(presented.encode(), token.encode()):
        response = HttpResponse("Unauthorized", status=401, content_type="text/plain")
        response['WWW-Authenticate'] = 'Bearer realm="metrics"'
        return response
    return ExportToDjangoView(request)
