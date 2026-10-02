"""
Checks OTLP log export end to end, without sending anything to Grafana Cloud:
starts a fake OTLP/HTTP collector, runs the Django server with
OTEL_EXPORTER_OTLP_ENDPOINT pointed at it, makes a few HTTP requests and decodes
what the collector received:
  - requests arrive at /v1/logs with the configured Authorization header
  - resource has service.name=besmart_backend and deployment.environment
  - bodies are the same JSON lines the console/Loki get (parseable, have "event")
  - /prometheus/metrics and /health/ request logs are filtered out

Local only (it starts its own server). Nothing is created or changed.

Usage:
    python test_otlp_logging.py
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest

AUTH = "Basic dGVzdDp0b2tlbg=="  # base64("test:token")
received = []  # (path, headers, ExportLogsServiceRequest)


class Collector(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        message = ExportLogsServiceRequest()
        message.ParseFromString(body)
        received.append((self.path, dict(self.headers), message))
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()

    def log_message(self, *args):
        pass


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check(label, condition, passed_list, detail=""):
    print(f"[{'OK' if condition else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not condition else ""))
    passed_list.append(bool(condition))


def main():
    passed = []
    collector = ThreadingHTTPServer(("127.0.0.1", free_port()), Collector)
    threading.Thread(target=collector.serve_forever, daemon=True).start()
    app_port = free_port()

    env = {
        **os.environ,
        "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://127.0.0.1:{collector.server_port}",
        "OTEL_EXPORTER_OTLP_HEADERS": AUTH.replace(" ", "%20").join(["Authorization=", ""]),
        "OTEL_BLRP_SCHEDULE_DELAY": "300",
        "LOKI_URL": "",
        "ENVIRONMENT": "otlp-test",
        "METRICS_TOKEN": "otlp-test-metrics",
    }
    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{app_port}", "--noreload"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    base = f"http://127.0.0.1:{app_port}"
    try:
        for _ in range(60):
            try:
                requests.get(f"{base}/api/schema/", timeout=5)
                break
            except requests.ConnectionError:
                time.sleep(1)
        requests.get(f"{base}/api/products/", timeout=30)
        requests.get(f"{base}/api/products/does-not-exist-otlp-check/", timeout=30)
        requests.post(f"{base}/api/auth/login/", json={"email": "nobody-otlp@example.com"}, timeout=30)
        requests.get(f"{base}/prometheus/metrics", headers={"Authorization": "Bearer otlp-test-metrics"}, timeout=30)
        requests.get(f"{base}/health/", timeout=30)
        time.sleep(3)
    finally:
        server.terminate()
        server.wait(timeout=30)
        collector.shutdown()

    check("collector received OTLP log exports", received, passed)
    if not received:
        print(server.stderr.read().decode()[-2000:])
        sys.exit(1)
    check("exports go to /v1/logs", all(path == "/v1/logs" for path, _, _ in received), passed, str({p for p, _, _ in received}))
    auth_values = [{k.lower(): v for k, v in h.items()}.get("authorization") for _, h, _ in received]
    check("Authorization header sent", all(v == AUTH for v in auth_values), passed, str(auth_values[:1]))

    resources, bodies = [], []
    for _, _, message in received:
        for resource_logs in message.resource_logs:
            resources.append({a.key: a.value.string_value for a in resource_logs.resource.attributes})
            for scope_logs in resource_logs.scope_logs:
                bodies.extend(record.body.string_value for record in scope_logs.log_records)
    check("resource service.name=besmart_backend", all(r.get("service.name") == "besmart_backend" for r in resources), passed, str(resources[:1]))
    check("resource deployment.environment set", all(r.get("deployment.environment") == "otlp-test" for r in resources), passed)

    parsed = []
    for body in bodies:
        try:
            parsed.append(json.loads(body))
        except ValueError:
            pass
    check("every log body is a JSON line", bodies and len(parsed) == len(bodies), passed, f"{len(parsed)}/{len(bodies)}")
    check("JSON lines have an 'event'", parsed and all("event" in p for p in parsed), passed)
    check("request logs were exported", any("/api/products/" in json.dumps(p) for p in parsed), passed, str([p.get("event") for p in parsed][:10]))
    check("/prometheus/metrics and /health/ request logs filtered out",
          not any(path in json.dumps(p) for p in parsed for path in ("/prometheus/metrics", "/health/")), passed)

    print(f"\n{sum(passed)}/{len(passed)} checks passed ({len(bodies)} log records in {len(received)} exports)")
    sys.exit(0 if all(passed) else 1)


if __name__ == "__main__":
    main()
