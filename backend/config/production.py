# ==================================
# backend/config/production.py
# ==================================
"""
Production configuration for Flask Cognitive Assessment Backend
⚠️  DO NOT COMMIT THIS FILE WITH REAL SECRETS
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration for Flask app"""
    
    # ==================================
    # CRITICAL SETTINGS
    # ==================================
    DEBUG = False
    TESTING = False
    
    # Flask secret key (MUST be set)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY environment variable must be set")
    
    # ==================================
    # DATABASE
    # ==================================
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL environment variable must be set")
    
    # Fix for Railway/Heroku Postgres URL format
    # They use postgres:// but psycopg2 needs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Database connection pooling (if using SQLAlchemy)
    # Uncomment if your app uses SQLAlchemy
    # SQLALCHEMY_DATABASE_URI = DATABASE_URL
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     'pool_size': 10,           # Max connections in pool
    #     'pool_recycle': 3600,      # Recycle connections after 1 hour
    #     'pool_pre_ping': True,     # Verify connections before using
    #     'max_overflow': 5,         # Max overflow connections
    #     'pool_timeout': 30,        # Connection timeout
    # }
    
    # ==================================
    # AI SERVICES
    # ==================================
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY environment variable must be set")
    
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY or GOOGLE_API_KEY must be set")
    
    # ==================================
    # CORS CONFIGURATION
    # ==================================
    # IMPORTANT: Set to your frontend domain(s)
    # NEVER use '*' in production!
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    if not CORS_ORIGINS or CORS_ORIGINS == ['']:
        raise ValueError(
            "❌ CORS_ORIGINS must be set\n"
            "Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
        )
    
    CORS_ALLOW_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']
    CORS_MAX_AGE = 3600  # 1 hour
    
    # ==================================
    # RATE LIMITING
    # ==================================
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '60 per minute')
    RATELIMIT_HEADERS_ENABLED = True
    
    # Specific limits for different endpoints
    RATELIMIT_AUTH = '5 per minute'      # Login/register
    RATELIMIT_UPLOAD = '10 per hour'     # Audio uploads
    RATELIMIT_AI = '30 per hour'         # AI processing
    
    # ==================================
    # FILE UPLOADS
    # ==================================
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 16)) * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_PATH', '/tmp/uploads')
    STORAGE_PATH = os.environ.get('STORAGE_PATH', '/tmp/storage')
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'm4a', 'ogg', 'flac'}
    
    # ==================================
    # LOGGING
    # ==================================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE')  # None = stdout only
    
    # ==================================
    # SECURITY
    # ==================================
    # Session cookies
    SESSION_COOKIE_SECURE = True         # HTTPS only
    SESSION_COOKIE_HTTPONLY = True       # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'      # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security headers (using flask-talisman)
    FORCE_HTTPS = True
    STRICT_TRANSPORT_SECURITY = True
    STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 year
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data: https:",
        'font-src': "'self' data:",
        'connect-src': "'self' https://api.openai.com https://generativelanguage.googleapis.com",
    }
    
    # ==================================
    # JWT (if using)
    # ==================================
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    # Don't raise error if not using JWT
    if JWT_SECRET_KEY:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
        JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # ==================================
    # SENTRY (ERROR TRACKING)
    # ==================================
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    if SENTRY_DSN:
        SENTRY_ENVIRONMENT = 'production'
        SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', 0.1))
    
    # ==================================
    # CACHE (if using Redis)
    # ==================================
    REDIS_URL = os.environ.get('REDIS_URL')
    if REDIS_URL:
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = REDIS_URL
        CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    else:
        CACHE_TYPE = 'simple'  # In-memory cache
    
    # ==================================
    # MODEL CONFIGURATION
    # ==================================
    MODEL_PATH = os.environ.get('MODEL_PATH', './models')
    LOAD_MODELS_ON_STARTUP = os.environ.get('LOAD_MODELS_ON_STARTUP', 'true').lower() == 'true'
    
    # Whisper model size (tiny, base, small, medium, large)
    WHISPER_MODEL_SIZE = os.environ.get('WHISPER_MODEL_SIZE', 'base')
    
    # ==================================
    # GUNICORN INTEGRATION
    # ==================================
    # These are for reference, Gunicorn reads from env vars
    PORT = int(os.environ.get('PORT', 8000))
    WEB_CONCURRENCY = int(os.environ.get('WEB_CONCURRENCY', 2))
    GUNICORN_TIMEOUT = int(os.environ.get('GUNICORN_TIMEOUT', 300))


def validate_config():
    """
    Validate all required environment variables are set
    Call this on app startup to fail fast if misconfigured
    """
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'CORS_ORIGINS',
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        raise EnvironmentError(
            f"❌ Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in Railway dashboard or .env file"
        )
    
    print("✅ All required environment variables are set")
    return True


def setup_logging(app):
    """Setup production logging"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Set log level
    log_level = getattr(logging, ProductionConfig.LOG_LEVEL)
    app.logger.setLevel(log_level)
    
    # Console handler (always enabled for Railway/Heroku)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(ProductionConfig.LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    app.logger.addHandler(console_handler)
    
    # File handler (optional)
    if ProductionConfig.LOG_FILE:
        file_handler = RotatingFileHandler(
            ProductionConfig.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        app.logger.addHandler(file_handler)
    
    app.logger.info("🚀 Logging configured for production")


# ==================================
# USAGE EXAMPLE
# ==================================
"""
# In your app.py or __init__.py:

from flask import Flask
from config.production import ProductionConfig, validate_config, setup_logging

app = Flask(__name__)

# Load production config
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
    validate_config()  # Fail fast if misconfigured
    setup_logging(app)

# ... rest of your app setup
"""

