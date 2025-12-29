#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCI/AD Patient Audio Analysis Script
Multi-dimensional analysis of 4 patient audio files with comprehensive visualizations

Author: Cognitive Assessment System
Date: 2025-01-XX
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
import seaborn as sns
import librosa
import librosa.display
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

warnings.filterwarnings('ignore')

# Try to import optional libraries
try:
    import parselmouth
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    print("⚠️ parselmouth not available. Voice quality features will be limited.")

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    print("⚠️ noisereduce not available. Noise reduction will be skipped.")

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    print("⚠️ webrtcvad not available. Using librosa-based VAD.")

# Set style
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('seaborn-darkgrid')
sns.set_palette("viridis")
sns.set_context("paper", font_scale=1.2)

# Colorblind-friendly colors
COLORS = {
    'normal': '#2E8B57',      # Sea green
    'mild': '#FFD700',         # Gold
    'severe': '#DC143C',       # Crimson
    'pause': '#FF4500',        # Orange red
    'anomaly': '#8B0000',      # Dark red
    'baseline': '#4682B4',    # Steel blue
    'highlight': '#FF1493'    # Deep pink
}

# MCI/AD Thresholds (based on research literature)
THRESHOLDS = {
    'speech_rate_min': 100,      # words/min (normal: 120-180)
    'pause_duration_abnormal': 2.0,  # seconds
    'jitter_normal_max': 1.0,   # %
    'shimmer_normal_max': 3.0,  # %
    'pitch_std_abnormal': 30,   # Hz
    'energy_drop_threshold': 0.3,  # relative
    'mfcc_variability_min': 0.5  # coefficient std
}


