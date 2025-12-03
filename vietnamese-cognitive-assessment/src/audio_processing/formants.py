from __future__ import annotations

from typing import Dict

import numpy as np
import parselmouth


def extract_formants_vietnamese(
    audio_path: str,
    time_step: float = 0.01,
    max_formants: int = 5,
    max_frequency: float = 5500.0,
) -> Dict[str, float]:
    """
    Extract formant frequencies (F1, F2, F3) from Vietnamese speech using Praat/parselmouth.

    Returns:
        dict: keys f1_mean, f1_std, f2_mean, f2_std, f3_mean, formant_dispersion
    """
    sound = parselmouth.Sound(audio_path)
    formants = sound.to_formant_burg(
        time_step=time_step,
        max_number_of_formants=max_formants,
        maximum_formant=max_frequency,
        window_length=0.025,
        pre_emphasis_from=50.0,
    )

    f1_values: list[float] = []
    f2_values: list[float] = []
    f3_values: list[float] = []

    t = 0.0
    while t < sound.get_total_duration():
        f1 = formants.get_value_at_time(1, t)
        f2 = formants.get_value_at_time(2, t)
        f3 = formants.get_value_at_time(3, t)
        if not np.isnan(f1):
            f1_values.append(float(f1))
        if not np.isnan(f2):
            f2_values.append(float(f2))
        if not np.isnan(f3):
            f3_values.append(float(f3))
        t += time_step

    def safe_mean(x: list[float]) -> float:
        return float(np.mean(x)) if x else float("nan")

    f1_mean = safe_mean(f1_values)
    f2_mean = safe_mean(f2_values)
    f3_mean = safe_mean(f3_values)

    return {
        "f1_mean": f1_mean,
        "f1_std": float(np.std(f1_values)) if f1_values else float("nan"),
        "f2_mean": f2_mean,
        "f2_std": float(np.std(f2_values)) if f2_values else float("nan"),
        "f3_mean": f3_mean,
        "formant_dispersion": (f2_mean - f1_mean) if (not np.isnan(f1_mean) and not np.isnan(f2_mean)) else float("nan"),
    }



