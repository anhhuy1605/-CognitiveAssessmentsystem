from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import librosa
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class F0Result:
    f0: np.ndarray
    voiced_flag: np.ndarray
    times: np.ndarray


def _median_filter(x: np.ndarray, k: int = 5) -> np.ndarray:
    if x is None or len(x) == 0:
        return np.array([])
    x = np.asarray(x, dtype=float)
    x[np.isinf(x)] = np.nan
    if np.all(np.isnan(x)):
        return x
    pad = k // 2
    # replace NaN with nearest non-NaN for padding
    filled = x.copy()
    if np.isnan(filled[0]):
        first_valid = np.nanmin(np.where(~np.isnan(filled), np.arange(len(filled)), np.inf))
        if np.isfinite(first_valid):
            filled[0:int(first_valid)] = filled[int(first_valid)]
    if np.isnan(filled[-1]):
        last_valid = np.nanmax(np.where(~np.isnan(filled), np.arange(len(filled)), -np.inf))
        if np.isfinite(last_valid):
            filled[int(last_valid)+1:] = filled[int(last_valid)]
    filled = np.where(np.isnan(filled), np.nanmedian(filled), filled)
    x_pad = np.pad(filled, (pad, pad), mode="edge")
    return np.array([np.median(x_pad[i:i + k]) for i in range(len(filled))], dtype=float)


def extract_f0_raw(audio_path: str, fmin: float = 75, fmax: float = 400) -> Dict[str, np.ndarray]:
    """
    Extract raw F0 using pYIN with robust handling.
    Returns dict with keys: 'f0', 'voiced_flag', 'times'.
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    if len(y) < sr // 2:
        raise ValueError("Audio too short (<0.5s)")
    f0, vflag, vprob = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr)
    hop_length = 512
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    f0_sm = _median_filter(f0, k=5)
    return {"f0": f0_sm, "voiced_flag": (vflag.astype(bool) if vflag is not None else ~np.isnan(f0_sm)), "times": times}


def segment_syllables_vietnamese(audio_path: str) -> List[Tuple[int, int, str]]:
    """
    Placeholder deterministic syllable segmentation based on energy (frame indices).
    Returns list of (start_frame, end_frame, text) with text empty if transcript unavailable.
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    thresh = np.max(rms) * 0.1
    voiced = rms > max(thresh, 1e-8)
    segments: List[Tuple[int, int, str]] = []
    state = 0
    start = 0
    for i, v in enumerate(voiced):
        if v and state == 0:
            state = 1
            start = i
        elif (not v) and state == 1:
            if i - start >= 3:
                segments.append((start, i, ""))
            state = 0
    if state == 1 and len(voiced) - start >= 3:
        segments.append((start, len(voiced), ""))
    return segments


def classify_vietnamese_tone(syllable_f0: np.ndarray) -> int:
    """
    Heuristic tone classifier by normalized F0 contour: 1..6
    1: ngang (flat), 2: huyền (fall), 3: sắc (rise), 4: hỏi (dip-rise), 5: ngã (rise + irregular), 6: nặng (drop + low)
    """
    x = syllable_f0
    x = x[~np.isnan(x)]
    if x.size < 5:
        return 1
    t = np.linspace(0, 1, num=len(x))
    # detrend by mean
    xz = (x - np.nanmean(x)) / (np.nanstd(x) + 1e-6)
    slope = (xz[-1] - xz[0])
    curvature = float(np.polyfit(t, xz, 2)[0]) if len(xz) >= 5 else 0.0
    range_z = np.nanmax(xz) - np.nanmin(xz)
    # crude rules
    if abs(slope) < 0.2 and range_z < 0.6:
        return 1  # ngang
    if slope > 0.4 and curvature >= -0.2:
        return 3  # sắc
    if slope < -0.4 and curvature <= 0.2:
        # drop; distinguish nặng by low offset
        if np.nanmean(x) < (np.nanmedian(x) - 0.1 * np.nanmedian(x)):
            return 6
        return 2  # huyền
    if curvature > 0.4 and range_z >= 0.8 and np.nanmin(xz) < -0.5 and np.nanmax(xz) > 0.2:
        return 4  # hỏi dip-rise
    if curvature > 0.2 and range_z >= 1.0:
        return 5  # ngã (rise/irregular)
    return 1


def load_vietnamese_tone_templates() -> Dict[int, np.ndarray]:
    """Return simple normalized F0 templates for 6 tones (unit-length contours)."""
    t = np.linspace(0, 1, 50)
    templates = {
        1: np.full_like(t, 1.0),                # ngang
        2: 1.2 - 0.8 * t,                       # huyền
        3: 0.8 + 0.8 * t,                       # sắc
        4: 1.0 - 0.6 * np.exp(-((t - 0.4) ** 2) / 0.02) + 0.2 * t,  # hỏi dip-rise
        5: 0.9 + 0.9 * t + 0.1 * np.sin(6 * np.pi * t),             # ngã
        6: 1.1 - 1.0 * t,                       # nặng (steeper fall)
    }
    return templates


def _interp_baseline(baseline: np.ndarray, target_len: int) -> np.ndarray:
    src = np.linspace(0, 1, num=len(baseline))
    dst = np.linspace(0, 1, num=target_len)
    return np.interp(dst, src, baseline)


def extract_f0_residual(audio_path: str) -> Dict[str, float]:
    """
    Extract tone-normalized F0 residual features.
    Follows the method in docs: subtract tone template from syllable F0 and aggregate statistics.
    """
    raw = extract_f0_raw(audio_path)
    f0 = raw["f0"]
    segments = segment_syllables_vietnamese(audio_path)
    templates = load_vietnamese_tone_templates()

    hop_length = 512
    residual_values: List[float] = []
    for start_frame, end_frame, _ in segments:
        s = start_frame
        e = end_frame
        f0_seg = f0[s:e]
        f0_seg = f0_seg[~np.isnan(f0_seg)]
        if f0_seg.size < 5:
            continue
        tone = classify_vietnamese_tone(f0_seg)
        baseline = templates.get(tone)
        if baseline is None or baseline.size == 0:
            continue
        baseline_i = _interp_baseline(baseline, len(f0_seg))
        # scale baseline to segment mean for fair subtraction
        scale = (np.nanmean(f0_seg) / (np.nanmean(baseline_i) + 1e-6))
        baseline_i = baseline_i * scale
        resid = f0_seg - baseline_i
        residual_values.extend(resid.tolist())

    residual = np.asarray(residual_values, dtype=float)
    if residual.size == 0:
        return {
            "f0_residual_mean": np.nan,
            "f0_residual_std": np.nan,
            "f0_residual_cv": np.nan,
            "f0_residual_range": np.nan,
            "f0_residual_iqr": np.nan,
        }
    mean = float(np.nanmean(residual))
    std = float(np.nanstd(residual))
    cv = float(std / (abs(mean) + 1e-6))
    rng = float(np.nanmax(residual) - np.nanmin(residual))
    iqr = float(np.nanpercentile(residual, 75) - np.nanpercentile(residual, 25))
    return {
        "f0_residual_mean": mean,
        "f0_residual_std": std,
        "f0_residual_cv": cv,
        "f0_residual_range": rng,
        "f0_residual_iqr": iqr,
    }


