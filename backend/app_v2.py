import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sock import Sock

# Load env
load_dotenv()

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Auth helper
from backend.utils import auth_required

# Blueprints
from backend.routes.session import session_bp
from backend.routes.audio import audio_bp

app.register_blueprint(session_bp, url_prefix="/api")
app.register_blueprint(audio_bp, url_prefix="/api")

# Metrics placeholder (Prometheus-ready hook)
@app.get("/metrics")
def metrics():
    # TODO: integrate prometheus_client metrics here
    return jsonify({
        "uptime": datetime.utcnow().isoformat() + "Z",
        "status":"ok"
    })

# WebSocket endpoint (handled in session blueprint via Sock)
# We mount Sock here for blueprint use
from backend.routes.session import register_ws
register_ws(sock)

@app.get("/")
def root():
    return jsonify({"service":"GoldenFish Backend","status":"ready"})

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    app.run(host=host, port=port)


