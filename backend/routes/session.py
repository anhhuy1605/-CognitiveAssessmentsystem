import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.utils import auth_required
from backend.services.storage import ensure_dirs, load_summary, write_json

session_bp = Blueprint("session", __name__)

# In-memory question bank (can be replaced by DB)
QUESTION_BANK = [
    {"id": 1, "text": "Hãy mô tả một ngày gần đây của bạn."},
    {"id": 2, "text": "Hãy kể lại kỷ niệm tuổi thơ đáng nhớ."},
    {"id": 3, "text": "Hôm nay bạn cảm thấy thế nào?"}
]

SESSIONS = {}

def next_question_state(state):
    idx = state.get("current_index", 0)
    if idx < len(QUESTION_BANK):
        q = QUESTION_BANK[idx]
        state["current_index"] = idx + 1
        return q
    return None

@session_bp.post("/session")
@auth_required
def create_session():
    ensure_dirs()
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "anonymous")
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "user_id": user_id,
        "current_index": 0,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    return jsonify({"success": True, "session_id": session_id})

@session_bp.get("/session/<session_id>/question")
@auth_required
def get_next_question(session_id):
    state = SESSIONS.get(session_id)
    if not state:
        return jsonify({"success": False, "error": "session_not_found"}), 404
    q = next_question_state(state)
    if not q:
        return jsonify({"success": False, "error": "no_more_questions"}), 404
    return jsonify({"success": True, "question": q, "index": state["current_index"]})

@session_bp.get("/session/<session_id>/results")
@auth_required
def get_session_results(session_id):
    summary = load_summary(session_id)
    if not summary:
        return jsonify({"success": False, "error": "no_results"}), 404
    return jsonify({"success": True, "summary": summary})

# WebSocket registration
def register_ws(sock):
    @sock.route("/ws/session/<session_id>")
    def ws(ws, session_id):
        # Minimal echo/control channel; the workers push via another mechanism in prod
        try:
            ws.send(json.dumps({"event":"question_asked","session_id":session_id}))
            while True:
                msg = ws.receive()
                if not msg:
                    break
                # Simply echo with a wrapper
                ws.send(json.dumps({"event":"ack","data":msg}))
        except Exception as e:
            try:
                ws.send(json.dumps({"event":"error","message":str(e)}))
            except Exception:
                pass


