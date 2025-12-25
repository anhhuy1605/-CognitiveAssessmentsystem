# ==================================
# backend/middleware/security.py
# ==================================
"""
Production-grade security middleware for Flask
- CORS with whitelist
- Rate limiting
- Input validation & sanitization
- Security headers
- Request logging
"""

from flask import Flask, request, abort, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_talisman import Talisman
from functools import wraps
import re
import os
import logging
import time

logger = logging.getLogger(__name__)

# ==================================
# 1. CORS CONFIGURATION
# ==================================

def setup_cors(app: Flask):
    """
    Configure CORS with strict whitelist
    ⚠️  NEVER use origins=['*'] in production!
    """
    cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    
    if not cors_origins or cors_origins == ['']:
        raise ValueError(
            "❌ CORS_ORIGINS environment variable must be set\n"
            "Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
        )
    
    # Remove any whitespace
    cors_origins = [origin.strip() for origin in cors_origins]
    
    CORS(
        app,
        origins=cors_origins,
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
        expose_headers=['Content-Type', 'Authorization'],
        supports_credentials=True,
        max_age=3600,  # Cache preflight for 1 hour
    )
    
    logger.info(f"✅ CORS configured with origins: {cors_origins}")
    return app


# ==================================
# 2. RATE LIMITING
# ==================================

def setup_rate_limiting(app: Flask):
    """
    Rate limiting to prevent abuse
    Uses Redis if available, otherwise in-memory (resets on restart)
    """
    
    storage_uri = os.environ.get('RATE_LIMIT_STORAGE', 'memory://')
    default_limit = os.environ.get('RATE_LIMIT_DEFAULT', '60 per minute')
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[default_limit],
        storage_uri=storage_uri,
        strategy='fixed-window',
        headers_enabled=True,
        swallow_errors=True,  # Don't crash if Redis down
    )
    
    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"⚠️  Rate limit exceeded: {get_remote_address()}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    logger.info(f"✅ Rate limiting configured: {default_limit}")
    logger.info(f"   Storage: {storage_uri}")
    
    return limiter


# ==================================
# 3. SECURITY HEADERS (Flask-Talisman)
# ==================================

def setup_security_headers(app: Flask):
    """
    Add security headers using Flask-Talisman
    - HTTPS enforcement
    - HSTS
    - Content Security Policy
    - X-Frame-Options
    """
    
    # Only enforce HTTPS in production
    force_https = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'
    
    # Content Security Policy
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Needed for some ML libs
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': ["'self'", 'data:'],
        'connect-src': ["'self'", 'https://api.openai.com', 'https://generativelanguage.googleapis.com'],
        'media-src': ["'self'", 'blob:'],
        'object-src': "'none'",
        'frame-ancestors': "'none'",
    }
    
    Talisman(
        app,
        force_https=force_https,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        x_content_type_options=True,
        x_frame_options='DENY',
        x_xss_protection=True,
        referrer_policy='strict-origin-when-cross-origin',
        force_file_save=False,
    )
    
    logger.info("✅ Security headers configured (Talisman)")
    return app


# ==================================
# 4. INPUT SANITIZATION
# ==================================

