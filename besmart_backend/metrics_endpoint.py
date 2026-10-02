"""
Auth wrapper for the Prometheus scrape endpoint (/prometheus/metrics).

The endpoint lists every view with its traffic and error counts, so it isn't
public. Scrapers (Grafana Cloud's hosted "Metrics Endpoint" job) authenticate
with METRICS_TOKEN, either as `Authorization: Bearer <token>` or as the
password of HTTP Basic auth (any username). Without METRICS_TOKEN set the
endpoint returns 404; set any value locally to read it.
"""
import base64
import hmac
import os

import prometheus_client
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from prometheus_client import multiprocess
from prometheus_client.exposition import choose_encoder


def _export(request):
    """
    Same output as django_prometheus' ExportToDjangoView, but honouring the
    scraper's Accept header. ExportToDjangoView always labels the body
    `text/plain; version=1.0.0` (prometheus_client >= 0.22's default), which
    scrapers that only speak the classic 0.0.4 format, like Grafana Cloud's
    hosted Metrics Endpoint, reject.
    """
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ or "prometheus_multiproc_dir" in os.environ:
        registry = prometheus_client.CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = prometheus_client.REGISTRY
    encoder, content_type = choose_encoder(request.META.get('HTTP_ACCEPT', ''))
    return HttpResponse(encoder(registry), content_type=content_type)


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
        # Unconfigured: hidden. (Not "open when DEBUG": DEBUG defaults to on, so
        # an environment that forgets to set it would expose the metrics.)
        return HttpResponseNotFound()

    presented = _presented_token(request)
    if not presented or not hmac.compare_digest(presented.encode(), token.encode()):
        response = HttpResponse("Unauthorized", status=401, content_type="text/plain")
        response['WWW-Authenticate'] = 'Bearer realm="metrics"'
        return response
    return _export(request)