def load_and_preprocess(file_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Load M4A file, convert to WAV, apply preprocessing
    
    Args:
        file_path: Path to M4A file
        target_sr: Target sample rate (default 16kHz)
    
    Returns:
        audio: Preprocessed audio array
        sr: Sample rate
    """
    print(f"📂 Loading: {file_path}")
    
    try:
        # Load audio (librosa handles M4A automatically)
        audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
        print(f"   ✅ Loaded: {len(audio)/sr:.2f}s at {sr}Hz")
        
        # Apply noise reduction if available
        if NOISEREDUCE_AVAILABLE:
            print("   🔇 Applying noise reduction...")
            audio = nr.reduce_noise(y=audio, sr=sr, stationary=False)
        
        # Voice Activity Detection
        print("   🎤 Applying Voice Activity Detection...")
        audio = apply_vad(audio, sr)
        print(f"   ✅ After VAD: {len(audio)/sr:.2f}s")
        
        return audio, sr
    
    except Exception as e:
        print(f"   ❌ Error loading {file_path}: {e}")
        raise


def apply_vad(audio: np.ndarray, sr: int, frame_duration_ms: int = 30) -> np.ndarray:
    """
    Apply Voice Activity Detection to remove silence
    
    Args:
        audio: Audio signal
        sr: Sample rate
        frame_duration_ms: Frame duration in milliseconds
    
    Returns:
        audio: Audio with silence removed
    """
    if VAD_AVAILABLE:
        # Use webrtcvad for better accuracy
        vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3
        frame_size = int(sr * frame_duration_ms / 1000)
        
        # Process in frames
        frames = []
        for i in range(0, len(audio), frame_size):
            frame = audio[i:i+frame_size]
            if len(frame) == frame_size:
                # Convert to bytes (16-bit PCM)
                frame_bytes = (frame * 32767).astype(np.int16).tobytes()
                if vad.is_speech(frame_bytes, sr):
                    frames.append(frame)
        
        if frames:
            return np.concatenate(frames)
        return audio
    else:
        # Fallback: librosa-based VAD
        intervals = librosa.effects.split(audio, top_db=20)
        audio_clean = []
        for interval in intervals:
            audio_clean.append(audio[interval[0]:interval[1]])
        
        if audio_clean:
            return np.concatenate(audio_clean)
        return audio


def extract_acoustic_features(audio: np.ndarray, sr: int) -> Dict[str, any]:
    """
    Extract comprehensive acoustic features
    
    Args:
        audio: Audio signal
        sr: Sample rate
    
    Returns:
        features: Dictionary of extracted features
    """
    print("   🔍 Extracting acoustic features...")
    features = {}
    
    # 1. F0 (Pitch) Contour
    print("      - F0 contour...")
    f0 = librosa.yin(audio, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    f0[f0 == 0] = np.nan  # Remove unvoiced frames
    
    if PARSELMOUTH_AVAILABLE:
        # Use Praat for more accurate F0
        sound = parselmouth.Sound(audio, sampling_frequency=sr)
        pitch = sound.to_pitch()
        f0_praat = pitch.selected_array['frequency']
        f0_praat[f0_praat == 0] = np.nan
        features['f0'] = f0_praat
        features['f0_times'] = pitch.xs()
    else:
        times = librosa.frames_to_time(np.arange(len(f0)), sr=sr)
        features['f0'] = f0
        features['f0_times'] = times
    
    features['f0_mean'] = np.nanmean(features['f0'])
    features['f0_std'] = np.nanstd(features['f0'])
    features['f0_range'] = np.nanmax(features['f0']) - np.nanmin(features['f0'])
    
    # 2. Speech Rate (syllables/second approximation)
    print("      - Speech rate...")
    # Use onset detection as proxy for syllables
    onsets = librosa.onset.onset_detect(y=audio, sr=sr, units='time')
    features['speech_rate'] = len(onsets) / (len(audio) / sr) if len(audio) > 0 else 0
    features['onsets'] = onsets
    
    # 3. Pause Analysis
    print("      - Pause patterns...")
    rms = librosa.feature.rms(y=audio)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    
    # Detect pauses (low RMS)
    pause_threshold = np.percentile(rms, 20)
    pause_mask = rms < pause_threshold
    
    # Find pause durations
    pause_intervals = []
    in_pause = False
    pause_start = 0
    
    for i, is_pause in enumerate(pause_mask):
        if is_pause and not in_pause:
            pause_start = rms_times[i]
            in_pause = True
        elif not is_pause and in_pause:
            pause_duration = rms_times[i] - pause_start
            if pause_duration > 0.1:  # Minimum 100ms
                pause_intervals.append((pause_start, pause_duration))
            in_pause = False
    
    features['pause_intervals'] = pause_intervals
    features['pause_durations'] = [p[1] for p in pause_intervals]
    features['total_pause_time'] = sum([p[1] for p in pause_intervals])
    features['speaking_time_ratio'] = 1 - (features['total_pause_time'] / (len(audio) / sr))
    
    # 4. Voice Quality (Jitter & Shimmer)
    print("      - Voice quality...")
    if PARSELMOUTH_AVAILABLE:
        try:
            sound = parselmouth.Sound(audio, sampling_frequency=sr)
            
            # Create PointProcess directly from Sound (correct method)
            # Using "To PointProcess (periodic, cc)" - cross-correlation method
            point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 600)
            
            # Jitter (pitch period variation) - returns ratio, convert to percentage
            jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            features['jitter'] = float(jitter) * 100 if jitter else 0.0
            
            # Shimmer (amplitude variation) - returns ratio, convert to percentage
            shimmer = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            features['shimmer'] = float(shimmer) * 100 if shimmer else 0.0
        except Exception as e:
            print(f"         ⚠️  Parselmouth error, using approximation: {e}")
            # Fallback to approximation
            f0_clean = features['f0'][~np.isnan(features['f0'])]
            if len(f0_clean) > 1:
                period_diffs = np.diff(1/f0_clean)
                features['jitter'] = np.std(period_diffs) / np.mean(1/f0_clean) * 100 if np.mean(1/f0_clean) > 0 else 0
            else:
                features['jitter'] = 0
            
            # Shimmer approximation from RMS
            rms_diff = np.diff(rms)
            features['shimmer'] = np.std(rms_diff) / np.mean(rms) * 100 if np.mean(rms) > 0 else 0
    else:
        # Approximation using F0
        f0_clean = features['f0'][~np.isnan(features['f0'])]
        if len(f0_clean) > 1:
            period_diffs = np.diff(1/f0_clean)
            features['jitter'] = np.std(period_diffs) / np.mean(1/f0_clean) * 100 if np.mean(1/f0_clean) > 0 else 0
        else:
            features['jitter'] = 0
        
        # Shimmer approximation from RMS
        rms_diff = np.diff(rms)
        features['shimmer'] = np.std(rms_diff) / np.mean(rms) * 100 if np.mean(rms) > 0 else 0
    
    # 5. MFCC
    print("      - MFCC coefficients...")
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    features['mfcc'] = mfcc
    features['mfcc_times'] = librosa.frames_to_time(np.arange(mfcc.shape[1]), sr=sr)
    features['mfcc_mean'] = np.mean(mfcc, axis=1)
    features['mfcc_std'] = np.std(mfcc, axis=1)
    features['mfcc_variability'] = np.mean(features['mfcc_std'])
    
    # 6. Spectral Features
    print("      - Spectral features...")
    spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
    
    features['spectral_centroid'] = spectral_centroids
    features['spectral_rolloff'] = spectral_rolloff
    features['spectral_bandwidth'] = spectral_bandwidth
    features['spectral_times'] = librosa.frames_to_time(np.arange(len(spectral_centroids)), sr=sr)
    
    # 7. Energy/Intensity Contour
    print("      - Energy contour...")
    features['energy'] = rms
    features['energy_times'] = rms_times
    features['energy_mean'] = np.mean(rms)
    features['energy_std'] = np.std(rms)
    
    # 8. Articulation Rate
    print("      - Articulation rate...")
    # Words per minute approximation (using onsets)
    features['articulation_rate'] = features['speech_rate'] * 60  # Convert to per minute
    
    print("   ✅ Feature extraction complete")
    return features


def detect_mci_indicators(features: Dict) -> Dict[str, any]:
    """
    Detect MCI/AD indicators from features
    
    Args:
        features: Extracted acoustic features
    
    Returns:
        indicators: Dictionary of detected indicators
    """
    indicators = {
        'speech_rate_abnormal': False,
        'pause_frequency_high': False,
        'pitch_instability': False,
        'jitter_abnormal': False,
        'shimmer_abnormal': False,
        'energy_decline': False,
        'mfcc_irregularity': False,
        'anomaly_timestamps': []
    }
    
    # Check speech rate
    if features.get('articulation_rate', 0) < THRESHOLDS['speech_rate_min']:
        indicators['speech_rate_abnormal'] = True
    
    # Check pause frequency
    pause_durations = features.get('pause_durations', [])
    long_pauses = [p for p in pause_durations if p > THRESHOLDS['pause_duration_abnormal']]
    if len(long_pauses) > len(pause_durations) * 0.2:  # >20% are long pauses
        indicators['pause_frequency_high'] = True
    
    # Check pitch instability
    if features.get('f0_std', 0) > THRESHOLDS['pitch_std_abnormal']:
        indicators['pitch_instability'] = True
    
    # Check jitter
    if features.get('jitter', 0) > THRESHOLDS['jitter_normal_max']:
        indicators['jitter_abnormal'] = True
    
    # Check shimmer
    if features.get('shimmer', 0) > THRESHOLDS['shimmer_normal_max']:
        indicators['shimmer_abnormal'] = True
    
    # Check energy decline
    energy = features.get('energy', [])
    if len(energy) > 10:
        first_half = np.mean(energy[:len(energy)//2])
        second_half = np.mean(energy[len(energy)//2:])
        if second_half < first_half * (1 - THRESHOLDS['energy_drop_threshold']):
            indicators['energy_decline'] = True
    
    # Check MFCC irregularity
    if features.get('mfcc_variability', 0) < THRESHOLDS['mfcc_variability_min']:
        indicators['mfcc_irregularity'] = True
    
    # Count total indicators
    indicators['total_indicators'] = sum([
        indicators['speech_rate_abnormal'],
        indicators['pause_frequency_high'],
        indicators['pitch_instability'],
        indicators['jitter_abnormal'],
        indicators['shimmer_abnormal'],
        indicators['energy_decline'],
        indicators['mfcc_irregularity']
    ])
    
    # Risk level
    if indicators['total_indicators'] >= 5:
        indicators['risk_level'] = 'High'
    elif indicators['total_indicators'] >= 3:
        indicators['risk_level'] = 'Moderate'
    else:
        indicators['risk_level'] = 'Low'
    
    return indicators


def plot_figure_1(data_list: List[Dict], output_path: str):
    """Figure 1: Waveform và Spectrogram Comparison"""
    print("📊 Creating Figure 1: Waveform & Spectrogram...")
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 12))
    fig.suptitle('Waveform và Spectrogram Comparison', fontsize=16, fontweight='bold', y=0.995)
    
    for idx, data in enumerate(data_list):
        audio = data['audio']
        sr = data['sr']
        features = data['features']
        filename = data['filename']
        
        times = np.linspace(0, len(audio)/sr, len(audio))
        
        # Column 1: Waveform
        ax1 = axes[idx, 0]
        ax1.plot(times, audio, color='#2E8B57', linewidth=0.5, alpha=0.7)
        
        # Amplitude envelope
        hop_length = 512
        rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
        ax1.plot(rms_times, rms, color='#DC143C', linewidth=2, label='Envelope')
        ax1.fill_between(rms_times, -rms, rms, alpha=0.3, color='#DC143C')
        
        # Mark long pauses
        pause_intervals = features.get('pause_intervals', [])
        for pause_start, pause_duration in pause_intervals:
            if pause_duration > 2.0:
                ax1.axvspan(pause_start, pause_start + pause_duration, 
                           color='red', alpha=0.3, label='Long Pause (>2s)' if pause_duration > 2.0 else '')
        
        ax1.set_xlabel('Time (s)', fontsize=11)
        ax1.set_ylabel('Amplitude', fontsize=11)
        ax1.set_title(f'{filename}\nWaveform', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right', fontsize=9)
        
        # Column 2: Spectrogram
        ax2 = axes[idx, 1]
        D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
        img = librosa.display.specshow(D, y_axis='mel', x_axis='time', sr=sr, ax=ax2, cmap='viridis')
        
        # Mark long pauses on spectrogram
        for pause_start, pause_duration in pause_intervals:
            if pause_duration > 2.0:
                ax2.axvspan(pause_start, pause_start + pause_duration, 
                           color='red', alpha=0.4, linewidth=2)
        
        ax2.set_title(f'{filename}\nMel Spectrogram', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Time (s)', fontsize=11)
        ax2.set_ylabel('Frequency (Hz)', fontsize=11)
        plt.colorbar(img, ax=ax2, format='%+2.0f dB', label='Magnitude (dB)')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def plot_figure_2(data_list: List[Dict], output_path: str):
    """Figure 2: Pitch Analysis - MCI Indicators"""
    print("📊 Creating Figure 2: Pitch Analysis...")
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 12))
    fig.suptitle('Pitch Analysis - MCI Indicators', fontsize=16, fontweight='bold', y=0.995)
    
    for idx, data in enumerate(data_list):
        features = data['features']
        filename = data['filename']
        
        f0 = features.get('f0', [])
        f0_times = features.get('f0_times', [])
        
        # Column 1: F0 Contour with confidence band
        ax1 = axes[idx, 0]
        
        if len(f0) > 0 and not np.all(np.isnan(f0)):
            f0_clean = f0[~np.isnan(f0)]
            times_clean = f0_times[~np.isnan(f0)]
            
            # Plot F0 contour
            ax1.plot(times_clean, f0_clean, color='#2E8B57', linewidth=1.5, label='F0 Contour', alpha=0.8)
            
            # Confidence band (mean ± std)
            f0_mean = np.nanmean(f0_clean)
            f0_std = np.nanstd(f0_clean)
            ax1.fill_between(times_clean, f0_mean - f0_std, f0_mean + f0_std, 
                           alpha=0.2, color='#4682B4', label='±1 Std')
            ax1.axhline(f0_mean, color='#DC143C', linestyle='--', linewidth=1, label='Mean')
            
            # Highlight pitch drops (sudden decreases >30Hz)
            f0_diff = np.diff(f0_clean)
            drop_indices = np.where(f0_diff < -30)[0]
            for drop_idx in drop_indices:
                if drop_idx < len(times_clean) - 1:
                    ax1.axvspan(times_clean[drop_idx], times_clean[drop_idx + 1], 
                             color='red', alpha=0.3)
                    ax1.annotate('Pitch Drop', 
                               xy=(times_clean[drop_idx], f0_clean[drop_idx]),
                               xytext=(10, 10), textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                               fontsize=8, arrowprops=dict(arrowstyle='->', color='red'))
        
        ax1.set_xlabel('Time (s)', fontsize=11)
        ax1.set_ylabel('Frequency (Hz)', fontsize=11)
        ax1.set_title(f'{filename}\nF0 Contour with Confidence Band', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right', fontsize=9)
        
        # Column 2: Pitch Variability over Time Windows
        ax2 = axes[idx, 1]
        
        if len(f0) > 0 and not np.all(np.isnan(f0)):
            f0_clean = f0[~np.isnan(f0)]
            times_clean = f0_times[~np.isnan(f0)]
            
            # Calculate rolling std
            window_size = min(50, len(f0_clean) // 10)
            if window_size > 1:
                pitch_std_rolling = []
                std_times = []
                for i in range(0, len(f0_clean) - window_size, window_size // 2):
                    window_std = np.std(f0_clean[i:i+window_size])
                    pitch_std_rolling.append(window_std)
                    std_times.append(times_clean[i + window_size // 2])
                
                ax2.plot(std_times, pitch_std_rolling, color='#FFD700', linewidth=2, label='Pitch Variability (Std)')
                ax2.axhline(THRESHOLDS['pitch_std_abnormal'], color='red', linestyle='--', 
                          linewidth=2, label=f'Abnormal Threshold ({THRESHOLDS["pitch_std_abnormal"]} Hz)')
                ax2.fill_between(std_times, 0, THRESHOLDS['pitch_std_abnormal'], 
                                alpha=0.2, color='green', label='Normal Range')
                ax2.fill_between(std_times, THRESHOLDS['pitch_std_abnormal'], 
                                max(pitch_std_rolling) if pitch_std_rolling else 50,
                                alpha=0.2, color='red', label='Abnormal Range')
        
        ax2.set_xlabel('Time (s)', fontsize=11)
        ax2.set_ylabel('Pitch Std (Hz)', fontsize=11)
        ax2.set_title(f'{filename}\nPitch Variability Over Time', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def plot_figure_3(data_list: List[Dict], output_path: str):
    """Figure 3: Speech Rate & Pause Patterns"""
    print("📊 Creating Figure 3: Speech Rate & Pause Patterns...")
    
    fig, axes = plt.subplots(4, 3, figsize=(18, 12))
    fig.suptitle('Speech Rate & Pause Patterns', fontsize=16, fontweight='bold', y=0.995)
    
    for idx, data in enumerate(data_list):
        audio = data['audio']
        sr = data['sr']
        features = data['features']
        filename = data['filename']
        
        times = np.linspace(0, len(audio)/sr, len(audio))
        
        # Column 1: Speech Rate Timeline
        ax1 = axes[idx, 0]
        
        # Calculate speech rate in sliding windows
        window_size = int(sr * 5)  # 5-second windows
        speech_rates = []
        rate_times = []
        
        for i in range(0, len(audio) - window_size, window_size // 2):
            window_audio = audio[i:i+window_size]
            onsets = librosa.onset.onset_detect(y=window_audio, sr=sr, units='time')
            rate = len(onsets) / 5 * 60  # Convert to words/min
            speech_rates.append(rate)
            rate_times.append(i / sr + 2.5)
        
        if speech_rates:
            ax1.plot(rate_times, speech_rates, color='#2E8B57', linewidth=2, marker='o', markersize=4)
            ax1.axhline(THRESHOLDS['speech_rate_min'], color='red', linestyle='--', 
                       linewidth=2, label=f'Slow Speech Threshold ({THRESHOLDS["speech_rate_min"]} wpm)')
            
            # Mark slow speech segments
            slow_mask = np.array(speech_rates) < THRESHOLDS['speech_rate_min']
            if np.any(slow_mask):
                for i, is_slow in enumerate(slow_mask):
                    if is_slow and i < len(rate_times):
                        ax1.axvspan(rate_times[i] - 2.5, rate_times[i] + 2.5, 
                                  color='red', alpha=0.3)
        
        ax1.set_xlabel('Time (s)', fontsize=11)
        ax1.set_ylabel('Speech Rate (words/min)', fontsize=11)
        ax1.set_title(f'{filename}\nSpeech Rate Timeline', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right', fontsize=9)
        
        # Column 2: Pause Duration Histogram
        ax2 = axes[idx, 1]
        
        pause_durations = features.get('pause_durations', [])
        if pause_durations:
            ax2.hist(pause_durations, bins=20, color='#4682B4', alpha=0.7, edgecolor='black')
            ax2.axvline(THRESHOLDS['pause_duration_abnormal'], color='red', 
                       linestyle='--', linewidth=2, label=f'Abnormal Threshold ({THRESHOLDS["pause_duration_abnormal"]}s)')
            
            # Color abnormal zone
            xlim = ax2.get_xlim()
            ax2.axvspan(THRESHOLDS['pause_duration_abnormal'], xlim[1], 
                       alpha=0.2, color='red', label='Abnormal Zone')
            ax2.axvspan(0, THRESHOLDS['pause_duration_abnormal'], 
                       alpha=0.2, color='green', label='Normal Zone')
        
        ax2.set_xlabel('Pause Duration (s)', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title(f'{filename}\nPause Duration Distribution', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.legend(loc='upper right', fontsize=9)
        
        # Column 3: Cumulative Pause Time Percentage
        ax3 = axes[idx, 2]
        
        if pause_durations:
            pause_intervals = features.get('pause_intervals', [])
            total_time = len(audio) / sr
            cumulative_pause = []
            cumulative_time = []
            current_pause = 0
            
            for pause_start, pause_duration in sorted(pause_intervals, key=lambda x: x[0]):
                current_pause += pause_duration
                cumulative_pause.append(current_pause / total_time * 100)
                cumulative_time.append(pause_start + pause_duration)
            
            if cumulative_time:
                ax3.plot(cumulative_time, cumulative_pause, color='#DC143C', linewidth=2, marker='o', markersize=3)
                ax3.fill_between(cumulative_time, 0, cumulative_pause, alpha=0.3, color='#DC143C')
        
        ax3.set_xlabel('Time (s)', fontsize=11)
        ax3.set_ylabel('Cumulative Pause Time (%)', fontsize=11)
        ax3.set_title(f'{filename}\nCumulative Pause Percentage', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def plot_figure_4(data_list: List[Dict], output_path: str):
    """Figure 4: Voice Quality Indicators"""
    print("📊 Creating Figure 4: Voice Quality Indicators...")
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 12))
    fig.suptitle('Voice Quality Indicators', fontsize=16, fontweight='bold', y=0.995)
    
    for idx, data in enumerate(data_list):
        features = data['features']
        filename = data['filename']
        
        # Column 1: Jitter & Shimmer Comparison
        ax1 = axes[idx, 0]
        
        jitter = features.get('jitter', 0)
        shimmer = features.get('shimmer', 0)
        
        categories = ['Jitter', 'Shimmer']
        values = [jitter, shimmer]
        thresholds = [THRESHOLDS['jitter_normal_max'], THRESHOLDS['shimmer_normal_max']]
        
        colors = []
        for i, (val, thresh) in enumerate(zip(values, thresholds)):
            if val > thresh:
                colors.append(COLORS['severe'])
            elif val > thresh * 0.7:
                colors.append(COLORS['mild'])
            else:
                colors.append(COLORS['normal'])
        
        bars = ax1.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax1.axhline(THRESHOLDS['jitter_normal_max'], color='red', linestyle='--', 
                   linewidth=2, label=f'Jitter Threshold ({THRESHOLDS["jitter_normal_max"]}%)')
        ax1.axhline(THRESHOLDS['shimmer_normal_max'], color='orange', linestyle='--', 
                   linewidth=2, label=f'Shimmer Threshold ({THRESHOLDS["shimmer_normal_max"]}%)')
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax1.set_ylabel('Value (%)', fontsize=11)
        ax1.set_title(f'{filename}\nJitter & Shimmer vs Baseline', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.legend(loc='upper right', fontsize=9)
        
        # Column 2: Energy Contour
        ax2 = axes[idx, 1]
        
        energy = features.get('energy', [])
        energy_times = features.get('energy_times', [])
        
        if len(energy) > 0:
            ax2.plot(energy_times, energy, color='#2E8B57', linewidth=2, label='Energy Contour', alpha=0.8)
            
            # Mark low energy segments (fatigue indicator)
            energy_mean = np.mean(energy)
            energy_threshold = energy_mean * 0.7
            low_energy_mask = energy < energy_threshold
            
            # Find continuous low energy segments
            in_low = False
            low_start = 0
            for i, is_low in enumerate(low_energy_mask):
                if is_low and not in_low:
                    low_start = energy_times[i] if i < len(energy_times) else 0
                    in_low = True
                elif not is_low and in_low:
                    low_end = energy_times[i-1] if i > 0 else energy_times[-1]
                    if low_end - low_start > 1.0:  # At least 1 second
                        ax2.axvspan(low_start, low_end, color='red', alpha=0.3)
                        ax2.annotate('Low Energy', 
                                   xy=((low_start + low_end)/2, energy_threshold),
                                   xytext=(0, 10), textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                                   fontsize=8, ha='center')
                    in_low = False
            
            ax2.axhline(energy_threshold, color='red', linestyle='--', 
                       linewidth=1, label='Low Energy Threshold')
            ax2.fill_between(energy_times, 0, energy_threshold, alpha=0.1, color='red')
        
        ax2.set_xlabel('Time (s)', fontsize=11)
        ax2.set_ylabel('Energy (RMS)', fontsize=11)
        ax2.set_title(f'{filename}\nEnergy Contour with Fatigue Indicators', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def plot_figure_5(data_list: List[Dict], output_path: str):
    """Figure 5: MFCC Heatmap Comparison"""
    print("📊 Creating Figure 5: MFCC Heatmap...")
    
    fig, axes = plt.subplots(4, 1, figsize=(16, 12))
    fig.suptitle('MFCC Heatmap Comparison', fontsize=16, fontweight='bold', y=0.995)
    
    for idx, data in enumerate(data_list):
        features = data['features']
        filename = data['filename']
        
        mfcc = features.get('mfcc', np.array([]))
        mfcc_times = features.get('mfcc_times', [])
        
        if mfcc.size > 0:
            # Normalize for better visualization
            mfcc_db = librosa.power_to_db(mfcc, ref=np.max)
            
            im = axes[idx].imshow(mfcc_db, aspect='auto', origin='lower', 
                                 interpolation='nearest', cmap='viridis')
            
            # Set ticks
            if len(mfcc_times) > 0:
                time_ticks = np.linspace(0, len(mfcc_times)-1, min(10, len(mfcc_times)))
                time_labels = [f'{mfcc_times[int(t)]:.1f}' for t in time_ticks]
                axes[idx].set_xticks(time_ticks)
                axes[idx].set_xticklabels(time_labels)
            
            axes[idx].set_yticks(range(13))
            axes[idx].set_yticklabels([f'MFCC {i+1}' for i in range(13)])
            
            # Highlight low variability regions
            mfcc_std = np.std(mfcc_db, axis=0)
            low_var_threshold = np.percentile(mfcc_std, 20)
            low_var_indices = np.where(mfcc_std < low_var_threshold)[0]
            
            for idx_var in low_var_indices:
                if idx_var < len(mfcc_times):
                    axes[idx].axvline(idx_var, color='red', linestyle='--', alpha=0.5, linewidth=1)
            
            axes[idx].set_xlabel('Time (s)', fontsize=11)
            axes[idx].set_ylabel('MFCC Coefficient', fontsize=11)
            axes[idx].set_title(f'{filename}\nMFCC Heatmap (13 coefficients)', fontsize=12, fontweight='bold')
            
            plt.colorbar(im, ax=axes[idx], format='%+2.0f dB', label='Magnitude (dB)')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def plot_figure_6(data_list: List[Dict], indicators_list: List[Dict], output_path: str):
    """Figure 6: Summary Dashboard - MCI/AD Risk Indicators"""
    print("📊 Creating Figure 6: Summary Dashboard...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), subplot_kw=dict(projection='polar'))
    fig.suptitle('Summary Dashboard - MCI/AD Risk Indicators', fontsize=16, fontweight='bold', y=0.995)
    
    categories = [
        'Speech Rate\nDeviation',
        'Pause\nFrequency',
        'Pitch\nInstability',
        'Jitter/Shimmer\nAbnormality',
        'Energy\nDecline',
        'Articulation\nDifficulty',
        'MFCC Pattern\nIrregularity',
        'Overall\nConfidence'
    ]
    
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    for idx, (data, indicators) in enumerate(zip(data_list, indicators_list)):
        features = data['features']
        filename = data['filename']
        
        ax = axes[idx // 2, idx % 2]
        
        # Calculate scores for each category (0-1 scale, normalized)
        scores = []
        
        # 1. Speech Rate Deviation
        speech_rate = features.get('articulation_rate', 0)
        if speech_rate < THRESHOLDS['speech_rate_min']:
            scores.append(1.0 - (speech_rate / THRESHOLDS['speech_rate_min']))
        else:
            scores.append(0.0)
        
        # 2. Pause Frequency
        pause_durations = features.get('pause_durations', [])
        long_pauses = [p for p in pause_durations if p > THRESHOLDS['pause_duration_abnormal']]
        scores.append(min(1.0, len(long_pauses) / max(1, len(pause_durations))))
        
        # 3. Pitch Instability
        f0_std = features.get('f0_std', 0)
        scores.append(min(1.0, f0_std / THRESHOLDS['pitch_std_abnormal']))
        
        # 4. Jitter/Shimmer Abnormality
        jitter = features.get('jitter', 0)
        shimmer = features.get('shimmer', 0)
        jitter_score = min(1.0, jitter / THRESHOLDS['jitter_normal_max'])
        shimmer_score = min(1.0, shimmer / THRESHOLDS['shimmer_normal_max'])
        scores.append((jitter_score + shimmer_score) / 2)
        
        # 5. Energy Decline
        energy = features.get('energy', [])
        if len(energy) > 10:
            first_half = np.mean(energy[:len(energy)//2])
            second_half = np.mean(energy[len(energy)//2:])
            if first_half > 0:
                decline_ratio = max(0, (first_half - second_half) / first_half)
                scores.append(min(1.0, decline_ratio / THRESHOLDS['energy_drop_threshold']))
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)
        
        # 6. Articulation Difficulty (proxy from speech rate and pause)
        articulation_score = (scores[0] + scores[1]) / 2
        scores.append(articulation_score)
        
        # 7. MFCC Pattern Irregularity
        mfcc_variability = features.get('mfcc_variability', 1.0)
        if mfcc_variability < THRESHOLDS['mfcc_variability_min']:
            scores.append(1.0 - (mfcc_variability / THRESHOLDS['mfcc_variability_min']))
        else:
            scores.append(0.0)
        
        # 8. Overall Confidence (average of all indicators)
        scores.append(np.mean(scores[:7]))
        
        scores += scores[:1]  # Complete the circle
        
        # Determine color based on risk level
        risk_level = indicators.get('risk_level', 'Low')
        if risk_level == 'High':
            color = COLORS['severe']
        elif risk_level == 'Moderate':
            color = COLORS['mild']
        else:
            color = COLORS['normal']
        
        # Plot
        ax.plot(angles, scores, 'o-', linewidth=2, color=color, label=filename)
        ax.fill(angles, scores, alpha=0.25, color=color)
        
        # Add threshold circles
        for threshold in [0.3, 0.6, 1.0]:
            ax.plot(angles, [threshold] * len(angles), '--', linewidth=0.5, 
                   color='gray', alpha=0.3)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{filename}\nRisk Level: {risk_level}', fontsize=11, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ Saved: {output_path}")


def generate_summary_report(data_list: List[Dict], indicators_list: List[Dict], output_path: str):
    """Generate text summary report"""
    print("📝 Generating summary report...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("MCI/AD PATIENT AUDIO ANALYSIS - SUMMARY REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall summary
        f.write("OVERALL SUMMARY\n")
        f.write("-" * 80 + "\n")
        for idx, (data, indicators) in enumerate(zip(data_list, indicators_list)):
            filename = data['filename']
            risk_level = indicators.get('risk_level', 'Unknown')
            total_indicators = indicators.get('total_indicators', 0)
            f.write(f"Patient {idx+1} ({filename}): {risk_level} Risk ({total_indicators}/7 indicators)\n")
        f.write("\n")
        
        # Detailed metrics for each patient
        for idx, (data, indicators) in enumerate(zip(data_list, indicators_list)):
            features = data['features']
            filename = data['filename']
            
            f.write("=" * 80 + "\n")
            f.write(f"PATIENT {idx+1}: {filename}\n")
            f.write("=" * 80 + "\n\n")
            
            # Basic metrics
            f.write("BASIC METRICS:\n")
            f.write(f"  Audio Duration: {len(data['audio'])/data['sr']:.2f} seconds\n")
            f.write(f"  Sample Rate: {data['sr']} Hz\n")
            f.write(f"  Speaking Time Ratio: {features.get('speaking_time_ratio', 0)*100:.1f}%\n")
            f.write(f"  Total Pause Time: {features.get('total_pause_time', 0):.2f} seconds\n\n")
            
            # Acoustic features
            f.write("ACOUSTIC FEATURES:\n")
            f.write(f"  F0 Mean: {features.get('f0_mean', 0):.1f} Hz\n")
            f.write(f"  F0 Std: {features.get('f0_std', 0):.1f} Hz\n")
            f.write(f"  F0 Range: {features.get('f0_range', 0):.1f} Hz\n")
            f.write(f"  Speech Rate: {features.get('speech_rate', 0):.2f} syllables/sec\n")
            f.write(f"  Articulation Rate: {features.get('articulation_rate', 0):.1f} words/min\n")
            f.write(f"  Jitter: {features.get('jitter', 0):.2f}%\n")
            f.write(f"  Shimmer: {features.get('shimmer', 0):.2f}%\n")
            f.write(f"  Energy Mean: {features.get('energy_mean', 0):.4f}\n")
            f.write(f"  Energy Std: {features.get('energy_std', 0):.4f}\n")
            f.write(f"  MFCC Variability: {features.get('mfcc_variability', 0):.4f}\n\n")
            
            # MCI Indicators
            f.write("MCI/AD INDICATORS DETECTED:\n")
            if indicators.get('speech_rate_abnormal', False):
                f.write("  ⚠️  Slow Speech Rate (<100 words/min)\n")
            if indicators.get('pause_frequency_high', False):
                f.write("  ⚠️  High Frequency of Long Pauses (>2s)\n")
            if indicators.get('pitch_instability', False):
                f.write("  ⚠️  Pitch Instability (Std >30Hz)\n")
            if indicators.get('jitter_abnormal', False):
                f.write("  ⚠️  Abnormal Jitter (>1.0%)\n")
            if indicators.get('shimmer_abnormal', False):
                f.write("  ⚠️  Abnormal Shimmer (>3.0%)\n")
            if indicators.get('energy_decline', False):
                f.write("  ⚠️  Energy Decline Over Time (Fatigue)\n")
            if indicators.get('mfcc_irregularity', False):
                f.write("  ⚠️  MFCC Pattern Irregularity (Reduced Variability)\n")
            
            if indicators.get('total_indicators', 0) == 0:
                f.write("  ✅ No significant indicators detected\n")
            
            f.write(f"\n  Risk Level: {indicators.get('risk_level', 'Unknown')}\n")
            f.write(f"  Total Indicators: {indicators.get('total_indicators', 0)}/7\n\n")
        
        # Ranking
        f.write("=" * 80 + "\n")
        f.write("RISK RANKING (Highest to Lowest)\n")
        f.write("=" * 80 + "\n")
        
        # Sort by risk level and total indicators
        patient_risks = []
        for idx, (data, indicators) in enumerate(zip(data_list, indicators_list)):
            risk_level = indicators.get('risk_level', 'Low')
            total_indicators = indicators.get('total_indicators', 0)
            risk_score = {'High': 3, 'Moderate': 2, 'Low': 1}.get(risk_level, 0)
            patient_risks.append((idx+1, data['filename'], risk_score, total_indicators))
        
        patient_risks.sort(key=lambda x: (x[2], x[3]), reverse=True)
        
        for rank, (patient_num, filename, risk_score, total_indicators) in enumerate(patient_risks, 1):
            risk_level = {3: 'High', 2: 'Moderate', 1: 'Low'}.get(risk_score, 'Unknown')
            f.write(f"{rank}. Patient {patient_num} ({filename}): {risk_level} Risk ({total_indicators} indicators)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"   ✅ Saved: {output_path}")


def main():
    """Main function"""
    print("=" * 80)
    print("MCI/AD PATIENT AUDIO ANALYSIS")
    print("=" * 80)
    print()
    
    # Find M4A files in backend directory
    backend_dir = Path(__file__).parent
    m4a_files = list(backend_dir.glob("*.m4a"))
    
    if len(m4a_files) == 0:
        print("❌ No M4A files found in backend directory!")
        print("   Please ensure 4 M4A files are present.")
        return
    
    if len(m4a_files) < 4:
        print(f"⚠️  Found only {len(m4a_files)} M4A file(s). Using available files.")
    
    # Sort files for consistent ordering
    m4a_files = sorted(m4a_files)[:4]
    
    print(f"📁 Found {len(m4a_files)} audio file(s):")
    for f in m4a_files:
        print(f"   - {f.name}")
    print()
    
    # Process each file
    data_list = []
    indicators_list = []
    
    for file_path in m4a_files:
        try:
            # Load and preprocess
            audio, sr = load_and_preprocess(str(file_path))
            
            # Extract features
            features = extract_acoustic_features(audio, sr)
            
            # Detect indicators
            indicators = detect_mci_indicators(features)
            
            data_list.append({
                'audio': audio,
                'sr': sr,
                'features': features,
                'filename': file_path.stem
            })
            indicators_list.append(indicators)
            
            print(f"✅ Processed: {file_path.name}")
            print()
        
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if len(data_list) == 0:
        print("❌ No files were successfully processed!")
        return
    
    # Create output directory
    output_dir = backend_dir / "mci_analysis_output"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)
    print()
    
    # Generate all figures
    plot_figure_1(data_list, str(output_dir / "patient_analysis_fig1.png"))
    plot_figure_2(data_list, str(output_dir / "patient_analysis_fig2.png"))
    plot_figure_3(data_list, str(output_dir / "patient_analysis_fig3.png"))
    plot_figure_4(data_list, str(output_dir / "patient_analysis_fig4.png"))
    plot_figure_5(data_list, str(output_dir / "patient_analysis_fig5.png"))
    plot_figure_6(data_list, indicators_list, str(output_dir / "patient_analysis_fig6.png"))
    
    # Generate summary report
    generate_summary_report(data_list, indicators_list, str(output_dir / "summary_report.txt"))
    
    print()
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"📊 Output files saved to: {output_dir}")
    print()
    print("Generated files:")
    print("  - patient_analysis_fig1.png (Waveform & Spectrogram)")
    print("  - patient_analysis_fig2.png (Pitch Analysis)")
    print("  - patient_analysis_fig3.png (Speech Rate & Pause Patterns)")
    print("  - patient_analysis_fig4.png (Voice Quality Indicators)")
    print("  - patient_analysis_fig5.png (MFCC Heatmap)")
    print("  - patient_analysis_fig6.png (Summary Dashboard)")
    print("  - summary_report.txt (Detailed Metrics & Risk Assessment)")
    print()


if __name__ == "__main__":
    main()

