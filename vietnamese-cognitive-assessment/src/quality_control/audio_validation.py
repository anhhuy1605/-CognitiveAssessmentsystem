from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import librosa
import numpy as np


@dataclass
class AudioQualityReport:
    """Data class for audio quality assessment results."""

    status: str  # 'PASS' or 'REJECT'
    reason: Optional[str]
    snr: float
    clipping_ratio: float
    speech_ratio: float
    duration: float

    def is_valid(self) -> bool:
        return self.status == "PASS"


class AudioQualityController:
    """Complete implementation of quality control pipeline."""

    def __init__(
        self,
        min_snr: float = 15.0,
        max_clipping: float = 0.01,
        min_speech_ratio: float = 0.3,
        min_duration: float = 30.0,
    ):
        self.min_snr = float(min_snr)
        self.max_clipping = float(max_clipping)
        self.min_speech_ratio = float(min_speech_ratio)
        self.min_duration = float(min_duration)
        self.logger = logging.getLogger(__name__)

    def compute_snr(self, y: np.ndarray, sr: int) -> float:
        if y.size == 0:
            return 0.0
        # Estimate noise from first 0.5s (fallback to global std)
        n_len = min(int(0.5 * sr), len(y))
        noise_std = float(np.std(y[:n_len])) if n_len > 0 else float(np.std(y))
        signal_std = float(np.std(y))
        noise_std = max(noise_std, 1e-6)
        signal_std = max(signal_std, 1e-6)
        return float(20.0 * np.log10(signal_std / noise_std))

    def detect_clipping(self, y: np.ndarray) -> float:
        if y.size == 0:
            return 1.0
        clipped = int(np.sum(np.abs(y) > 0.95))
        return float(clipped / len(y))

    def compute_speech_ratio(self, y: np.ndarray, sr: int) -> float:
        if y.size == 0:
            return 0.0
        rms = librosa.feature.rms(y=y)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        speech_frames = int(np.sum(rms_db > -40))
        return float(speech_frames / max(len(rms_db), 1))

    def validate_audio(self, audio_path: str) -> AudioQualityReport:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = float(len(y) / sr)

        if duration < self.min_duration:
            return AudioQualityReport(
                status="REJECT",
                reason=f"Recording too short: {duration:.1f}s < {self.min_duration}s",
                snr=0.0,
                clipping_ratio=0.0,
                speech_ratio=0.0,
                duration=duration,
            )

        snr = self.compute_snr(y, sr)
        if snr < self.min_snr:
            return AudioQualityReport(
                status="REJECT",
                reason=f"SNR too low: {snr:.1f} dB < {self.min_snr} dB",
                snr=snr,
                clipping_ratio=0.0,
                speech_ratio=0.0,
                duration=duration,
            )

        clipping = self.detect_clipping(y)
        if clipping > self.max_clipping:
            return AudioQualityReport(
                status="REJECT",
                reason=f"Clipping detected: {clipping*100:.2f}% > {self.max_clipping*100:.2f}%",
                snr=snr,
                clipping_ratio=clipping,
                speech_ratio=0.0,
                duration=duration,
            )

        speech_ratio = self.compute_speech_ratio(y, sr)
        if speech_ratio < self.min_speech_ratio:
            return AudioQualityReport(
                status="REJECT",
                reason=f"Insufficient speech: {speech_ratio*100:.1f}% < {self.min_speech_ratio*100:.1f}%",
                snr=snr,
                clipping_ratio=clipping,
                speech_ratio=speech_ratio,
                duration=duration,
            )

        return AudioQualityReport(
            status="PASS",
            reason=None,
            snr=snr,
            clipping_ratio=clipping,
            speech_ratio=speech_ratio,
            duration=duration,
        )


def handle_missing_features(features: dict, threshold: float = 0.3) -> dict:
    """
    Replace small proportion of NaNs with simple imputations; raise if too many missing.
    """
    if not features:
        return {}
    values = list(features.values())
    total = len(values)
    missing = sum(1 for v in values if v is None or (isinstance(v, float) and np.isnan(v)))
    if total == 0:
        return features
    if (missing / total) > threshold:
        raise ValueError("Too many missing features; reject recording")
    # simple impute: replace NaN with 0.0
    clean = {}
    for k, v in features.items():
        if v is None:
            clean[k] = 0.0
        elif isinstance(v, float) and np.isnan(v):
            clean[k] = 0.0
        else:
            clean[k] = v
    return clean


def normalize_features(features: dict, age: int, gender: str, education: int) -> dict:
    """Add simple demographic normalization helpers (extendable)."""
    f = dict(features)
    # gender-based F0 relative feature if present
    if "f0_mean" in f:
        baseline = 120.0 if (str(gender).lower() in ["nam", "male", "m"]) else 220.0
        try:
            f["f0_mean_rel"] = float(f["f0_mean"]) / baseline
        except Exception:
            f["f0_mean_rel"] = 0.0
    f["age"] = int(age)
    f["education_years"] = int(education)
    f["gender_male"] = 1 if (str(gender).lower() in ["nam", "male", "m"]) else 0
    return f


