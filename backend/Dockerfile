# ==================================
# 🐍 PRODUCTION DOCKERFILE - COGNITIVE ASSESSMENT BACKEND
# ==================================
# Generated: 2025-10-08
# Framework: Flask + ML (PyTorch, Transformers, Whisper)
# Optimized for: Railway deployment

# ==================================
# STAGE 1: Builder - Install dependencies
# ==================================
FROM python:3.11.6-slim-bookworm AS builder

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Keep Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
# Disable pip version check
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for building Python packages
# - gcc, g++: For compiling numpy, scipy, etc.
# - libpq-dev: For psycopg2
# - libsndfile1: For audio processing (soundfile, librosa)
# - ffmpeg: For audio format conversion (pydub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to reduce image size
# Using pip==23.3.2 for stability
RUN pip install --no-cache-dir --upgrade pip==23.3.2 && \
    pip install --no-cache-dir -r requirements.txt

# ==================================
# STAGE 2: Runtime - Lean production image
# ==================================
FROM python:3.11.6-slim-bookworm

# Security: Run as non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /tmp/uploads /tmp/storage && \
    chown -R appuser:appuser /app /tmp/uploads /tmp/storage

WORKDIR /app

# Install ONLY runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port (Railway will inject PORT env var)
EXPOSE 8000

# Health check
# Railway will use this to verify app is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Production command with Gunicorn
# - bind to 0.0.0.0:$PORT (Railway injects PORT)
# - workers: 2 (safe for 512MB RAM, scale to 4 for 8GB)
# - threads: 4 per worker (total 8 concurrent requests)
# - timeout: 300s (5 min for ML processing)
# - worker-class: sync (can change to gevent for async)
# - access logs to stdout
# - error logs to stderr
CMD gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-2} \
    --threads 4 \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --capture-output \
    --enable-stdio-inheritance \
    app:app

# ==================================
# NOTES FOR DEPLOYMENT:
# ==================================
# 
# Railway Environment Variables needed:
# - PORT (auto-injected by Railway)
# - DATABASE_URL (from Neon)
# - OPENAI_API_KEY
# - GEMINI_API_KEY
# - SECRET_KEY
# - CORS_ORIGINS
# 
# Optional for scaling:
# - WEB_CONCURRENCY=4 (for 8GB RAM)
# - GUNICORN_TIMEOUT=300 (default 5 min)
# - LOG_LEVEL=info (debug|info|warning|error)
# 
# Build command:
#   docker build -t cognitive-backend .
# 
# Run locally:
#   docker run -p 8000:8000 --env-file .env cognitive-backend
# 
# Image size: ~2.5GB (PyTorch + Transformers are large)
# RAM usage: ~2.8GB minimum (ML models)
# Recommended Railway plan: Pro (8GB RAM, $20/month)
# ==================================