# Dangerous patterns (XSS, SQL injection, etc.)
DANGEROUS_PATTERNS = [
    # XSS
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'onerror\s*=',
    r'onload\s*=',
    r'onclick\s*=',
    r'<iframe',
    r'<object',
    r'<embed',
    
    # SQL Injection
    r'(\bUNION\b.*\bSELECT\b)',
    r'(\bDROP\b.*\bTABLE\b)',
    r'(\bDELETE\b.*\bFROM\b)',
    r'(\bUPDATE\b.*\bSET\b)',
    r'(\bINSERT\b.*\bINTO\b)',
    r'--\s*$',
    r'/\*.*\*/',
    r';\s*DROP\s+',
    
    # Path traversal
    r'\.\./\.\.',
    r'\.\.\\\.\\',
    
    # Command injection
    r';\s*\w+\s*;',
    r'\|\s*\w+',
    r'`.*`',
    r'\$\(.*\)',
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


def detect_attack(data_str: str) -> tuple:
    """
    Check if input contains attack patterns
    Returns: (is_attack, pattern_matched)
    """
    for i, pattern in enumerate(COMPILED_PATTERNS):
        if pattern.search(data_str):
            return True, DANGEROUS_PATTERNS[i]
    return False, ""


def setup_input_sanitization(app: Flask):
    """
    Validate all incoming requests for malicious patterns
    """
    
    @app.before_request
    def sanitize_request():
        # Skip for health check and static files
        if request.path in ['/api/health', '/favicon.ico', '/robots.txt']:
            return
        
        # Skip for OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return
        
        # Get request data
        data = {}
        
        try:
            if request.is_json:
                data = request.get_json(silent=True) or {}
            elif request.form:
                data = request.form.to_dict()
        except:
            pass
        
        # Also check query params
        query_data = request.args.to_dict()
        data.update(query_data)
        
        # Convert to string for pattern matching
        data_str = str(data).lower()
        
        # Check for attacks
        is_attack, pattern = detect_attack(data_str)
        
        if is_attack:
            logger.warning(
                f"🚨 ATTACK DETECTED: "
                f"IP={get_remote_address()} "
                f"PATH={request.path} "
                f"METHOD={request.method} "
                f"PATTERN={pattern}"
            )
            abort(400, description="Invalid input detected")
        
        # Check request size (prevent large payload attacks)
        if request.content_length:
            max_size = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 16)) * 1024 * 1024
            if request.content_length > max_size:
                logger.warning(
                    f"⚠️  LARGE REQUEST: {request.content_length} bytes "
                    f"from {get_remote_address()}"
                )
                abort(413, description="Request too large")
    
    logger.info("✅ Input sanitization configured")
    return app


# ==================================
# 5. REQUEST LOGGING
# ==================================

def setup_request_logging(app: Flask):
    """
    Log all requests for monitoring and debugging
    """
    
    @app.before_request
    def log_request_start():
        g.start_time = time.time()
    
    @app.after_request
    def log_request_end(response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000  # ms
            
            # Log request details
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration, 2),
                'ip': get_remote_address(),
            }
            
            # Log as INFO for successful requests, WARNING for errors
            if response.status_code < 400:
                logger.info(f"REQUEST: {log_data}")
            else:
                logger.warning(f"REQUEST: {log_data}")
        
        return response
    
    logger.info("✅ Request logging configured")
    return app


# ==================================
# 6. AUTHENTICATION DECORATORS
# ==================================

def require_api_key(f):
    """
    Decorator to require API key in request
    Usage: @require_api_key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning(f"⚠️  Missing API key from {get_remote_address()}")
            return jsonify({"error": "API key required"}), 401
        
        # Validate API key (implement your logic)
        expected_key = os.environ.get('API_KEY')
        if api_key != expected_key:
            logger.warning(f"⚠️  Invalid API key from {get_remote_address()}")
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ==================================
# 7. VALIDATION HELPERS
# ==================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    
    return True, ""


def validate_phone(phone: str) -> bool:
    """Validate phone number (basic)"""
    pattern = r'^\+?1?\d{9,15}$'
    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return bool(re.match(pattern, clean_phone))


# ==================================
# 8. MAIN SETUP FUNCTION
# ==================================

def setup_security(app: Flask):
    """
    Setup all security features
    Call this in your app factory/initialization
    """
    try:
        logger.info("🔒 Initializing security middleware...")
        
        # 1. CORS
        setup_cors(app)
        
        # 2. Rate Limiting
        limiter = setup_rate_limiting(app)
        
        # 3. Security Headers
        setup_security_headers(app)
        
        # 4. Input Sanitization
        setup_input_sanitization(app)
        
        # 5. Request Logging
        setup_request_logging(app)
        
        logger.info("✅ All security features initialized successfully")
        
        return app, limiter
        
    except Exception as e:
        logger.error(f"❌ Security setup failed: {str(e)}")
        raise


# ==================================
# USAGE EXAMPLE
# ==================================
"""
# In your app.py or __init__.py:

from flask import Flask
from middleware.security import setup_security, require_api_key
from flask_limiter import Limiter

app = Flask(__name__)

# Setup security
app, limiter = setup_security(app)

# Protected route with API key
@app.route('/api/protected')
@require_api_key
def protected_route():
    return {"message": "Access granted"}

# Custom rate limit
@app.route('/api/heavy')
@limiter.limit("10 per hour")
def heavy_endpoint():
    return {"message": "Heavy operation"}

# Custom rate limit for specific routes
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    return {"message": "Login"}

if __name__ == '__main__':
    app.run()
"""

