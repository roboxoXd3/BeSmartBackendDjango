# Grafana Observability Stack Setup for BeSmart

This document outlines the observability stack implementation for the BeSmart backend, including Prometheus for metrics and Loki for structured logging. The implementation uses a push-based architecture for logs (Python pushing to Loki) and a pull-based architecture for metrics (Prometheus scraping Django).

## 1. Architecture Overview

- **Application (Django)**: 
  - Exposes `/prometheus/metrics` via `django-prometheus`
  - Formats logs as JSON using `structlog`
  - Injects `trace_id` and `user_id` into all logs via custom `TracingMiddleware`
  - Pushes logs directly to Grafana Loki via `python-logging-loki` handler
- **Prometheus**: Scrapes `/prometheus/metrics` on the backend periodically.
- **Grafana Loki**: Receives pushed JSON logs from the backend.
- **Grafana**: Visualizes metrics and logs.

## 2. Configuration Parameters

### Environment Variables

The backend accepts the following environment variables to configure observability:

```bash
# Enable pushing logs to Loki (Empty in local to disable)
LOKI_URL=http://loki.staging.internal:3100/loki/api/v1/push
LOKI_USERNAME=your_loki_user
LOKI_PASSWORD=your_loki_password

# Identify the environment in logs (e.g., local, staging, production)
ENVIRONMENT=production
```

If `LOKI_URL` is omitted, the application falls back to standard console logging (development friendly).

## 3. Loki Log Retention Policy (60 Days)

The user has requested a 60-day retention period for logs to support long-term auditing and user story tracking.

You must configure this in your Loki configuration file (`loki-config.yaml` or via your helm values if using Kubernetes):

```yaml
compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: s3
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

limits_config:
  # Set retention period to 60 days (1440 hours)
  retention_period: 1440h
```

*Note: Retention requires the compactor to be enabled. Ensure your underlying storage (e.g., S3 or filesystem) has sufficient capacity for 60 days of detailed logs.*

## 4. Prometheus Scrape Configuration

To ingest metrics, Prometheus must be configured to scrape the BeSmart backend. Add the following job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'besmart_backend'
    scrape_interval: 15s
    metrics_path: '/prometheus/metrics'
    static_configs:
      - targets: ['besmart-backend:8000'] # Replace with your internal routing/IP
```

## 5. Trace and Span IDs

All logs are automatically enriched with a `trace_id` for tracking an entire request lifecycle. If you need to trace cross-service communication in the future, the application is compatible with standard `X-B3-TraceId` and `traceparent` HTTP headers, meaning trace IDs will propagate correctly when used with API gateways or microservices.
