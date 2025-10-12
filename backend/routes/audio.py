import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.utils import auth_required
from backend.services.storage import ensure_dirs, save_and_convert_audio
from backend.workers.celery_worker import task_transcribe, task_analyze

audio_bp = Blueprint("audio", __name__)

@audio_bp.post("/session/<session_id>/audio")
@auth_required
def upload_audio(session_id):
    ensure_dirs()
    file = request.files.get("audio")
    qidx = int(request.form.get("question_index", "1"))
    if not file:
        return jsonify({"success": False, "error": "no_file"}), 400
    path, ts = save_and_convert_audio(file, session_id, qidx)
    # Enqueue background jobs
    task_transcribe.apply_async(args=[path, session_id, qidx], countdown=0)
    task_analyze.apply_async(args=[path, session_id, qidx], countdown=0)
    return jsonify({"success": True, "path": path, "timestamp": ts})

@audio_bp.post("/session/<session_id>/end_answer")
@auth_required
def end_answer(session_id):
    # Frontend can force end-of-answer; nothing to persist beyond acknowledgement
    qidx = int((request.get_json(silent=True) or {}).get("question_index", 1))
    return jsonify({"success": True, "session_id": session_id, "question_index": qidx})


