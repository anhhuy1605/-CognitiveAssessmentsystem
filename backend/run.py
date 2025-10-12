#!/usr/bin/env python3
"""
Vietnamese Cognitive Assessment Backend Runner
Main script to start the backend server
"""

import os
import sys
import logging
from pathlib import Path

# Ensure UTF-8 output for Windows consoles and logs
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Initialize the Flask app for gunicorn
app = None

def create_app():
    """Create and configure the Flask application"""
    global app
    if app is not None:
        return app
        
    logger.info("🚀 Initializing Vietnamese Cognitive Assessment Backend...")
    
    try:
        from app import app as flask_app, initialize_model
        app = flask_app
        
        # Initialize model in background
        try:
            initialize_model()
            logger.info("✅ Model initialization completed")
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            logger.info("ℹ️ Server will start with limited functionality")
        
        return app
    except Exception as e:
        logger.error(f"❌ Failed to create Flask app: {e}")
        raise

def main():
    """Main entry point for the backend server"""
    try:
        # Create the Flask app
        app = create_app()
        
        # Get configuration from environment
        port = int(os.environ.get('PORT', 5001))
        host = os.environ.get('HOST', '0.0.0.0')
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        logger.info(f"🔧 Debug mode: {debug}")
        logger.info("📚 API Documentation:")
        logger.info(f"   Health check: http://{host}:{port}/api/health")
        logger.info(f"   Status: http://{host}:{port}/api/status")
        logger.info(f"   Config: http://{host}:{port}/api/config")
        logger.info(f"   Assessment: http://{host}:{port}/api/assess")
        logger.info(f"   Transcription: http://{host}:{port}/api/transcribe (Gemini-first)")
        
        # Check if running with gunicorn (Heroku will use gunicorn)
        if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            logger.info("🚀 Running with gunicorn (production mode)")
            # Don't call app.run() when using gunicorn
            return app
        else:
            # Development mode - start Flask development server
            logger.info("🔧 Running Flask development server")
            app.run(
                host=host,
                port=port,
                debug=debug,
                threaded=True
            )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

# Initialize app for gunicorn
app = create_app()

if __name__ == '__main__':
    main()
