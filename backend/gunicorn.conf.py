# ==================================
# backend/gunicorn.conf.py
# ==================================
"""
Gunicorn production configuration
Optimized for Railway deployment with ML workloads
"""

import multiprocessing
import os

# ==================================
# SERVER SOCKET
# ==================================
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# ==================================
# WORKER PROCESSES
# ==================================
# Railway free: 512MB RAM → 2 workers safe
# Railway Pro: 8GB RAM → 4-8 workers
# Formula: (2 x CPU cores) + 1, but limited by RAM for ML models
workers = int(os.environ.get('WEB_CONCURRENCY', 2))

# Worker class
# - sync: Default, simple, works for most cases
# - gevent: Async, good for I/O bound (needs: pip install gevent)
# - eventlet: Async alternative (needs: pip install eventlet)
worker_class = os.environ.get('WORKER_CLASS', 'sync')

# Connections per worker (only for async workers)
worker_connections = 1000

# Restart workers after N requests (prevent memory leaks)
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Worker timeout (seconds)
# IMPORTANT: Set high for ML processing (audio transcription, GPT calls)
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 300))  # 5 minutes default
graceful_timeout = 30  # Time to finish requests during shutdown
keepalive = 5  # Keep alive connections

# ==================================
# THREADING
# ==================================
# Threads per worker (only effective with sync worker class)
# total concurrent requests = workers * threads
threads = int(os.environ.get('THREADS_PER_WORKER', 4))

# ==================================
# LOGGING
# ==================================
# Log to stdout/stderr (Railway captures this)
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

# Access log format (includes response time)
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s µs'
)

# ==================================
# PROCESS NAMING
# ==================================
proc_name = os.environ.get('PROC_NAME', 'cognitive-backend')

# ==================================
# SERVER MECHANICS
# ==================================
daemon = False  # Don't daemonize (Railway needs foreground process)
pidfile = None  # No PID file needed
umask = 0
user = None  # Run as current user (Docker handles this)
group = None
tmp_upload_dir = '/tmp'  # Railway has writable /tmp

# ==================================
# SECURITY
# ==================================
# HTTP request limits (prevent attacks)
limit_request_line = 4096      # Max size of HTTP request line (4KB)
limit_request_fields = 100     # Max number of headers
limit_request_field_size = 8190  # Max size of header (8KB)

# ==================================
# SSL/TLS (usually handled by Railway)
# ==================================
# Uncomment if terminating SSL at app level
# keyfile = os.environ.get('SSL_KEYFILE')
# certfile = os.environ.get('SSL_CERTFILE')

# ==================================
# WORKER LIFECYCLE HOOKS
# ==================================

def on_starting(server):
    """Called just before the master process is initialized"""
    server.log.info("="*60)
    server.log.info("🚀 Gunicorn is starting...")
    server.log.info(f"   Workers: {workers}")
    server.log.info(f"   Threads per worker: {threads}")
    server.log.info(f"   Total concurrent requests: {workers * threads}")
    server.log.info(f"   Timeout: {timeout}s")
    server.log.info(f"   Port: {os.environ.get('PORT', '8000')}")
    server.log.info("="*60)

def when_ready(server):
    """Called just after the server is started"""
    server.log.info("✅ Gunicorn is ready. Serving application...")
    
    # Validate production config
    try:
        from config.production import validate_config
        validate_config()
    except ImportError:
        server.log.warning("⚠️  Could not import production config")
    except Exception as e:
        server.log.error(f"❌ Config validation failed: {e}")

def on_exit(server):
    """Called just before exiting Gunicorn"""
    server.log.info("👋 Gunicorn is shutting down...")

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT"""
    worker.log.warning(f"⚠️  Worker {worker.pid} received interrupt signal")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info(f"🔧 Worker {worker.pid} spawned")

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    pass

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("🔄 Gunicorn master process is being replaced")

def worker_exit(server, worker):
    """Called when a worker is exited"""
    server.log.info(f"💀 Worker {worker.pid} exited")

def worker_abort(worker):
    """Called when a worker times out"""
    worker.log.error(f"❌ Worker {worker.pid} TIMED OUT after {timeout}s")

# ==================================
# ENVIRONMENT VARIABLES REFERENCE
# ==================================
"""
Environment variables used:

REQUIRED:
- PORT: Port to bind to (Railway auto-injects, default: 8000)

OPTIONAL TUNING:
- WEB_CONCURRENCY: Number of workers (default: 2)
  - Railway free (512MB): 2
  - Railway Pro (8GB): 4-8
  
- THREADS_PER_WORKER: Threads per worker (default: 4)
  - Increase for I/O bound workloads
  - Total concurrent requests = WEB_CONCURRENCY × THREADS_PER_WORKER
  
- GUNICORN_TIMEOUT: Worker timeout in seconds (default: 300)
  - 60s: For fast API endpoints
  - 300s: For ML processing (recommended)
  - 600s: For very slow operations
  
- WORKER_CLASS: Worker type (default: sync)
  - sync: Simple, reliable
  - gevent: Async I/O (install gevent first)
  - eventlet: Async alternative (install eventlet first)
  
- MAX_REQUESTS: Restart worker after N requests (default: 1000)
  - Prevents memory leaks
  - Lower for memory-intensive apps (500)
  
- LOG_LEVEL: Logging verbosity (default: info)
  - debug: Very verbose
  - info: Standard
  - warning: Less verbose
  - error: Only errors

EXAMPLE CONFIGURATIONS:

Development/Testing (Railway free - 512MB):
export WEB_CONCURRENCY=2
export THREADS_PER_WORKER=2
export GUNICORN_TIMEOUT=180

Production (Railway Pro - 8GB):
export WEB_CONCURRENCY=4
export THREADS_PER_WORKER=4
export GUNICORN_TIMEOUT=300
export MAX_REQUESTS=500

High Traffic (Railway Pro - 8GB + async):
export WEB_CONCURRENCY=8
export WORKER_CLASS=gevent
export WORKER_CONNECTIONS=1000
export GUNICORN_TIMEOUT=300
"""

# ==================================
# TESTING CONFIGURATION
# ==================================
"""
Test locally:
  gunicorn -c gunicorn.conf.py app:app
  
Test with custom port:
  PORT=5000 gunicorn -c gunicorn.conf.py app:app
  
Test with more workers:
  WEB_CONCURRENCY=4 gunicorn -c gunicorn.conf.py app:app
  
Monitor workers:
  # In another terminal:
  watch -n 1 'ps aux | grep gunicorn'
"""

