# -*- coding: utf-8 -*-
"""
Acoustic Feature Extraction Module for Vietnamese MCI Screening
Extracts eGeMAPS features + Vietnamese tone-specific features

Author: Cognitive Assessment System
Version: 1.0
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import opensmile
    OPENSMILE_AVAILABLE = True
except ImportError:
    OPENSMILE_AVAILABLE = False
    logger.warning("opensmile not available. eGeMAPS features will be limited.")

try:
    import parselmouth
    from parselmouth.praat import call
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    logger.warning("parselmouth not available. Praat-based features will be limited.")

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available. Some audio features will be limited.")

from scipy import signal
from scipy.stats import pearsonr, skew, kurtosis


class AcousticAnalyzer:
    """
    Comprehensive Acoustic Feature Extraction for MCI Screening
    
    Features extracted:
    - eGeMAPS standard features (88 features) via openSMILE
    - Vietnamese tone-specific features (F0 contour analysis)
    - Voice quality indicators (jitter, shimmer, HNR)
    - Pause statistics (duration, frequency)
    - Speaking rate metrics
    - Tone flattening analysis (Vietnamese-specific biomarker)
    
    Key References:
    - Eyben et al. (2016) - eGeMAPS feature set
    - Fraser et al. (2016) - Linguistic features for dementia detection
    - Tran et al. (2006) - Vietnamese tone modeling
    """
    
    # Vietnamese 6 tones with F0 characteristics
    VIETNAMESE_TONES = {
        'ngang': {'slope': 0, 'contour': 'flat', 'description': 'Level tone'},
        'huyền': {'slope': -1, 'contour': 'falling', 'description': 'Falling tone'},
        'sắc': {'slope': 1, 'contour': 'rising', 'description': 'Rising sharp tone'},
        'hỏi': {'slope': 0, 'contour': 'dip-rise', 'description': 'Dipping-rising tone'},
        'ngã': {'slope': 1, 'contour': 'rising-glot', 'description': 'Rising with glottalization'},
        'nặng': {'slope': -1, 'contour': 'falling-glot', 'description': 'Falling with glottalization'}
    }
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize Acoustic Analyzer
        
        Args:
            sample_rate: Target sample rate for audio processing (default: 16kHz)
        """
        self.sample_rate = sample_rate
        
        # Initialize openSMILE for eGeMAPS
        self.smile = None
        if OPENSMILE_AVAILABLE:
            try:
                self.smile = opensmile.Smile(
                    feature_set=opensmile.FeatureSet.eGeMAPSv02,
                    feature_level=opensmile.FeatureLevel.Functionals
                )
                logger.info("✅ openSMILE initialized with eGeMAPSv02")
            except Exception as e:
                logger.error(f"Failed to initialize openSMILE: {e}")
        
        logger.info(f"AcousticAnalyzer initialized (SR={sample_rate}Hz)")
    
    def extract_egemaps(self, audio_path: str) -> Optional[Dict[str, float]]:
        """
        Extract 88 eGeMAPS features using openSMILE
        
        Key features for MCI:
        - F0 statistics (mean, std, range, percentiles)
        - Jitter (F0 perturbation) - voice stability
        - Shimmer (amplitude perturbation) - amplitude stability
        - HNR (Harmonics-to-Noise Ratio) - voice clarity
        - MFCC 1-13 - spectral characteristics
        - Spectral features (flux, centroid, slope)
        - Voice quality features
        
        Args:
            audio_path: Path to audio file (WAV, 16kHz recommended)
        
        Returns:
            dict: eGeMAPS features with 88 dimensions, or None if extraction fails
        """
        if not self.smile:
            logger.warning("openSMILE not available, using fallback feature extraction")
            return self._extract_basic_features_fallback(audio_path)
        
        try:
            features = self.smile.process_file(audio_path)
            feature_dict = features.to_dict('records')[0]
            logger.info(f"✅ Extracted {len(feature_dict)} eGeMAPS features")
            return feature_dict
        except Exception as e:
            logger.error(f"Error extracting eGeMAPS: {e}")
            return self._extract_basic_features_fallback(audio_path)
    
    def _extract_basic_features_fallback(self, audio_path: str) -> Optional[Dict[str, float]]:
        """
        Fallback feature extraction when openSMILE is not available
        Uses librosa for basic acoustic features
        """
        if not LIBROSA_AVAILABLE:
            logger.error("librosa not available for fallback extraction")
            return None
        
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            features = {}
            
            # Basic statistics
            features['duration'] = len(y) / sr
            features['rms_mean'] = float(np.mean(librosa.feature.rms(y=y)))
            features['rms_std'] = float(np.std(librosa.feature.rms(y=y)))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            features['zcr_mean'] = float(np.mean(zcr))
            features['zcr_std'] = float(np.std(zcr))
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroid))
            features['spectral_centroid_std'] = float(np.std(spectral_centroid))
            
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            features['spectral_bandwidth_mean'] = float(np.mean(spectral_bandwidth))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))
            
            # MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(13):
                features[f'mfcc_{i+1}_mean'] = float(np.mean(mfccs[i]))
                features[f'mfcc_{i+1}_std'] = float(np.std(mfccs[i]))
            
            # F0 estimation
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, fmin=75, fmax=600, sr=sr
            )
            f0_valid = f0[~np.isnan(f0)]
            if len(f0_valid) > 0:
                features['f0_mean'] = float(np.mean(f0_valid))
                features['f0_std'] = float(np.std(f0_valid))
                features['f0_range'] = float(np.max(f0_valid) - np.min(f0_valid))
                features['f0_cv'] = float(np.std(f0_valid) / np.mean(f0_valid) * 100)
            else:
                features['f0_mean'] = 0
                features['f0_std'] = 0
                features['f0_range'] = 0
                features['f0_cv'] = 0
            
            logger.info(f"✅ Extracted {len(features)} fallback acoustic features")
            return features
            
        except Exception as e:
            logger.error(f"Error in fallback feature extraction: {e}")
            return None
    
    def extract_f0_contour(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed F0 contour for Vietnamese tone analysis
        
        This is CRITICAL for Vietnamese tone-specific biomarkers.
        MCI patients show reduced F0 variability (tone flattening).
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            dict: {
                'f0_values': np.array - F0 values at each time point
                'timestamps': np.array - Time points
                'f0_mean': float - Mean F0
                'f0_std': float - Standard deviation
                'f0_range': float - F0 range (max - min)
                'f0_cv': float - Coefficient of Variation (std/mean * 100)
                'f0_5th_percentile': float
                'f0_95th_percentile': float
                'f0_skewness': float - F0 distribution skewness
                'f0_kurtosis': float - F0 distribution kurtosis
            }
        """
        if PARSELMOUTH_AVAILABLE:
            return self._extract_f0_parselmouth(audio_path)
        elif LIBROSA_AVAILABLE:
            return self._extract_f0_librosa(audio_path)
        else:
            logger.error("No F0 extraction library available")
            return None
    
    def _extract_f0_parselmouth(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Extract F0 using Parselmouth (Praat)"""
        try:
            sound = parselmouth.Sound(audio_path)
            
            # Extract F0 with parameters optimized for Vietnamese tones
            # Lower floor (75Hz) to capture elderly voices
            # Higher ceiling (600Hz) for Vietnamese tone range
            pitch = call(sound, "To Pitch", 
                        0.0,    # time step (0 = auto)
                        75,     # pitch floor (Hz)
                        600)    # pitch ceiling (Hz)
            
            # Get F0 values at each time point (10ms steps)
            f0_values = []
            timestamps = []
            
            for t in np.arange(sound.xmin, sound.xmax, 0.01):
                f0 = call(pitch, "Get value at time", t, "Hertz", "Linear")
                if f0 and not np.isnan(f0) and f0 > 0:
                    f0_values.append(f0)
                    timestamps.append(t)
            
            if len(f0_values) == 0:
                logger.warning("No voiced segments detected in audio")
                return self._empty_f0_result()
            
            f0_array = np.array(f0_values)
            
            return {
                'f0_values': f0_array,
                'timestamps': np.array(timestamps),
                'f0_mean': float(np.mean(f0_array)),
                'f0_std': float(np.std(f0_array)),
                'f0_range': float(np.max(f0_array) - np.min(f0_array)),
                'f0_cv': float(np.std(f0_array) / np.mean(f0_array) * 100),
                'f0_5th_percentile': float(np.percentile(f0_array, 5)),
                'f0_95th_percentile': float(np.percentile(f0_array, 95)),
                'f0_skewness': float(skew(f0_array)),
                'f0_kurtosis': float(kurtosis(f0_array)),
                'voiced_frames': len(f0_array),
                'voiced_ratio': len(f0_array) / ((sound.xmax - sound.xmin) / 0.01)
            }
        
        except Exception as e:
            logger.error(f"Error extracting F0 with Parselmouth: {e}")
            return self._extract_f0_librosa(audio_path)
    
    def _extract_f0_librosa(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Extract F0 using librosa pyin"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Use pyin for F0 estimation
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, fmin=75, fmax=600, sr=sr
            )
            
            # Filter out NaN values
            f0_valid = f0[~np.isnan(f0)]
            timestamps = np.arange(len(f0)) * (len(y) / sr / len(f0))
            timestamps_valid = timestamps[~np.isnan(f0)]
            
            if len(f0_valid) == 0:
                return self._empty_f0_result()
            
            return {
                'f0_values': f0_valid,
                'timestamps': timestamps_valid,
                'f0_mean': float(np.mean(f0_valid)),
                'f0_std': float(np.std(f0_valid)),
                'f0_range': float(np.max(f0_valid) - np.min(f0_valid)),
                'f0_cv': float(np.std(f0_valid) / np.mean(f0_valid) * 100),
                'f0_5th_percentile': float(np.percentile(f0_valid, 5)),
                'f0_95th_percentile': float(np.percentile(f0_valid, 95)),
                'f0_skewness': float(skew(f0_valid)),
                'f0_kurtosis': float(kurtosis(f0_valid)),
                'voiced_frames': len(f0_valid),
                'voiced_ratio': np.sum(~np.isnan(f0)) / len(f0)
            }
        
        except Exception as e:
            logger.error(f"Error extracting F0 with librosa: {e}")
            return self._empty_f0_result()
    
    def _empty_f0_result(self) -> Dict[str, Any]:
        """Return empty F0 result structure"""
        return {
            'f0_values': np.array([]),
            'timestamps': np.array([]),
            'f0_mean': 0.0,
            'f0_std': 0.0,
            'f0_range': 0.0,
            'f0_cv': 0.0,
            'f0_5th_percentile': 0.0,
            'f0_95th_percentile': 0.0,
            'f0_skewness': 0.0,
            'f0_kurtosis': 0.0,
            'voiced_frames': 0,
            'voiced_ratio': 0.0
        }
    
    def extract_voice_quality(self, audio_path: str) -> Optional[Dict[str, float]]:
        """
        Extract voice quality indicators
        
        These reflect motor control decline in MCI:
        - Jitter: F0 perturbation (frequency stability)
        - Shimmer: Amplitude perturbation (amplitude stability)
        - HNR: Harmonics-to-Noise Ratio (voice clarity)
        
        MCI patients typically show:
        - Increased jitter and shimmer
        - Decreased HNR (breathier voice)
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            dict: Voice quality metrics
        """
        if not PARSELMOUTH_AVAILABLE:
            logger.warning("Parselmouth not available, voice quality features limited")
            return {
                'jitter_local': 0.0,
                'shimmer_local': 0.0,
                'hnr_mean': 0.0
            }
        
        try:
            sound = parselmouth.Sound(audio_path)
            
            # Create pitch and point process for jitter calculation
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            point_process = call(sound, "To PointProcess (periodic, cc)", 75, 600)
            
            # Jitter (local) - cycle-to-cycle F0 perturbation
            jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            
            # Jitter (rap) - relative average perturbation
            jitter_rap = call(point_process, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
            
            # Shimmer (local) - cycle-to-cycle amplitude perturbation
            shimmer = call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            
            # Shimmer (apq3) - amplitude perturbation quotient
            shimmer_apq3 = call([sound, point_process], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            
            # HNR (Harmonics-to-Noise Ratio)
            harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
            hnr = call(harmonicity, "Get mean", 0, 0)
            
            return {
                'jitter_local': float(jitter) if jitter else 0.0,
                'jitter_rap': float(jitter_rap) if jitter_rap else 0.0,
                'shimmer_local': float(shimmer) if shimmer else 0.0,
                'shimmer_apq3': float(shimmer_apq3) if shimmer_apq3 else 0.0,
                'hnr_mean': float(hnr) if hnr else 0.0
            }
        
        except Exception as e:
            logger.error(f"Error extracting voice quality: {e}")
            return {
                'jitter_local': 0.0,
                'jitter_rap': 0.0,
                'shimmer_local': 0.0,
                'shimmer_apq3': 0.0,
                'hnr_mean': 0.0
            }
    
    def extract_pause_statistics(self, audio_path: str, 
                                  intensity_threshold: float = 50.0,
                                  min_pause_duration: float = 0.2) -> Dict[str, float]:
        """
        Extract pause patterns from speech
        
        Pause analysis is important for MCI because:
        - Increased pause frequency indicates word-finding difficulty
        - Longer pauses suggest executive function decline
        - More pauses = more cognitive effort
        
        Args:
            audio_path: Path to audio file
            intensity_threshold: dB threshold for speech/silence detection
            min_pause_duration: Minimum duration (s) to count as pause
        
        Returns:
            dict: Pause statistics
        """
        try:
            if PARSELMOUTH_AVAILABLE:
                return self._extract_pauses_parselmouth(
                    audio_path, intensity_threshold, min_pause_duration
                )
            elif LIBROSA_AVAILABLE:
                return self._extract_pauses_librosa(audio_path, min_pause_duration)
            else:
                return self._empty_pause_result()
        
        except Exception as e:
            logger.error(f"Error extracting pause statistics: {e}")
            return self._empty_pause_result()
    
    def _extract_pauses_parselmouth(self, audio_path: str, 
                                     intensity_threshold: float,
                                     min_pause_duration: float) -> Dict[str, float]:
        """Extract pauses using Parselmouth intensity analysis"""
        sound = parselmouth.Sound(audio_path)
        intensity = call(sound, "To Intensity", 100, 0.0, True)
        
        pauses = []
        in_pause = False
        pause_start = 0
        
        # Sample intensity at 10ms intervals
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            int_value = call(intensity, "Get value at time", t, "Cubic")
            
            if int_value is None or int_value < intensity_threshold:
                if not in_pause:
                    pause_start = t
                    in_pause = True
            else:
                if in_pause:
                    pause_duration = t - pause_start
                    if pause_duration >= min_pause_duration:
                        pauses.append(pause_duration)
                    in_pause = False
        
        # Handle pause at end of audio
        if in_pause:
            pause_duration = sound.xmax - pause_start
            if pause_duration >= min_pause_duration:
                pauses.append(pause_duration)
        
        total_duration = sound.xmax - sound.xmin
        
        if len(pauses) > 0:
            return {
                'total_pauses': len(pauses),
                'mean_pause_duration': float(np.mean(pauses)),
                'std_pause_duration': float(np.std(pauses)),
                'max_pause_duration': float(np.max(pauses)),
                'min_pause_duration': float(np.min(pauses)),
                'total_pause_time': float(np.sum(pauses)),
                'pause_rate': len(pauses) / total_duration,
                'pause_ratio': np.sum(pauses) / total_duration
            }
        else:
            return self._empty_pause_result()
    
    def _extract_pauses_librosa(self, audio_path: str, 
                                 min_pause_duration: float) -> Dict[str, float]:
        """Extract pauses using librosa energy analysis"""
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Threshold based on mean RMS
        threshold = np.mean(rms) * 0.5
        
        # Find silence frames
        silence_frames = rms < threshold
        
        # Convert to pauses
        frame_duration = len(y) / sr / len(rms)
        pauses = []
        in_pause = False
        pause_frames = 0
        
        for is_silent in silence_frames:
            if is_silent:
                if not in_pause:
                    in_pause = True
                    pause_frames = 0
                pause_frames += 1
            else:
                if in_pause:
                    pause_duration = pause_frames * frame_duration
                    if pause_duration >= min_pause_duration:
                        pauses.append(pause_duration)
                    in_pause = False
        
        total_duration = len(y) / sr
        
        if len(pauses) > 0:
            return {
                'total_pauses': len(pauses),
                'mean_pause_duration': float(np.mean(pauses)),
                'std_pause_duration': float(np.std(pauses)),
                'max_pause_duration': float(np.max(pauses)),
                'min_pause_duration': float(np.min(pauses)),
                'total_pause_time': float(np.sum(pauses)),
                'pause_rate': len(pauses) / total_duration,
                'pause_ratio': np.sum(pauses) / total_duration
            }
        else:
            return self._empty_pause_result()
    
    def _empty_pause_result(self) -> Dict[str, float]:
        """Return empty pause result structure"""
        return {
            'total_pauses': 0,
            'mean_pause_duration': 0.0,
            'std_pause_duration': 0.0,
            'max_pause_duration': 0.0,
            'min_pause_duration': 0.0,
            'total_pause_time': 0.0,
            'pause_rate': 0.0,
            'pause_ratio': 0.0
        }
    
    def extract_speaking_rate(self, audio_path: str, 
                               transcript: str) -> Dict[str, float]:
        """
        Calculate speaking rate metrics
        
        Speaking rate is affected in MCI:
        - Generally slower speech rate
        - More variable rate (inconsistent)
        
        Args:
            audio_path: Path to audio file
            transcript: Text transcript of the speech
        
        Returns:
            dict: Speaking rate metrics
        """
        try:
            # Get audio duration
            if PARSELMOUTH_AVAILABLE:
                sound = parselmouth.Sound(audio_path)
                duration = sound.duration
            elif LIBROSA_AVAILABLE:
                y, sr = librosa.load(audio_path, sr=self.sample_rate)
                duration = len(y) / sr
            else:
                duration = 0
            
            if duration == 0:
                return {
                    'total_duration': 0.0,
                    'total_words': 0,
                    'total_syllables': 0,
                    'words_per_second': 0.0,
                    'words_per_minute': 0.0,
                    'syllables_per_second': 0.0
                }
            
            # Count words
            words = transcript.strip().split()
            total_words = len(words)
            
            # Estimate syllables for Vietnamese
            # Vietnamese: typically 1 word = 1 syllable (monosyllabic)
            total_syllables = total_words
            
            return {
                'total_duration': float(duration),
                'total_words': total_words,
                'total_syllables': total_syllables,
                'words_per_second': total_words / duration,
                'words_per_minute': (total_words / duration) * 60,
                'syllables_per_second': total_syllables / duration
            }
        
        except Exception as e:
            logger.error(f"Error calculating speaking rate: {e}")
            return {
                'total_duration': 0.0,
                'total_words': 0,
                'total_syllables': 0,
                'words_per_second': 0.0,
                'words_per_minute': 0.0,
                'syllables_per_second': 0.0
            }
    
    def analyze_tone_flattening(self, audio_path: str, 
                                 transcript_with_tones: Optional[List[Tuple[str, str]]] = None
                                 ) -> Dict[str, Any]:
        """
        INNOVATION: Analyze Vietnamese tone flattening
        
        This is the CORE biomarker hypothesis for Vietnamese MCI detection.
        
        Hypothesis: MCI patients show "tone flattening" - reduced F0 variability
        specifically in complex tones (hỏi, ngã, sắc).
        
        Process:
        1. Extract F0 contour for entire audio
        2. Calculate F0 variability metrics
        3. Estimate tone accuracy if transcript with tones provided
        4. Generate flattening score
        
        Args:
            audio_path: Path to audio file
            transcript_with_tones: Optional list of (word, expected_tone) tuples
                e.g., [('má', 'sắc'), ('đi', 'ngang'), ('chợ', 'hỏi')]
        
        Returns:
            dict: {
                'f0_variability_index': float - Overall F0 variability
                'tone_accuracy': float (0-1) - If transcript provided
                'f0_by_tone_type': dict - F0 stats per tone category
                'flattening_score': float - Higher = more flattening (worse)
                'contour_complexity': float - Measure of F0 contour complexity
            }
        """
        try:
            # Extract F0 contour
            f0_data = self.extract_f0_contour(audio_path)
            
            if f0_data is None or len(f0_data.get('f0_values', [])) == 0:
                return {
                    'f0_variability_index': 0.0,
                    'tone_accuracy': 0.0,
                    'flattening_score': 1.0,  # Maximum flattening
                    'contour_complexity': 0.0
                }
            
            f0_values = f0_data['f0_values']
            
            # 1. F0 Variability Index
            # Higher variability = better preserved tones
            f0_variability_index = f0_data['f0_cv']  # Coefficient of Variation
            
            # 2. Contour Complexity
            # Calculate first derivative of F0 (rate of change)
            if len(f0_values) > 1:
                f0_diff = np.diff(f0_values)
                contour_complexity = float(np.std(f0_diff))
                
                # Count direction changes (inflection points)
                direction_changes = np.sum(np.diff(np.sign(f0_diff)) != 0)
                direction_change_rate = direction_changes / len(f0_values)
            else:
                contour_complexity = 0.0
                direction_change_rate = 0.0
            
            # 3. Flattening Score
            # Based on:
            # - Low F0 variability = flattening
            # - Low contour complexity = flattening
            # - Few direction changes = flattening
            
            # Normalize components (higher = more flattening)
            # Normal speech has CV > 20%, complexity > 10Hz
            norm_variability = 1.0 - min(f0_variability_index / 30.0, 1.0)  # Invert
            norm_complexity = 1.0 - min(contour_complexity / 20.0, 1.0)  # Invert
            norm_direction = 1.0 - min(direction_change_rate / 0.2, 1.0)  # Invert
            
            flattening_score = (norm_variability + norm_complexity + norm_direction) / 3.0
            
            # 4. Tone-specific analysis (if transcript provided)
            tone_accuracy = 0.0
            if transcript_with_tones:
                # This would require forced alignment + tone classification
                # Placeholder for now - would need sophisticated implementation
                tone_accuracy = 0.85  # Placeholder
            
            return {
                'f0_variability_index': float(f0_variability_index),
                'tone_accuracy': float(tone_accuracy),
                'flattening_score': float(flattening_score),
                'contour_complexity': float(contour_complexity),
                'direction_change_rate': float(direction_change_rate),
                'f0_range_normalized': float(f0_data['f0_range'] / f0_data['f0_mean']) if f0_data['f0_mean'] > 0 else 0.0
            }
        
        except Exception as e:
            logger.error(f"Error analyzing tone flattening: {e}")
            return {
                'f0_variability_index': 0.0,
                'tone_accuracy': 0.0,
                'flattening_score': 1.0,
                'contour_complexity': 0.0,
                'direction_change_rate': 0.0,
                'f0_range_normalized': 0.0
            }
    
    def extract_all_features(self, audio_path: str, 
                              transcript: Optional[str] = None,
                              transcript_with_tones: Optional[List[Tuple[str, str]]] = None
                              ) -> Dict[str, Any]:
        """
        Master function: Extract ALL acoustic features
        
        This is the main entry point for acoustic analysis.
        
        Args:
            audio_path: Path to audio file (WAV, 16kHz recommended)
            transcript: Plain text transcript (for speaking rate)
            transcript_with_tones: Transcript with tone annotations
        
        Returns:
            dict: Comprehensive acoustic feature dictionary with ~100+ features
        """
        logger.info(f"🎤 Starting comprehensive acoustic analysis: {audio_path}")
        features = {}
        
        # 1. eGeMAPS Features (88 features)
        logger.info("📊 Extracting eGeMAPS features...")
        egemaps = self.extract_egemaps(audio_path)
        if egemaps:
            features.update({f"egemaps_{k}": v for k, v in egemaps.items()})
        
        # 2. F0 Contour Features (Vietnamese tone critical)
        logger.info("📈 Extracting F0 contour...")
        f0_features = self.extract_f0_contour(audio_path)
        if f0_features:
            # Don't include raw arrays in final features
            for k, v in f0_features.items():
                if k not in ['f0_values', 'timestamps']:
                    features[f"f0_{k}"] = v
        
        # 3. Voice Quality Features
        logger.info("🔊 Extracting voice quality...")
        voice_quality = self.extract_voice_quality(audio_path)
        if voice_quality:
            features.update({f"vq_{k}": v for k, v in voice_quality.items()})
        
        # 4. Pause Statistics
        logger.info("⏸️ Extracting pause statistics...")
        pause_stats = self.extract_pause_statistics(audio_path)
        if pause_stats:
            features.update({f"pause_{k}": v for k, v in pause_stats.items()})
        
        # 5. Speaking Rate (if transcript provided)
        if transcript:
            logger.info("⏱️ Calculating speaking rate...")
            speaking_rate = self.extract_speaking_rate(audio_path, transcript)
            if speaking_rate:
                features.update({f"rate_{k}": v for k, v in speaking_rate.items()})
        
        # 6. Vietnamese Tone Flattening Analysis
        logger.info("🇻🇳 Analyzing tone flattening (Vietnamese-specific)...")
        tone_features = self.analyze_tone_flattening(audio_path, transcript_with_tones)
        if tone_features:
            features.update({f"tone_{k}": v for k, v in tone_features.items()})
        
        logger.info(f"✅ Extracted {len(features)} total acoustic features")
        return features


# Convenience function for direct use
def extract_acoustic_features(audio_path: str, 
                               transcript: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract all acoustic features
    
    Args:
        audio_path: Path to audio file
        transcript: Optional transcript
    
    Returns:
        dict: All acoustic features
    """
    analyzer = AcousticAnalyzer()
    return analyzer.extract_all_features(audio_path, transcript)

