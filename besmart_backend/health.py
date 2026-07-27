"""
Liveness/readiness endpoint for uptime monitoring (Grafana, Railway healthchecks).

Deliberately cheap: a trivial DB round-trip and, when REDIS_URL is configured, a Redis
PING. No ORM model queries, no external HTTP calls (Supabase, Squad, R2) -- those have
their own failure modes and shouldn't take the whole service "down" in monitoring just
because a third party is slow.
"""
import os

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, views
from rest_framework.response import Response

from besmart_backend.utils.logger import get_logger

logger = get_logger(__name__)


def _check_database():
    try:
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, None
    except OperationalError as exc:
        return False, str(exc)
    except Exception as exc:  # defensive: a health check must never itself 500
        return False, str(exc)


def _check_redis():
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        # Redis isn't configured for this environment (only backs the
        # channels/websocket layer here) -- nothing to check.
        return None, None
    try:
        import redis as redis_lib
        client = redis_lib.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return True, None
    except Exception as exc:
        return False, str(exc)


class HealthCheckView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Service health check",
        description=(
            "Liveness/readiness probe for uptime monitoring. Checks a trivial DB "
            "query, and Redis (via PING) when REDIS_URL is configured. Returns 200 "
            "when every configured dependency is reachable, 503 otherwise. Does not "
            "check third-party services (Supabase, Squad, Cloudflare R2) -- those "
            "failing shouldn't be reported as this service being down."
        ),
        responses={
            200: inline_serializer(
                name="HealthCheckOKResponse",
                fields={
                    "status": serializers.CharField(),
                    "checks": serializers.DictField(),
                },
            ),
            503: inline_serializer(
                name="HealthCheckFailResponse",
                fields={
                    "status": serializers.CharField(),
                    "checks": serializers.DictField(),
                },
            ),
        },
    )
    def get(self, request):
        db_ok, db_error = _check_database()
        redis_ok, redis_error = _check_redis()

        checks = {"database": "ok" if db_ok else "error"}
        if db_error:
            checks["database_error"] = db_error

        if redis_ok is not None:
            checks["redis"] = "ok" if redis_ok else "error"
            if redis_error:
                checks["redis_error"] = redis_error

        healthy = db_ok and (redis_ok is not False)

        if not healthy:
            logger.error("health_check_failed", checks=checks)

        return Response(
            {"status": "ok" if healthy else "error", "checks": checks},
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
