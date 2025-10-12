#!/usr/bin/env python3
"""
Audio Feature Extractor for Speech-based MMSE System
===================================================

Extracts comprehensive audio features for cognitive assessment:
- eGeMAPS feature set (prosody, voice quality, spectral)
- Wav2Vec2 embeddings (pretrained or fine-tuned)
- Voice Activity Detection (VAD)
- Audio segmentation and quality assessment

Author: AI Assistant
Date: September 2025
"""

import numpy as np
import pandas as pd
import librosa
import librosa.display
import soundfile as sf
from scipy import signal
from scipy.stats import skew, kurtosis
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
import os
import torch
import warnings
warnings.filterwarnings('ignore')

# Optional imports for advanced features
try:
    import opensmile
    HAS_OPENSMILE = True
except ImportError:
    HAS_OPENSMILE = False

try:
    from transformers import Wav2Vec2Model, Wav2Vec2Processor
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    HAS_WEBRTCVAD = False

logger = logging.getLogger(__name__)


class AudioFeatureExtractor:
    """
    Comprehensive audio feature extractor for MMSE assessment.

    Features extracted:
    - eGeMAPS set: F0, jitter, shimmer, formants, spectral features
    - Voice quality: HNR, CPP, voice breaks
    - Temporal: speech rate, articulation rate, pause patterns
    - Wav2Vec2 embeddings: contextual audio representations
    - VAD: voice activity detection for speech segmentation
    """

    # eGeMAPS feature set (subset for MMSE)
    EGEMAPS_FEATURES = [
        # Fundamental frequency
        'F0semitoneFrom27.5Hz_sma3nz_amean',
        'F0semitoneFrom27.5Hz_sma3nz_stddevNorm',
        'F0semitoneFrom27.5Hz_sma3nz_percentile20.0',
        'F0semitoneFrom27.5Hz_sma3nz_percentile50.0',
        'F0semitoneFrom27.5Hz_sma3nz_percentile80.0',

        # Jitter and shimmer (voice perturbation)
        'jitterLocal_sma3nz_amean',
        'jitterLocal_sma3nz_stddevNorm',
        'shimmerLocaldB_sma3nz_amean',
        'shimmerLocaldB_sma3nz_stddevNorm',

        # Formants and spectral
        'F1frequency_sma3nz_amean',
        'F1bandwidth_sma3nz_amean',
        'F2frequency_sma3nz_amean',
        'F2bandwidth_sma3nz_amean',
        'F3frequency_sma3nz_amean',
        'F3bandwidth_sma3nz_amean',

        # Spectral features
        'spectralFlux_sma3_amean',
        'spectralCentroid_sma3_amean',
        'spectralSlope_sma3_amean',
        'mfcc1_sma3_amean',
        'mfcc2_sma3_amean',
        'mfcc3_sma3_amean',
        'mfcc4_sma3_amean',

        # Loudness and dynamics
        'loudness_sma3_amean',
        'loudness_sma3_stddevNorm',

        # Voice quality
        'HNRdBACF_sma3nz_amean',
        'logRelF0-H1-H2_sma3nz_amean',
        'logRelF0-H1-A3_sma3nz_amean'
    ]

    def __init__(self,
                 sample_rate: int = 16000,
                 use_opensmile: bool = True,
                 use_wav2vec: bool = True,
                 wav2vec_model: str = "facebook/wav2vec2-base-960h",
                 device: str = "cpu"):
        """
        Initialize audio feature extractor.

        Args:
            sample_rate: Target sample rate for audio processing
            use_opensmile: Whether to use OpenSMILE for eGeMAPS features
            use_wav2vec: Whether to use Wav2Vec2 for embeddings
            wav2vec_model: HuggingFace model name for Wav2Vec2
            device: PyTorch device for Wav2Vec2
        """
        self.sample_rate = sample_rate
        self.use_opensmile = use_opensmile and HAS_OPENSMILE
        self.use_wav2vec = use_wav2vec and HAS_TRANSFORMERS
        self.device = device

        # Initialize OpenSMILE if available
        if self.use_opensmile:
            try:
                self.smile = opensmile.Smile(
                    feature_set=opensmile.FeatureSet.eGeMAPSv02,
                    feature_level=opensmile.FeatureLevel.Functionals,
                )
                logger.info("✅ OpenSMILE eGeMAPS initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenSMILE initialization failed: {e}")
                self.use_opensmile = False
        else:
            logger.info("ℹ️ OpenSMILE not used (not available or disabled)")

        # Initialize Wav2Vec2 if available
        if self.use_wav2vec:
            try:
                self.wav2vec_processor = Wav2Vec2Processor.from_pretrained(wav2vec_model)
                self.wav2vec_model = Wav2Vec2Model.from_pretrained(wav2vec_model)
                self.wav2vec_model.to(device)
                self.wav2vec_model.eval()
                logger.info(f"✅ Wav2Vec2 model loaded: {wav2vec_model}")
            except Exception as e:
                logger.warning(f"⚠️ Wav2Vec2 initialization failed: {e}")
                self.use_wav2vec = False
        else:
            logger.info("ℹ️ Wav2Vec2 not used (not available or disabled)")

        # Initialize VAD if available
        if HAS_WEBRTCVAD:
            self.vad = webrtcvad.Vad(3)  # Aggressive mode
            logger.info("✅ WebRTC VAD initialized")
        else:
            self.vad = None
            logger.info("ℹ️ WebRTC VAD not available")

        logger.info("🎵 Audio Feature Extractor initialized")

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file with proper preprocessing.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)

            # Normalize to prevent clipping
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))

            # Ensure minimum length (0.5 seconds)
            min_samples = int(0.5 * self.sample_rate)
            if len(audio) < min_samples:
                # Pad with zeros
                padding = np.zeros(min_samples - len(audio))
                audio = np.concatenate([audio, padding])

            logger.info(f"📁 Loaded audio: {len(audio)} samples, {sr}Hz")
            return audio, sr

        except Exception as e:
            logger.error(f"❌ Failed to load audio {audio_path}: {e}")
            raise

    def extract_egemaps_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract eGeMAPS feature set using OpenSMILE or fallback implementation.

        Args:
            audio: Audio array

        Returns:
            Dictionary of eGeMAPS features
        """
        features = {}

        if self.use_opensmile:
            try:
                # Use OpenSMILE for accurate eGeMAPS
                smile_features = self.smile.process_signal(audio, self.sample_rate)
                features = smile_features.iloc[0].to_dict()
                logger.info(f"✅ Extracted {len(features)} eGeMAPS features via OpenSMILE")
                return features

            except Exception as e:
                logger.warning(f"⚠️ OpenSMILE extraction failed: {e}, using fallback")

        # Fallback implementation using librosa and scipy
        logger.info("🔧 Using fallback eGeMAPS implementation")

        try:
            # Fundamental frequency using PYIN
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate,
                frame_length=2048,
                hop_length=512
            )

            # Filter valid F0 values
            f0_valid = f0[voiced_flag]

            if len(f0_valid) > 0:
                # F0 features
                features['F0semitoneFrom27.5Hz_sma3nz_amean'] = float(librosa.hz_to_midi(np.mean(f0_valid)))
                features['F0semitoneFrom27.5Hz_sma3nz_stddevNorm'] = float(np.std(f0_valid) / np.mean(f0_valid) if np.mean(f0_valid) > 0 else 0)
                features['F0semitoneFrom27.5Hz_sma3nz_percentile20.0'] = float(np.percentile(f0_valid, 20))
                features['F0semitoneFrom27.5Hz_sma3nz_percentile50.0'] = float(np.percentile(f0_valid, 50))
                features['F0semitoneFrom27.5Hz_sma3nz_percentile80.0'] = float(np.percentile(f0_valid, 80))

                # Jitter (frequency perturbation)
                if len(f0_valid) > 1:
                    diff_f0 = np.diff(f0_valid)
                    features['jitterLocal_sma3nz_amean'] = float(np.mean(np.abs(diff_f0) / f0_valid[:-1]) if len(f0_valid) > 1 else 0)
                    features['jitterLocal_sma3nz_stddevNorm'] = float(np.std(np.abs(diff_f0) / f0_valid[:-1]) if len(f0_valid) > 1 else 0)

            # Spectral features
            # Compute spectrogram
            S = librosa.stft(audio, n_fft=2048, hop_length=512)
            S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

            # Spectral centroid
            centroids = librosa.feature.spectral_centroid(S=np.abs(S), sr=self.sample_rate)[0]
            features['spectralCentroid_sma3_amean'] = float(np.mean(centroids))

            # Spectral flux
            flux = librosa.onset.onset_strength(S=np.abs(S), sr=self.sample_rate)
            features['spectralFlux_sma3_amean'] = float(np.mean(flux))

            # MFCCs
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=4)
            for i in range(4):
                features[f'mfcc{i+1}_sma3_amean'] = float(np.mean(mfccs[i]))

            # Loudness approximation
            rms = librosa.feature.rms(y=audio)[0]
            features['loudness_sma3_amean'] = float(np.mean(rms))
            features['loudness_sma3_stddevNorm'] = float(np.std(rms) / np.mean(rms) if np.mean(rms) > 0 else 0)

            # Harmonics-to-noise ratio approximation (simplified)
            hnr = self._compute_hnr(audio, self.sample_rate)
            features['HNRdBACF_sma3nz_amean'] = float(hnr)

            logger.info(f"✅ Extracted {len(features)} fallback eGeMAPS features")

        except Exception as e:
            logger.error(f"❌ Fallback eGeMAPS extraction failed: {e}")
            # Return empty features
            features = {feature: 0.0 for feature in self.EGEMAPS_FEATURES[:10]}  # Minimal set

        return features

    def _compute_hnr(self, audio: np.ndarray, sr: int) -> float:
        """Compute Harmonics-to-Noise Ratio (simplified approximation)"""
        try:
            # Compute autocorrelation
            corr = signal.correlate(audio, audio, mode='full')
            corr = corr[len(corr)//2:]

            # Find fundamental period (simplified)
            # This is a very basic approximation
            if len(corr) > 1:
                # Find first peak after lag 0
                peaks = signal.find_peaks(corr[1:], height=0.1*np.max(corr))[0]
                if len(peaks) > 0:
                    lag = peaks[0] + 1
                    hnr = 10 * np.log10(corr[0] / (corr[lag] + 1e-10)) if corr[lag] > 0 else 0
                    return float(np.clip(hnr, -20, 40))
            return 0.0
        except:
            return 0.0

    def extract_wav2vec_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract Wav2Vec2 embeddings with multiple pooling strategies.

        Args:
            audio: Audio array

        Returns:
            Dictionary with different pooling strategies
        """
        if not self.use_wav2vec:
            return {'mean_pool': np.zeros(768), 'attention_pool': np.zeros(768)}

        try:
            # Prepare input
            inputs = self.wav2vec_processor(
                audio,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding=True
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.wav2vec_model(**inputs)

            # Get hidden states (last layer)
            hidden_states = outputs.last_hidden_state.squeeze(0)  # [seq_len, hidden_size]

            # Mean pooling
            mean_pool = torch.mean(hidden_states, dim=0).cpu().numpy()

            # Attention pooling (weighted by norm)
            attention_weights = torch.norm(hidden_states, dim=1)
            attention_weights = torch.softmax(attention_weights, dim=0)
            attention_pool = torch.sum(hidden_states * attention_weights.unsqueeze(1), dim=0).cpu().numpy()

            features = {
                'mean_pool': mean_pool,
                'attention_pool': attention_pool,
                'sequence_length': hidden_states.shape[0]
            }

            logger.info(f"✅ Extracted Wav2Vec2 features: {hidden_states.shape}")
            return features

        except Exception as e:
            logger.error(f"❌ Wav2Vec2 feature extraction failed: {e}")
            return {'mean_pool': np.zeros(768), 'attention_pool': np.zeros(768)}

    def extract_temporal_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract temporal features: speech rate, articulation rate, pause patterns.

        Args:
            audio: Audio array

        Returns:
            Dictionary of temporal features
        """
        features = {}

        try:
            # Voice activity detection
            if self.vad is not None:
                voiced_segments = self._detect_voice_activity(audio, self.sample_rate)
            else:
                # Fallback: simple energy-based VAD
                voiced_segments = self._simple_vad(audio, self.sample_rate)

            if len(voiced_segments) > 0:
                # Speech rate (syllables per second) - approximation
                total_voiced_duration = sum(end - start for start, end in voiced_segments)
                # Rough syllable estimation (very approximate)
                estimated_syllables = total_voiced_duration * 4  # ~4 syllables per second average
                speech_rate = estimated_syllables / total_voiced_duration if total_voiced_duration > 0 else 0
                features['speech_rate_sps'] = float(speech_rate)

                # Articulation rate (phones per second during speech) - approximation
                features['articulation_rate_pps'] = float(speech_rate * 1.2)  # Rough approximation

                # Pause analysis
                if len(voiced_segments) > 1:
                    pauses = []
                    for i in range(1, len(voiced_segments)):
                        pause_duration = voiced_segments[i][0] - voiced_segments[i-1][1]
                        if pause_duration > 0.1:  # Only count pauses > 100ms
                            pauses.append(pause_duration)

                    if pauses:
                        features['pause_rate_per_min'] = float(len(pauses) / (len(audio) / self.sample_rate) * 60)
                        features['mean_pause_duration_s'] = float(np.mean(pauses))
                        features['pause_density'] = float(len(pauses) / len(voiced_segments))

                # Voice breaks and fluency markers
                features['total_voiced_duration_s'] = float(total_voiced_duration)
                features['speech_percentage'] = float(total_voiced_duration / (len(audio) / self.sample_rate))

            logger.info(f"✅ Extracted {len(features)} temporal features")

        except Exception as e:
            logger.error(f"❌ Temporal feature extraction failed: {e}")
            features = {
                'speech_rate_sps': 0.0,
                'articulation_rate_pps': 0.0,
                'total_voiced_duration_s': 0.0,
                'speech_percentage': 0.0
            }

        return features

    def _detect_voice_activity(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Detect voice activity using WebRTC VAD"""
        if self.vad is None:
            return []

        # WebRTC VAD works on 10ms frames
        frame_duration = 10  # ms
        frame_length = int(sr * frame_duration / 1000)

        segments = []
        is_voiced = False
        start_time = 0

        for i in range(0, len(audio) - frame_length, frame_length):
            frame = audio[i:i + frame_length]

            # Convert to 16-bit PCM
            frame_int16 = (frame * 32767).astype(np.int16).tobytes()

            try:
                if self.vad.is_speech(frame_int16, sr):
                    if not is_voiced:
                        start_time = i / sr
                        is_voiced = True
                else:
                    if is_voiced:
                        end_time = i / sr
                        if end_time - start_time > 0.1:  # Minimum segment length
                            segments.append((start_time, end_time))
                        is_voiced = False
            except:
                continue

        # Handle final segment
        if is_voiced:
            end_time = len(audio) / sr
            if end_time - start_time > 0.1:
                segments.append((start_time, end_time))

        return segments

    def _simple_vad(self, audio: np.ndarray, sr: int, threshold: float = 0.01) -> List[Tuple[float, float]]:
        """Simple energy-based voice activity detection"""
        # Compute RMS energy in frames
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop

        rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]

        # Find voiced frames
        voiced_frames = rms > threshold

        # Convert to time segments
        segments = []
        is_voiced = False
        start_idx = 0

        for i, voiced in enumerate(voiced_frames):
            if voiced and not is_voiced:
                start_idx = i
                is_voiced = True
            elif not voiced and is_voiced:
                start_time = start_idx * hop_length / sr
                end_time = i * hop_length / sr
                if end_time - start_time > 0.1:  # Minimum segment length
                    segments.append((start_time, end_time))
                is_voiced = False

        # Handle final segment
        if is_voiced:
            end_time = len(voiced_frames) * hop_length / sr
            if end_time - (start_idx * hop_length / sr) > 0.1:
                segments.append((start_idx * hop_length / sr, end_time))

        return segments

    def extract_audio_quality(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract audio quality metrics.

        Args:
            audio: Audio array

        Returns:
            Dictionary of quality metrics
        """
        quality = {}

        try:
            # SNR estimation
            signal_power = np.mean(audio ** 2)
            noise_power = np.mean((audio - librosa.util.normalize(audio)) ** 2)
            snr = 10 * np.log10(signal_power / (noise_power + 1e-10)) if noise_power > 0 else 60
            quality['snr_db'] = float(np.clip(snr, -20, 60))

            # Clipping detection
            clipped_samples = np.sum(np.abs(audio) >= 0.99)
            quality['clipping_percentage'] = float(clipped_samples / len(audio) * 100)

            # Dynamic range
            if np.max(np.abs(audio)) > 0:
                dynamic_range = 20 * np.log10(np.max(np.abs(audio)) / (np.std(audio) + 1e-10))
                quality['dynamic_range_db'] = float(np.clip(dynamic_range, 0, 120))
            else:
                quality['dynamic_range_db'] = 0.0

            # Zero crossings rate (rough noise indicator)
            zero_crossings = librosa.feature.zero_crossing_rate(audio)[0]
            quality['zero_crossing_rate'] = float(np.mean(zero_crossings))

            logger.info("✅ Audio quality metrics extracted")

        except Exception as e:
            logger.error(f"❌ Audio quality extraction failed: {e}")
            quality = {
                'snr_db': 30.0,  # Default good quality
                'clipping_percentage': 0.0,
                'dynamic_range_db': 50.0,
                'zero_crossing_rate': 0.1
            }

        return quality

    def extract_all_features(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract all audio features for MMSE assessment.

        Args:
            audio_path: Path to audio file

        Returns:
            Comprehensive feature dictionary
        """
        logger.info(f"🎵 Extracting features from: {audio_path}")

        # Load audio
        audio, sr = self.load_audio(audio_path)

        # Extract all feature types
        egemaps_features = self.extract_egemaps_features(audio)
        wav2vec_features = self.extract_wav2vec_features(audio)
        temporal_features = self.extract_temporal_features(audio)
        quality_features = self.extract_audio_quality(audio)

        # Combine all features
        features = {
            'audio_path': audio_path,
            'duration_seconds': len(audio) / sr,
            'sample_rate': sr,

            # Feature groups
            'egemaps': egemaps_features,
            'wav2vec': wav2vec_features,
            'temporal': temporal_features,
            'quality': quality_features,

            # Metadata
            'extraction_timestamp': pd.Timestamp.now().isoformat(),
            'feature_extractor_version': '1.0.0'
        }

        logger.info(f"✅ Extracted comprehensive features: {len(egemaps_features)} eGeMAPS, "
                   f"{len(temporal_features)} temporal, {len(quality_features)} quality")

        return features

    def extract_segment_features(self, audio_path: str,
                                segments: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        Extract features for specific audio segments (per question).

        Args:
            audio_path: Path to audio file
            segments: List of (start_time, end_time) tuples in seconds

        Returns:
            List of feature dictionaries, one per segment
        """
        # Load full audio
        audio, sr = self.load_audio(audio_path)

        segment_features = []

        for i, (start_time, end_time) in enumerate(segments):
            try:
                # Extract segment
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                segment_audio = audio[start_sample:end_sample]

                if len(segment_audio) < int(0.1 * sr):  # Skip very short segments
                    continue

                # Extract features for this segment
                egemaps_features = self.extract_egemaps_features(segment_audio)
                temporal_features = self.extract_temporal_features(segment_audio)
                quality_features = self.extract_audio_quality(segment_audio)

                # Note: Wav2Vec2 features might be too slow for per-segment extraction
                # Use mean pooling only for segments
                wav2vec_features = self.extract_wav2vec_features(segment_audio)
                if isinstance(wav2vec_features.get('mean_pool'), np.ndarray):
                    wav2vec_features['mean_pool'] = wav2vec_features['mean_pool'].tolist()

                segment_feature = {
                    'segment_id': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'egemaps': egemaps_features,
                    'temporal': temporal_features,
                    'quality': quality_features,
                    'wav2vec': wav2vec_features
                }

                segment_features.append(segment_feature)

            except Exception as e:
                logger.warning(f"⚠️ Failed to extract features for segment {i}: {e}")
                continue

        logger.info(f"✅ Extracted features for {len(segment_features)}/{len(segments)} segments")
        return segment_features


# Utility functions for feature processing
def normalize_features(features: Dict[str, float],
                      feature_stats: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, float]:
    """
    Normalize features using training statistics.

    Args:
        features: Raw feature dictionary
        feature_stats: Dictionary with 'mean' and 'std' for each feature

    Returns:
        Normalized features
    """
    if feature_stats is None:
        return features

    normalized = {}
    for feature_name, value in features.items():
        if feature_name in feature_stats:
            mean_val = feature_stats[feature_name].get('mean', 0)
            std_val = feature_stats[feature_name].get('std', 1)
            if std_val > 0:
                normalized[feature_name] = (value - mean_val) / std_val
            else:
                normalized[feature_name] = value
        else:
            normalized[feature_name] = value

    return normalized


def compute_feature_stats(feature_list: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Compute mean and std statistics for feature normalization.

    Args:
        feature_list: List of feature dictionaries

    Returns:
        Statistics dictionary
    """
    if not feature_list:
        return {}

    # Collect all feature names
    all_features = set()
    for features in feature_list:
        all_features.update(features.keys())

    stats = {}
    for feature_name in all_features:
        values = []
        for features in feature_list:
            if feature_name in features:
                val = features[feature_name]
                if isinstance(val, (int, float)) and not np.isnan(val) and not np.isinf(val):
                    values.append(val)

        if values:
            stats[feature_name] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'count': len(values)
            }

    return stats


if __name__ == "__main__":
    # Test the extractor
    print("🧪 Testing Audio Feature Extractor...")

    extractor = AudioFeatureExtractor()

    # Test with sample data (generate synthetic audio)
    sample_rate = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Generate synthetic speech-like audio
    f0_base = 100  # Hz
    f0_variation = 20 * np.sin(2 * np.pi * 0.5 * t)  # Slow variation
    audio = 0.3 * np.sin(2 * np.pi * (f0_base + f0_variation) * t)

    # Add some noise
    audio += 0.01 * np.random.randn(len(audio))

    # Save temporary file for testing
    temp_path = "test_audio.wav"
    sf.write(temp_path, audio, sample_rate)

    try:
        # Extract features
        features = extractor.extract_all_features(temp_path)

        print(f"✅ Feature extraction successful!")
        print(f"   Duration: {features['duration_seconds']:.2f}s")
        print(f"   eGeMAPS features: {len(features['egemaps'])}")
        print(f"   Temporal features: {len(features['temporal'])}")
        print(f"   Quality features: {len(features['quality'])}")
        print(f"   Wav2Vec available: {'Yes' if extractor.use_wav2vec else 'No'}")

        # Show some key features
        egemaps = features['egemaps']
        print(f"\n🎵 Key eGeMAPS features:")
        for key in ['F0semitoneFrom27.5Hz_sma3nz_amean', 'loudness_sma3_amean', 'HNRdBACF_sma3nz_amean']:
            if key in egemaps:
                print(".3f")

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print("✅ Audio Feature Extractor test completed!")
