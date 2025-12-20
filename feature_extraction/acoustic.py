"""
Acoustic feature extraction for MMSE regression (ADReSS-style).

Implements formulas provided by user spec:
- MFCC (mean/std/delta/delta-delta)
- Pitch F0 statistics (mean/std/range)
- Speech rate (syllable estimate / total speaking time)
- Pause metrics (pause ratio, mean pause duration)
- Energy (sum of squares)

All functions are deterministic given the same input (seed where applicable).
"""

from __future__ import annotations

import numpy as np
import librosa


def _safe_nan_to_num(value: np.ndarray | float, fill: float = 0.0) -> np.ndarray | float:
    """Replace NaN/Inf with a finite fill value."""
    return np.nan_to_num(value, nan=fill, posinf=fill, neginf=fill)


def extract_acoustic_features(audio_path: str, sr: int = 16000) -> dict:
    """
    Extract acoustic features according to the provided mathematical spec.

    Args:
        audio_path: Path to audio file.
        sr: Target sampling rate (default 16 kHz).

    Returns:
        Dictionary of acoustic features (numeric).
    """
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    if y.size == 0:
        return {}

    # Energy
    energy = float(np.sum(np.square(y)))

    # MFCCs (use 13 coefficients as common in ADReSS; include deltas)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = _safe_nan_to_num(np.mean(mfcc, axis=1))
    mfcc_std = _safe_nan_to_num(np.std(mfcc, axis=1))
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta_delta = librosa.feature.delta(mfcc, order=2)
    mfcc_delta_mean = _safe_nan_to_num(np.mean(mfcc_delta, axis=1))
    mfcc_delta_std = _safe_nan_to_num(np.std(mfcc_delta, axis=1))
    mfcc_dd_mean = _safe_nan_to_num(np.mean(mfcc_delta_delta, axis=1))
    mfcc_dd_std = _safe_nan_to_num(np.std(mfcc_delta_delta, axis=1))

    # Pitch (F0) via YIN; compute mean/std/range
    try:
        f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
        f0 = f0[f0 > 0]
    except Exception:
        f0 = np.array([])
    if f0.size > 0:
        mean_f0 = float(np.mean(f0))
        std_f0 = float(np.std(f0))
        range_f0 = float(np.max(f0) - np.min(f0))
    else:
        mean_f0 = std_f0 = range_f0 = 0.0

    # Speech rate: syllable estimate via RMS peaks per second (proxy)
    duration = len(y) / sr
    rms = librosa.feature.rms(y=y)[0]
    thr = float(np.percentile(rms, 75))
    peaks, _ = librosa.util.peak_pick(rms, 3, 3, 3, 3, threshold=thr, wait=1)
    syllables_est = max(1, len(peaks))
    speech_rate = float(syllables_est / max(duration, 1e-6))

    # Pause metrics using energy-based VAD
    intervals = librosa.effects.split(y, top_db=25)
    pauses = []
    pause_ratio = 0.0
    mean_pause_dur = 0.0
    if intervals is not None and len(intervals) > 0:
        total_speech = np.sum([(e - s) for s, e in intervals]) / sr
        total_time = duration
        pause_ratio = float(max(0.0, (total_time - total_speech)) / max(total_time, 1e-6))
        # gaps between speech segments are pauses
        if len(intervals) > 1:
            for i in range(1, len(intervals)):
                gap = (intervals[i][0] - intervals[i - 1][1]) / sr
                if gap > 0:
                    pauses.append(gap)
        if pauses:
            mean_pause_dur = float(np.mean(pauses))

    features: dict[str, float] = {
        "energy": energy,
        "duration": duration,
        "speech_rate": speech_rate,  # syllables / total_speaking_time
        "pause_ratio": pause_ratio,
        "mean_pause_duration": mean_pause_dur,
        "mean_F0": mean_f0,
        "std_F0": std_f0,
        "range_F0": range_f0,
    }

    # Add MFCC stats
    for i, (m, s) in enumerate(zip(mfcc_mean, mfcc_std), start=1):
        features[f"mfcc_{i}_mean"] = float(m)
        features[f"mfcc_{i}_std"] = float(s)
    for i, (m, s) in enumerate(zip(mfcc_delta_mean, mfcc_delta_std), start=1):
        features[f"mfcc_delta_{i}_mean"] = float(m)
        features[f"mfcc_delta_{i}_std"] = float(s)
    for i, (m, s) in enumerate(zip(mfcc_dd_mean, mfcc_dd_std), start=1):
        features[f"mfcc_delta2_{i}_mean"] = float(m)
        features[f"mfcc_delta2_{i}_std"] = float(s)

    return features
