import multiprocessing
import os

# --- Binding ---
# Listen on all interfaces on port 8000
port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"

# --- Worker Strategy (Tuning) ---
# For I/O bound async apps like FastAPI, we use Uvicorn workers managed by Gunicorn.
# The standard formula is (2 * cores) + 1, but we allow environment overrides.
cores = multiprocessing.cpu_count()
default_workers = min(2, (cores * 1) + 1)  
workers = int(os.getenv("WEB_CONCURRENCY", str(default_workers)))

# Crucial: Use the Uvicorn worker class for async compatibility
worker_class = "uvicorn.workers.UvicornWorker"

# --- Performance Tuning ---
# How long a worker can take to process a request before being killed
timeout = int(os.getenv("TIMEOUT", "120"))
# Keep-alive connections to reduce handshake overhead
keepalive = 5
# Time to wait for workers to finish current requests during a shutdown
graceful_timeout = 30

# --- Logging ---
# Log to stdout/stderr so Docker can capture the logs easily
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"

# --- Advanced ---
# Max requests a worker handles before restarting (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50
