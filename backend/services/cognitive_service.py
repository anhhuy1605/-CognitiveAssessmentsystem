import os
import numpy as np
import librosa
import joblib
from typing import Dict

SVM_MODEL_PATH = os.getenv("SVM_MODEL_PATH", "/models/svm_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "/models/scaler.pkl")

try:
    SVM_MODEL = joblib.load(SVM_MODEL_PATH)
except Exception:
    SVM_MODEL = None

try:
    SCALER = joblib.load(SCALER_PATH)
except Exception:
    SCALER = None

def extract_acoustic_features(audio_path: str) -> Dict[str, float]:
    y, sr = librosa.load(audio_path, sr=None)
    if y.size == 0:
        return {
            "speaking_rate": 0,
            "utterance_count": 0,
            "avg_pause_duration": 0,
            "pause_count": 0,
            "avg_pitch_hz": 0,
            "pitch_stddev": 0,
            "amplitude_rms_mean": 0,
            "jitter": 0,
            "shimmer": 0,
            "total_duration_seconds": 0,
        }

    dur = librosa.get_duration(y=y, sr=sr)

    # RMS/amplitude
    rms = librosa.feature.rms(y=y)[0]
    amplitude_rms_mean = float(np.mean(rms))

    # Voice activity → utterances & pauses
    intervals = librosa.effects.split(y, top_db=25)
    utterance_count = int(len(intervals))
    pauses = []
    for i in range(1, len(intervals)):
        prev_end = intervals[i-1][1]
        start = intervals[i][0]
        pauses.append((start - prev_end) / sr)
    pause_count = len(pauses)
    avg_pause_duration = float(np.mean(pauses)) if pauses else 0.0

    # Speaking rate proxy via peak density in RMS
    from scipy.signal import find_peaks
    thr = float(np.percentile(rms, 75))
    peaks, _ = find_peaks(rms, height=thr, distance=max(1, int(0.15*len(rms)/(dur+1e-6))))
    syll_est = max(1, len(peaks))
    words_est = syll_est/1.4
    speaking_rate = float(words_est / max(dur, 1e-6))

    # Pitch via PYIN
    try:
        f0, voiced_flag, _ = librosa.pyin(y, fmin=50.0, fmax=500.0)
        f0_voiced = f0[voiced_flag] if f0 is not None and voiced_flag is not None else np.array([])
        f0_voiced = f0_voiced[~np.isnan(f0_voiced)]
        if f0_voiced.size > 0:
            avg_pitch_hz = float(np.mean(f0_voiced))
            pitch_stddev = float(np.std(f0_voiced))
        else:
            avg_pitch_hz, pitch_stddev = 0.0, 0.0
    except Exception:
        avg_pitch_hz, pitch_stddev = 0.0, 0.0

    # Simple jitter/shimmer proxies
    # NOTE: True jitter/shimmer need cycle analysis; here proxies use frame deltas
    jitter = float(np.mean(np.abs(np.diff(rms)))) if rms.size > 1 else 0.0
    shimmer = float(np.std(rms)) if rms.size > 0 else 0.0

    return {
        "speaking_rate": speaking_rate,
        "utterance_count": utterance_count,
        "avg_pause_duration": avg_pause_duration,
        "pause_count": pause_count,
        "avg_pitch_hz": avg_pitch_hz,
        "pitch_stddev": pitch_stddev,
        "amplitude_rms_mean": amplitude_rms_mean,
        "jitter": jitter,
        "shimmer": shimmer,
        "total_duration_seconds": float(dur),
    }

def svm_predict(features: Dict[str, float], model_path: str = None) -> float:
    model = SVM_MODEL
    if model_path:
        try:
            model = joblib.load(model_path)
        except Exception:
            pass
    if model is None:
        # fallback simple scoring
        return float(20 + features.get("speaking_rate", 2.0) * 2.0)

    vec = np.array([
        features.get("speaking_rate", 0),
        features.get("utterance_count", 0),
        features.get("avg_pause_duration", 0),
        features.get("avg_pitch_hz", 0),
        features.get("pitch_stddev", 0),
        features.get("amplitude_rms_mean", 0),
        features.get("jitter", 0),
        features.get("shimmer", 0),
        features.get("total_duration_seconds", 0),
    ], dtype=float).reshape(1, -1)

    if SCALER is not None:
        vec = SCALER.transform(vec)
    else:
        # MinMax fallback
        vmin = np.minimum(vec, 0)
        vmax = np.maximum(vec, 1)
        vec = (vec - vmin) / (vmax - vmin + 1e-6)

    try:
        pred = float(model.predict(vec)[0])
    except Exception:
        pred = float(20.0)
    return pred


