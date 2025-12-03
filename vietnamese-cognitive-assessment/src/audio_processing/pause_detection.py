from __future__ import annotations

from typing import Dict, List, Tuple

import librosa
import numpy as np


class PauseDetector:
    """Voice Activity Detection and pause analysis for cognitive assessment."""

    def __init__(self, threshold_db: float = -40.0, min_pause_duration: float = 0.2):
        self.threshold_db = float(threshold_db)
        self.min_pause_duration = float(min_pause_duration)

    def detect_speech_segments(self, audio_path: str) -> List[Tuple[float, float]]:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        mask = rms_db > self.threshold_db
        hop_time = 512 / sr
        segments: List[Tuple[float, float]] = []
        state = False
        start = 0.0
        for i, m in enumerate(mask):
            t = i * hop_time
            if m and not state:
                state = True
                start = t
            elif (not m) and state:
                end = t
                if end - start > 0:
                    segments.append((start, end))
                state = False
        if state:
            segments.append((start, len(y) / sr))
        return segments

    def analyze_pauses(self, audio_path: str) -> Dict[str, float]:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        total_duration = len(y) / sr
        speech = self.detect_speech_segments(audio_path)
        # derive pauses as gaps between speech segments
        pauses: List[Tuple[float, float]] = []
        cur = 0.0
        for (s, e) in speech:
            if s - cur >= self.min_pause_duration:
                pauses.append((cur, s))
            cur = e
        if total_duration - cur >= self.min_pause_duration:
            pauses.append((cur, total_duration))

        pause_durs = [b - a for (a, b) in pauses]
        total_pause = float(sum(pause_durs))
        long_pauses = [d for d in pause_durs if d > 2.0]

        return {
            "pause_frequency": len(pauses) / (total_duration / 60.0) if total_duration > 0 else 0.0,
            "pause_mean_duration": float(np.mean(pause_durs)) if pause_durs else 0.0,
            "pause_ratio": (total_pause / total_duration) if total_duration > 0 else 0.0,
            "long_pause_count": int(len(long_pauses)),
            "speech_time": float(total_duration - total_pause),
        }


def calculate_speech_rate(audio_path: str, transcript: str) -> Dict[str, float]:
    from underthesea import word_tokenize

    tokens = word_tokenize(transcript)
    num_syllables = int(len(tokens))

    detector = PauseDetector()
    info = detector.analyze_pauses(audio_path)
    speech_time = max(info["speech_time"], 1e-6)

    speech_rate = num_syllables / speech_time
    articulation_rate = num_syllables / (speech_time + max(info["pause_mean_duration"], 1e-6))

    return {
        "speech_rate": float(speech_rate),
        "articulation_rate": float(articulation_rate),
        "num_syllables": num_syllables,
    }


