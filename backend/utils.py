import os
import re
from functools import wraps
from flask import request, jsonify

API_TOKEN = os.getenv("API_TOKEN", "change-me-token")

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error":"unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        if token != API_TOKEN:
            return jsonify({"error":"forbidden"}), 403
        return fn(*args, **kwargs)
    return wrapper

# End-of-answer detection
DONE_REGEX = re.compile(r"\b(done|da\s*xong|đã\s*xong)\b", re.IGNORECASE)

def is_end_of_answer(text: str) -> bool:
    if not text:
        return False
    norm = text.lower().replace("ã", "a").replace("đ", "d")
    return bool(DONE_REGEX.search(text)) or bool(DONE_REGEX.search(norm))


