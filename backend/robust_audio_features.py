#!/usr/bin/env python3
"""
Robust Audio Feature Extractor - V2.0
=====================================
Giải quyết: Feature extraction không ổn định, fallback values sai

Đây là phiên bản độc lập, không đụng vào các file hiện tại.
Bạn có thể import trong backend bằng:
    from backend.robust_audio_features import create_feature_extractor
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import librosa
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


@dataclass
class AudioQualityCheck:
    """Kiểm tra chất lượng audio trước khi extract features"""

    is_valid: bool
    duration: float
    snr_db: float
    has_speech: bool
    error: Optional[str] = None


class RobustAudioFeatureExtractor:
    """
    Feature extractor với validation nghiêm ngặt
    - Không dùng default fallback values
    - Báo lỗi rõ ràng khi không extract được
    - Chuẩn hóa features theo clinical standards
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

        # Clinical valid ranges (tham khảo từ nghiên cứu)
        self.valid_ranges = {
            "speech_rate": (0.5, 5.0),  # syllables/sec
            "pitch_mean": (80.0, 400.0),  # Hz (Vietnamese range)
            "number_utterances": (1, 100),  # count
            "silence_mean": (0.0, 3.0),  # seconds
        }

    def validate_audio(self, audio_path: str) -> AudioQualityCheck:
        """
        Kiểm tra chất lượng audio TRƯỚC KHI extract.
        Returns: AudioQualityCheck với thông tin chi tiết.
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
            duration = len(y) / sr

            if duration < 0.5:
                return AudioQualityCheck(
                    is_valid=False,
                    duration=duration,
                    snr_db=0.0,
                    has_speech=False,
                    error=f"Audio quá ngắn: {duration:.1f}s (cần tối thiểu 0.5s)",
                )

            rms = librosa.feature.rms(y=y)[0]
            if np.mean(rms) < 1e-4:
                return AudioQualityCheck(
                    is_valid=False,
                    duration=duration,
                    snr_db=-float("inf"),
                    has_speech=False,
                    error="Audio im lặng hoàn toàn (không có tín hiệu)",
                )

            signal_power = np.mean(y**2)
            noise_floor = np.percentile(rms, 10)  # Estimate noise from bottom 10%
            snr_db = 10 * np.log10(signal_power / (noise_floor**2 + 1e-10))

            intervals = librosa.effects.split(y, top_db=25)
            has_speech = len(intervals) > 0 and np.sum([e - s for s, e in intervals]) > sr * 0.3

            if not has_speech:
                return AudioQualityCheck(
                    is_valid=False,
                    duration=duration,
                    snr_db=snr_db,
                    has_speech=False,
                    error="Không phát hiện được giọng nói (có thể là noise)",
                )

            if snr_db < 5.0:
                return AudioQualityCheck(
                    is_valid=False,
                    duration=duration,
                    snr_db=snr_db,
                    has_speech=has_speech,
                    error=f"SNR quá thấp: {snr_db:.1f}dB (cần tối thiểu 5dB)",
                )

            return AudioQualityCheck(
                is_valid=True,
                duration=duration,
                snr_db=snr_db,
                has_speech=True,
            )

        except Exception as e:
            return AudioQualityCheck(
                is_valid=False,
                duration=0.0,
                snr_db=0.0,
                has_speech=False,
                error=f"Lỗi đọc file: {str(e)}",
            )

    def extract_features(self, audio_path: str) -> Dict[str, float]:
        """
        Extract 4 core features với validation nghiêm ngặt.
        Raises ValueError nếu không extract được.
        """
        quality = self.validate_audio(audio_path)
        if not quality.is_valid:
            raise ValueError(f"Audio quality check failed: {quality.error}")

        y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        features: Dict[str, float] = {}

        try:
            features["speech_rate"] = self._extract_speech_rate(y, sr)
        except Exception as e:
            logger.warning(f"Speech rate extraction failed: {e}")
            raise ValueError(f"Cannot extract speech_rate: {e}")

        try:
            features["number_utterances"] = self._extract_utterances(y, sr)
        except Exception as e:
            logger.warning(f"Utterances extraction failed: {e}")
            raise ValueError(f"Cannot extract number_utterances: {e}")

        try:
            features["silence_mean"] = self._extract_silence_mean(y, sr)
        except Exception as e:
            logger.warning(f"Silence extraction failed: {e}")
            raise ValueError(f"Cannot extract silence_mean: {e}")

        try:
            features["pitch_mean"] = self._extract_pitch_mean(y, sr)
        except Exception as e:
            logger.warning(f"Pitch extraction failed: {e}")
            raise ValueError(f"Cannot extract pitch_mean: {e}")

        validation_errors = []
        for feature_name, value in features.items():
            if np.isnan(value) or np.isinf(value):
                validation_errors.append(f"{feature_name}=NaN/Inf")
                continue

            valid_min, valid_max = self.valid_ranges[feature_name]
            if not (valid_min <= value <= valid_max):
                validation_errors.append(
                    f"{feature_name}={value:.2f} ngoài range [{valid_min}, {valid_max}]"
                )

        if validation_errors:
            raise ValueError(f"Feature validation failed: {'; '.join(validation_errors)}")

        features["audio_quality_snr"] = quality.snr_db
        features["audio_duration"] = quality.duration

        logger.info("✅ Extracted valid features: %s", features)
        return features

    def _extract_speech_rate(self, y: np.ndarray, sr: int) -> float:
        """Ước tính speech rate qua RMS peaks detection"""
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)  # 10ms hop
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        threshold = np.percentile(rms, 60)  # Adaptive threshold
        peaks, _ = signal.find_peaks(
            rms, height=threshold, distance=int(0.1 * sr / hop_length)
        )

        duration = len(y) / sr
        speech_rate = len(peaks) / duration if duration > 0 else 0.0

        return float(np.clip(speech_rate, 0.5, 5.0))

    def _extract_utterances(self, y: np.ndarray, sr: int) -> float:
        """Đếm số utterances qua Voice Activity Detection"""
        intervals = librosa.effects.split(y, top_db=25)

        valid_intervals = [
            (s, e) for s, e in intervals if (e - s) > sr * 0.1  # Min 100ms
        ]

        return float(len(valid_intervals))

    def _extract_silence_mean(self, y: np.ndarray, sr: int) -> float:
        """Tính mean pause duration"""
        intervals = librosa.effects.split(y, top_db=25)

        if len(intervals) <= 1:
            return 0.0

        pauses = []
        for i in range(1, len(intervals)):
            pause_samples = intervals[i][0] - intervals[i - 1][1]
            pause_duration = pause_samples / sr
            if pause_duration > 0.05:  # Min 50ms
                pauses.append(pause_duration)

        if not pauses:
            return 0.0

        return float(np.mean(pauses))

    def _extract_pitch_mean(self, y: np.ndarray, sr: int) -> float:
        """Extract mean pitch với pYIN - Vietnamese range"""
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=80.0,
            fmax=400.0,
            sr=sr,
            frame_length=2048,
            hop_length=512,
        )

        if f0 is None or voiced_flag is None:
            raise ValueError("pYIN failed to extract F0")

        f0_valid = f0[voiced_flag]

        if len(f0_valid) < 10:
            raise ValueError(f"Too few voiced frames: {len(f0_valid)}")

        q1, q3 = np.percentile(f0_valid, [25, 75])
        iqr = q3 - q1
        f0_filtered = f0_valid[
            (f0_valid >= q1 - 1.5 * iqr) & (f0_valid <= q3 + 1.5 * iqr)
        ]

        if len(f0_filtered) == 0:
            raise ValueError("All pitch values are outliers")

        return float(np.mean(f0_filtered))


def create_feature_extractor(sample_rate: int = 16000) -> RobustAudioFeatureExtractor:
    """Factory function để tạo extractor"""
    return RobustAudioFeatureExtractor(sample_rate=sample_rate)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python robust_audio_features.py <audio_file.wav>")
        sys.exit(1)

    extractor = create_feature_extractor()

    quality = extractor.validate_audio(sys.argv[1])
    print("\n📊 Audio Quality Check:")
    print(f"  Valid: {quality.is_valid}")
    print(f"  Duration: {quality.duration:.2f}s")
    print(f"  SNR: {quality.snr_db:.1f}dB")
    print(f"  Has Speech: {quality.has_speech}")
    if quality.error:
        print(f"  Error: {quality.error}")

    if quality.is_valid:
        try:
            features = extractor.extract_features(sys.argv[1])
            print("\n✅ Extracted Features:")
            for k, v in features.items():
                print(f"  {k}: {v:.2f}")
        except ValueError as e:
            print(f"\n❌ Feature extraction failed: {e}")
    else:
        print("\n❌ Audio quality check failed - cannot extract features")

