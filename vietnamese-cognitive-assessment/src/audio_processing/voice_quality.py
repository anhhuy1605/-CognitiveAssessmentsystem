from __future__ import annotations

from typing import Dict

import parselmouth


def extract_voice_quality(audio_path: str) -> Dict[str, float]:
    """
    Extract jitter, shimmer, and HNR from sustained/connected speech.
    Returns jitter_local (ratio), shimmer_local (ratio), hnr_mean (dB).
    """
    sound = parselmouth.Sound(audio_path)
    pitch = sound.to_pitch()
    point_process = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")

    jitter_local = float(parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3))
    shimmer_local = float(parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
    harmonicity = sound.to_harmonicity_cc()
    hnr_mean = float(parselmouth.praat.call(harmonicity, "Get mean", 0, 0))

    return {
        "jitter_local": jitter_local,
        "shimmer_local": shimmer_local,
        "hnr_mean": hnr_mean,
    }



