import os
import json
import tempfile
import subprocess
from datetime import datetime
from typing import Tuple, Optional

# Use environment variable for storage path, fallback to local recordings directory
STORAGE_PATH = os.getenv('STORAGE_PATH', os.path.join(os.path.dirname(__file__), "..", "recordings"))
RECORDINGS_DIR = os.path.abspath(STORAGE_PATH)

# Use same base directory for text and results
BASE_DIR = os.path.dirname(STORAGE_PATH)
TEXT_DIR = os.path.join(BASE_DIR, "text-records")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

def ensure_dirs():
    for p in [RECORDINGS_DIR, TEXT_DIR, RESULTS_DIR]:
        os.makedirs(p, exist_ok=True)

def _out_path(session_id: str, question_index: int, ext: str = ".wav"):
    iso = datetime.utcnow().isoformat().replace(":", "-")
    sdir = os.path.join(RECORDINGS_DIR, session_id)
    os.makedirs(sdir, exist_ok=True)
    return os.path.join(sdir, f"{question_index}_{iso}{ext}"), iso

def save_and_convert_audio(file, session_id: str, question_index: int) -> Tuple[str, str]:
    """Save upload then convert to WAV mono 16k 16-bit PCM via ffmpeg."""
    tmp = tempfile.NamedTemporaryFile(delete=False)
    file.save(tmp.name)
    out_path, iso = _out_path(session_id, question_index, ".wav")
    cmd = [
        "ffmpeg", "-y", "-i", tmp.name,
        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
        out_path
    ]
    subprocess.run(cmd, check=True)
    try:
        os.unlink(tmp.name)
    except Exception:
        pass
    return out_path, iso

def write_text_json(session_id: str, question_index: int, payload: dict) -> str:
    sdir = os.path.join(TEXT_DIR, session_id)
    os.makedirs(sdir, exist_ok=True)
    path = os.path.join(sdir, f"{question_index}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def write_result_json(session_id: str, question_index: int, payload: dict) -> str:
    sdir = os.path.join(RESULTS_DIR, session_id)
    os.makedirs(sdir, exist_ok=True)
    path = os.path.join(sdir, f"{question_index}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def write_summary(session_id: str, payload: dict) -> str:
    sdir = os.path.join(RESULTS_DIR, session_id)
    os.makedirs(sdir, exist_ok=True)
    path = os.path.join(sdir, "summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def load_summary(session_id: str) -> Optional[dict]:
    path = os.path.join(RESULTS_DIR, session_id, "summary.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# Optional: AES-256 at-rest encryption (example only)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_bytes_aes256_gcm(data: bytes, key32: bytes, iv12: bytes) -> bytes:
    """Example AES-256-GCM. Store IV separately (12 bytes)."""
    aesgcm = AESGCM(key32)
    return aesgcm.encrypt(iv12, data, None)


