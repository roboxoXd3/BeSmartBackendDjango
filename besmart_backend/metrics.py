"""
Custom business metrics for Grafana/Prometheus alerting.

All definitions live here so every counter used across the codebase is declared exactly
once (prometheus_client raises if the same metric name is registered twice) and so the
full list of what's instrumented is visible in one place.

LABEL CARDINALITY -- read before adding a new metric or label:
Never use an unbounded value as a label -- no user_id, order_id, vendor_id,
transaction_ref, email, or similar. Each distinct label combination becomes its own
time series stored forever (until process restart); an ID-shaped label grows that set
without limit and can take down Prometheus. Every label below is a small, fixed set of
known strings. Anything you actually need to search by ID belongs in the structlog log
line (already the case throughout this codebase), not in a metric label.

These are plain Counters (not Gauges), which is what survives Prometheus multiprocess
mode cleanly without extra config -- see gunicorn.conf.py.
"""
from prometheus_client import Counter

payment_attempts_total = Counter(
    "besmart_payment_attempts_total",
    "Payment gateway attempts by operation and outcome",
    ["operation", "status"],
    # operation: initiate | verify | webhook_charge
    # status: success | failed | error
)

payout_transfers_total = Counter(
    "besmart_payout_transfers_total",
    "Vendor payout transfer attempts by outcome",
    ["status"],
    # status: initiated | completed | failed | error
)

escrow_operations_total = Counter(
    "besmart_escrow_operations_total",
    "Escrow release/hold operations by outcome",
    ["operation", "status"],
    # operation: release | hold
    # status: success | error
)

auth_attempts_total = Counter(
    "besmart_auth_attempts_total",
    "Supabase-authenticated request outcomes",
    ["result"],
    # result: success | invalid_token | misconfigured | error
)

orders_total = Counter(
    "besmart_orders_total",
    "Orders by status transition",
    ["status"],
)
