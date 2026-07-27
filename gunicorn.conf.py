"""
Gunicorn config for Prometheus multiprocess mode.

With multiple workers (see Procfile), django-prometheus / prometheus_client keep a
separate in-memory registry per worker by default. Without this file, Prometheus scrapes
whichever worker answers the request and every counter reads low and jitters between
scrapes, making any threshold alert on those numbers unreliable.

Setting PROMETHEUS_MULTIPROC_DIR makes every worker write its metrics to files in that
directory instead; django_prometheus.exports.ExportToDjangoView already detects the env
var and merges all workers' data via prometheus_client.multiprocess.MultiProcessCollector
on every scrape -- no view code changes needed.

IMPORTANT: do not add --preload to the Procfile. Preloading imports the app (and defines
all metrics) in the master process before workers fork, which breaks multiprocess mode.
"""
import os
import shutil

PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", PROMETHEUS_MULTIPROC_DIR)


def on_starting(server):
    """
    Runs once, before any worker forks. Wipe any .db files left over from a previous
    boot -- if stale files from dead workers stick around, their last-known counter
    values get merged into the current scrape forever.
    """
    if os.path.isdir(PROMETHEUS_MULTIPROC_DIR):
        shutil.rmtree(PROMETHEUS_MULTIPROC_DIR)
    os.makedirs(PROMETHEUS_MULTIPROC_DIR, exist_ok=True)


def child_exit(server, worker):
    """
    Runs in the master process whenever a worker exits (recycled, killed, crashed).
    Marks that worker's metric files dead so its counters are dropped from future
    scrapes instead of being merged in forever as a phantom worker.
    """
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid, PROMETHEUS_MULTIPROC_DIR)
