"""
gunicorn.conf.py - Production Gunicorn configuration.
Start with: gunicorn -c gunicorn.conf.py app:app
"""

import multiprocessing
import os

# ── Binding ────────────────────────────────────────────────────────────────────
bind = f"{os.getenv('APP_HOST', '0.0.0.0')}:{os.getenv('APP_PORT', '8000')}"

# ── Workers ────────────────────────────────────────────────────────────────────
# Rule of thumb: (2 × CPU cores) + 1 for I/O-bound; 1 for CPU-heavy
workers = int(os.getenv("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count())))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# ── Logging ────────────────────────────────────────────────────────────────────
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"   # stdout
errorlog = "-"    # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ── Process ────────────────────────────────────────────────────────────────────
proc_name = "titanic_eda"
preload_app = True     # Load app code before forking workers (saves memory)
daemon = False         # Never daemonise inside Docker
