import os
import time
from backend.services.storage import write_text_json

MODE = os.getenv("EXTERNAL_SERVICES_MODE", "mock").lower()

def transcribe_audio_whisper(audio_path: str, language: str = "vi") -> dict:
    if MODE == "mock":
        # Deterministic transcript for tests
        return {"text": "xin chao toi ten la goldfish", "confidence": 0.9, "lang": language}
    # TODO: Implement real Whisper/PhoWhisper call here
    # Return shape: { text, confidence, lang }
    raise NotImplementedError("Real Whisper integration not configured")

def enqueue_transcription(session_id: str, question_index: int, transcript: dict) -> str:
    payload = {
        "session_id": session_id,
        "question_index": question_index,
        "transcript": transcript,
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    return write_text_json(session_id, question_index, payload)


