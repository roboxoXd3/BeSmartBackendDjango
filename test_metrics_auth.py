"""
Checks that /prometheus/metrics is protected by METRICS_TOKEN:
  - no credentials / wrong token -> 401 (or 404 when METRICS_TOKEN isn't configured
    and DEBUG is off: then the endpoint is hidden entirely)
  - correct token as `Authorization: Bearer` -> 200 with django_http_* series
  - correct token as the HTTP Basic auth password (how Grafana Cloud's hosted
    "Metrics Endpoint" scrape job can send it) -> 200

Read-only: nothing is created or changed.

Usage:
    python test_metrics_auth.py --base-url http://localhost:8000/api --metrics-token <METRICS_TOKEN>
"""
import argparse
import sys

import requests


def check(label, condition, passed_list, detail=""):
    print(f"[{'OK' if condition else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not condition else ""))
    passed_list.append(bool(condition))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--metrics-token", required=True)
    args = parser.parse_args()
    url = args.base_url.rstrip("/").rsplit("/api", 1)[0] + "/prometheus/metrics"
    passed = []

    res = requests.get(url, timeout=30)
    check("no credentials -> 401", res.status_code == 401, passed, f"{res.status_code}")
    check("401 carries no metrics", "django_http" not in res.text, passed)

    res = requests.get(url, headers={"Authorization": "Bearer wrong-token"}, timeout=30)
    check("wrong bearer token -> 401", res.status_code == 401, passed, f"{res.status_code}")

    res = requests.get(url, auth=("grafana", "wrong-token"), timeout=30)
    check("wrong basic auth password -> 401", res.status_code == 401, passed, f"{res.status_code}")

    res = requests.get(url, headers={"Authorization": f"Bearer {args.metrics_token}"}, timeout=30)
    check("correct bearer token -> 200", res.status_code == 200, passed, f"{res.status_code}")
    check("response has django_http_* series", "django_http_requests" in res.text, passed)

    res = requests.get(url, auth=("grafana", args.metrics_token), timeout=30)
    check("correct token as basic auth password -> 200", res.status_code == 200, passed, f"{res.status_code}")

    print(f"\n{sum(passed)}/{len(passed)} checks passed")
    sys.exit(0 if all(passed) else 1)


if __name__ == "__main__":
    main()
