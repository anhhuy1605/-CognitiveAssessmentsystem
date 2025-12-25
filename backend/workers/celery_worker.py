import os
import time
from celery import Celery
from celery.utils.log import get_task_logger
from backend.services.whisper_service import transcribe_audio_whisper, enqueue_transcription
from backend.services.cognitive_service import extract_acoustic_features, svm_predict
from backend.services.storage import write_result_json

logger = get_task_logger(__name__)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://redis:6379/0"))

celery_app = Celery("goldenfish", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_default_retry_delay = 5
celery_app.conf.task_annotations = {"*": {"max_retries": 3}}

@celery_app.task(bind=True, name="task_transcribe", autoretry_for=(Exception,), retry_backoff=True)
def task_transcribe(self, audio_path: str, session_id: str, question_index: int):
    logger.info(f"Transcribe job started: {audio_path}")
    transcript = transcribe_audio_whisper(audio_path, language="vi")
    path = enqueue_transcription(session_id, question_index, transcript)
    logger.info(f"Transcript stored: {path}")
    return {"path": path}

@celery_app.task(bind=True, name="task_analyze", autoretry_for=(Exception,), retry_backoff=True)
def task_analyze(self, audio_path: str, session_id: str, question_index: int):
    logger.info(f"Cognitive analysis started: {audio_path}")
    feats = extract_acoustic_features(audio_path)
    mmse = svm_predict(feats, os.getenv("SVM_MODEL_PATH", "/models/svm_model.pkl"))
    payload = {
        "session_id": session_id,
        "question_index": question_index,
        "acoustic_features": feats,
        "mmse_component_score": float(mmse),
        "timestamp_iso8601": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    path = write_result_json(session_id, question_index, payload)
    logger.info(f"Cognitive result stored: {path}")
    return {"path": path}


