"""
Ships application logs over OTLP/HTTP (Grafana Cloud's OTLP gateway, or any
OpenTelemetry collector), batched in a background thread.

Configured with the standard OpenTelemetry env vars, which the exporter reads
itself; settings.py only adds the handler when an endpoint is set:
    OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-<region>.grafana.net/otlp
    OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20<base64 of instanceId:token>
"""
import logging
import os

_logger_provider = None


def otlp_logs_configured():
    return bool(os.getenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT') or os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'))


def build_otlp_handler(service_name, environment):
    """logging.config factory: one LoggerProvider per process, shared by every logger using the handler."""
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    global _logger_provider
    if _logger_provider is None:
        _logger_provider = LoggerProvider(resource=Resource.create({
            "service.name": service_name,
            "deployment.environment": environment,
        }))
        _logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    return LoggingHandler(level=logging.NOTSET, logger_provider=_logger_provider)
