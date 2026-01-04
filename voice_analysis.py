import os
import sys
import io
import numpy as np
import pandas as pd
import librosa
import librosa.display
import parselmouth
from parselmouth.praat import call
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import signal, stats
from datetime import datetime
import warnings

# Force UTF-8 encoding for stdout to handle unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

# ============================================================
# 1. CONFIGURATION
# ============================================================

CONFIG = {
    'audio_dir': './backend/audio/',
    'labels_file': './backend/labels_m4a.csv',
    'output_dir': './analysis_output/',
    'sampling_rate': 16000,
    'thresholds': {
        'pitch_instability': 30,      # Hz - if f0_std > 30
        'slow_speech': 100,            # wpm - if articulation_rate < 100
        'high_pause_freq': 5,          # pauses/min - if pause_rate > 5
        'jitter': 1.0,                 # % - if jitter > 1.0%
        'shimmer': 3.0,                # % - if shimmer > 3.0%
        'low_energy': 0.01,            # RMS - if energy_mean < 0.01
        'energy_decline': 0.005,       # - if energy_decline > 0.005
        'mfcc_variability': 35         # - if mfcc_variability > 35
    }
}

COLORS = {
    'primary': '#2196F3',         # Blue
    'secondary': '#FF9800',       # Orange
    'success': '#4CAF50',         # Green
    'warning': '#FFC107',         # Yellow
    'danger': '#F44336',          # Red
    'normal_zone': '#C8E6C9',     # Light green
    'abnormal_zone': '#FFCDD2'    # Light red
}

# Ensure output directories exist
os.makedirs(CONFIG['output_dir'], exist_ok=True)
os.makedirs(os.path.join(CONFIG['output_dir'], 'graphs'), exist_ok=True)
os.makedirs(os.path.join(CONFIG['output_dir'], 'reports'), exist_ok=True)
os.makedirs(os.path.join(CONFIG['output_dir'], 'logs'), exist_ok=True)

# ============================================================
# 2. AUDIO ANALYZER CLASS
# ============================================================

class DetailedAudioAnalyzer:
    def __init__(self, audio_path, patient_id, metadata):
        self.audio_path = audio_path
        self.patient_id = patient_id
        self.metadata = metadata
        self.sr = CONFIG['sampling_rate']
        
        # Load audio with librosa
        self.y, _ = librosa.load(audio_path, sr=self.sr)
        
        # Create Parselmouth Sound object from numpy array (supports m4a via librosa)
        self.snd = parselmouth.Sound(self.y, sampling_frequency=self.sr)
        
        self.features = {}
        self.indicators = []

    def extract_basic_metrics(self):
        """Extract duration and speech/silence ratio"""
        duration = librosa.get_duration(y=self.y, sr=self.sr)
        
        # Simple voice activity detection based on energy
        S = librosa.feature.melspectrogram(y=self.y, sr=self.sr)
        log_S = librosa.power_to_db(S, ref=np.max)
        energy = np.mean(log_S, axis=0)
        threshold = np.mean(energy) - 10 # dB
        is_speech = energy > threshold
        
        speech_duration = np.sum(is_speech) * (len(self.y) / len(is_speech)) / self.sr
        silence_duration = duration - speech_duration
        
        self.features.update({
            'duration': duration,
            'speech_duration': speech_duration,
            'silence_duration': silence_duration,
            'speech_ratio': speech_duration / duration if duration > 0 else 0
        })

    def extract_pitch_features(self):
        """Extract F0 statistics using Praat"""
        pitch = call(self.snd, "To Pitch", 0.0, 75, 500)
        
        f0_values = []
        f0_times = []
        
        for i in range(pitch.get_number_of_frames()):
            time = pitch.get_time_from_frame_number(i+1)
            f0 = call(pitch, "Get value in frame", i+1, "Hertz")
            if f0 > 0:  # Valid F0 (voiced)
                f0_values.append(f0)
                f0_times.append(time)
            else:
                f0_values.append(np.nan) # Keep alignment for plotting
                f0_times.append(time)
        
        f0_clean = [f for f in f0_values if not np.isnan(f)]
        
        if f0_clean:
            f0_mean = np.mean(f0_clean)
            f0_std = np.std(f0_clean)
            
            # Check for instability indicator
            if f0_std > CONFIG['thresholds']['pitch_instability']:
                self.indicators.append('Pitch Instability (Std > 30Hz)')
                
            self.features.update({
                'f0_values': np.array(f0_values),
                'f0_times': np.array(f0_times),
                'f0_mean': f0_mean,
                'f0_std': f0_std,
                'f0_min': np.min(f0_clean),
                'f0_max': np.max(f0_clean),
                'f0_range': np.max(f0_clean) - np.min(f0_clean)
            })
        else:
             self.features.update({
                'f0_values': np.zeros_like(f0_times),
                'f0_times': np.array(f0_times),
                'f0_mean': 0, 'f0_std': 0, 'f0_min': 0, 'f0_max': 0, 'f0_range': 0
            })

    def extract_temporal_features(self):
        """Extract pauses and speech rate"""
        intervals = librosa.effects.split(self.y, top_db=25)
        
        pause_durations = []
        pause_times = []
        
        if len(intervals) > 0:
            # First silence
            if intervals[0][0] > 0:
                pause_durations.append(intervals[0][0] / self.sr)
                pause_times.append(0)
            
            # Middle silences
            for i in range(len(intervals) - 1):
                end_curr = intervals[i][1] / self.sr
                start_next = intervals[i+1][0] / self.sr
                pause_durations.append(start_next - end_curr)
                pause_times.append(end_curr)
                
            # Last silence
            if intervals[-1][1] < len(self.y):
                pause_durations.append((len(self.y) - intervals[-1][1]) / self.sr)
                pause_times.append(intervals[-1][1] / self.sr)
        
        n_pauses = len(pause_durations)
        duration_min = self.features['duration'] / 60
        pause_rate = n_pauses / duration_min if duration_min > 0 else 0
        
        # Estimate words from syllables (rough approximation)
        # Assuming avg 3-4 syllables per second for normal speech
        # Or peak counting on envelope
        
        # Simple word count approximation: pauses + 1 (very rough, but standard for no-text)
        # Better: use peaks in energy envelope
        envelope = np.abs(librosa.stft(self.y))
        envelope = np.sum(envelope, axis=0)
        peaks, _ = signal.find_peaks(envelope, distance=self.sr*0.2) # ~200ms min distance
        n_syllables = len(peaks)
        n_words_est = n_syllables / 1.5 # Avg syllables per word
        
        if self.features['speech_duration'] > 0:
            speech_rate = n_syllables / self.features['speech_duration']
            articulation_rate = n_words_est / (self.features['duration'] / 60) # wpm
        else:
            speech_rate, articulation_rate = 0, 0
            
        # Check indicators
        if articulation_rate < CONFIG['thresholds']['slow_speech']:
            self.indicators.append(f'Slow Speech (<{CONFIG["thresholds"]["slow_speech"]} wpm)')
            
        if pause_rate > CONFIG['thresholds']['high_pause_freq']:
            self.indicators.append(f'High Pause Frequency (>{CONFIG["thresholds"]["high_pause_freq"]}/min)')
            
        self.features.update({
            'pause_durations': pause_durations,
            'pause_times': pause_times,
            'n_pauses': n_pauses,
            'pause_rate': pause_rate,
            'pause_duration_mean': np.mean(pause_durations) if pause_durations else 0,
            'speech_rate': speech_rate,
            'articulation_rate': articulation_rate
        })

    def extract_voice_quality(self):
        """Extract Jitter, Shimmer, HNR, Energy"""
        # Jitter & Shimmer
        point_process = call(self.snd, "To PointProcess (periodic, cc)", 75, 500)
        try:
            jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100
            shimmer = call([self.snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100
        except:
            jitter, shimmer = 0.0, 0.0
            
        # HNR
        harmonicity = call(self.snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr = call(harmonicity, "Get mean", 0, 0)
        if hnr == -200: hnr = 0 # Silent
        
        # Energy
        intensity = call(self.snd, "To Intensity", 75, 0, "yes")
        energy_mean = call(intensity, "Get mean", 0, 0, "energy")
        
        # Indicators
        if jitter > CONFIG['thresholds']['jitter']:
            self.indicators.append(f'Abnormal Jitter (>{CONFIG["thresholds"]["jitter"]}%)')
        if shimmer > CONFIG['thresholds']['shimmer']:
            self.indicators.append(f'Abnormal Shimmer (>{CONFIG["thresholds"]["shimmer"]}%)')
        if energy_mean < CONFIG['thresholds']['low_energy']:
            self.indicators.append('Low Energy / Weak Voice')
            
        self.features.update({
            'jitter': jitter,
            'shimmer': shimmer,
            'hnr': hnr,
            'energy_mean': energy_mean
        })

    def extract_spectral_features(self):
        """Extract MFCCs"""
        mfcc = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        # Overall variability (sum of stds)
        mfcc_variability = np.sum(mfcc_std)
        if mfcc_variability > CONFIG['thresholds']['mfcc_variability']:
             self.indicators.append('High Spectral Variability')
             
        self.features.update({
            'mfcc': mfcc,
            'mfcc_mean': mfcc_mean,
            'mfcc_std': mfcc_std,
            'mfcc_variability': mfcc_variability
        })

    def extract_all_features(self):
        print(f"  Extracting features for {self.patient_id}...")
        self.extract_basic_metrics()
        self.extract_pitch_features()
        self.extract_temporal_features()
        self.extract_voice_quality()
        self.extract_spectral_features()
        return self.features, self.indicators

# ============================================================
# 3. VISUALIZER CLASS
# ============================================================

class DetailedVisualizer:
    def __init__(self, analyzer, output_dir):
        self.analyzer = analyzer
        self.output_dir = output_dir
        self.pid = analyzer.patient_id.replace(' ', '_')
        self.feats = analyzer.features
        
        # Set style
        plt.style.use('default') # Reset
        # Configure fonts and sizes manually to ensure consistency
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10 
        
    def save_fig(self, fig, name):
        path = os.path.join(self.output_dir, 'graphs', f"{self.pid}_{name}.png")
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def graph1_waveform_spectrogram(self):
        fig = plt.figure(figsize=(14, 6))
        gs = GridSpec(2, 1, height_ratios=[1, 1.5], hspace=0.3)
        
        # Subplot 1: Waveform
        ax1 = fig.add_subplot(gs[0])
        librosa.display.waveshow(self.analyzer.y, sr=self.analyzer.sr, ax=ax1, 
                               alpha=0.6, color=COLORS['primary'])
        ax1.set_title(f'Waveform - {self.analyzer.patient_id}', fontweight='bold')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Mel Spectrogram
        ax2 = fig.add_subplot(gs[1])
        S = librosa.feature.melspectrogram(y=self.analyzer.y, sr=self.analyzer.sr)
        S_dB = librosa.power_to_db(S, ref=np.max)
        img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', 
                                     sr=self.analyzer.sr, fmax=8000, ax=ax2, cmap='viridis')
        fig.colorbar(img, ax=ax2, format='%+2.0f dB')
        ax2.set_title('Mel Spectrogram')
        
        self.save_fig(fig, "1_waveform_spectrogram")

    def graph2_pitch_analysis(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
        
        # Subplot 1: F0 Contour
        times = self.feats['f0_times']
        f0 = self.feats['f0_values']
        
        ax1.plot(times, f0, '.', color=COLORS['primary'], markersize=2, label='F0 Raw')
        
        # Mean and Std
        mean_f0 = self.feats['f0_mean']
        std_f0 = self.feats['f0_std']
        ax1.axhline(mean_f0, color='darkblue', linestyle='--', linewidth=1.5, label='Mean F0')
        ax1.axhspan(mean_f0 - std_f0, mean_f0 + std_f0, color=COLORS['primary'], alpha=0.1, label='±1 Std')
        
        ax1.set_title(f'Pitch (F0) Analysis - Mean: {mean_f0:.1f}Hz, Std: {std_f0:.1f}Hz', fontweight='bold')
        ax1.set_ylabel('Frequency (Hz)')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Pitch Variability (simulated rolling std)
        # Note: f0 has NaNs, need to handle
        df_f0 = pd.DataFrame({'f0': f0})
        rolling_std = df_f0['f0'].rolling(window=50, min_periods=10).std()
        
        ax2.plot(times, rolling_std, color=COLORS['secondary'], linewidth=1.5)
        ax2.axhline(30, color=COLORS['danger'], linestyle='--', label='Threshold (30Hz)')
        
        # Highlight abnormal zones
        above_thresh = (rolling_std > 30).fillna(False)
        # We can't easily fill_between with NaNs in x, but rolling_std matches time index
        # Let's clean up for plotting
        valid_indices = ~np.isnan(times)
        ax2.fill_between(times[valid_indices], 0, rolling_std[valid_indices], 
                        where=above_thresh[valid_indices], color=COLORS['abnormal_zone'], alpha=0.5, label='Abnormal Area')
        
        ax2.set_title('Pitch Variability (Rolling Std)')
        ax2.set_ylabel('Std Dev (Hz)')
        ax2.set_xlabel('Time (s)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        self.save_fig(fig, "2_pitch_analysis")

    def graph3_speech_rate_pause(self):
        fig = plt.figure(figsize=(16, 6))
        gs = GridSpec(1, 3, width_ratios=[2, 1, 1])
        
        # Subplot 1: Pause Timeline included in waveform
        ax1 = fig.add_subplot(gs[0])
        librosa.display.waveshow(self.analyzer.y, sr=self.analyzer.sr, ax=ax1, alpha=0.4, color='gray')
        
        # Overlay pauses
        pause_starts = self.feats['pause_times']
        pause_durs = self.feats['pause_durations']
        
        for start, dur in zip(pause_starts, pause_durs):
            # start is actually end of previous segment for some logic, 
            # let's rely on stored list logic: pause_times stored start of silence?
            # In extract_temporal_features: pause_times.append(intervals[i][1]/sr) -> This is START of silence
            rect = mpatches.Rectangle((start, -1), dur, 2, color=COLORS['warning'], alpha=0.5)
            ax1.add_patch(rect)
            
        ax1.set_ylim(-1, 1)
        ax1.set_title('Pause Locations (Highlighted)', fontweight='bold')
        ax1.set_xlabel('Time (s)')
        
        # Subplot 2: Pause Duration Hist
        ax2 = fig.add_subplot(gs[1])
        if pause_durs:
            sns.histplot(pause_durs, bins=10, ax=ax2, color=COLORS['secondary'], kde=True)
            ax2.axvline(2.0, color=COLORS['danger'], linestyle='--', label='Abnormal (>2s)')
        ax2.set_title('Pause Duration Dist.')
        ax2.set_xlabel('Duration (s)')
        ax2.legend()
        
        # Subplot 3: Metrics Table (simulated as text)
        ax3 = fig.add_subplot(gs[2])
        ax3.axis('off')
        
        wpm = self.feats['articulation_rate']
        pause_rate = self.feats['pause_rate']
        mean_pause = self.feats['pause_duration_mean']
        
        text = f"SPEECH METRICS\n\n"
        text += f"Articulation Rate:\n{wpm:.1f} wpm\n"
        text += f"Target: >100\n\n"
        text += f"Pause Rate:\n{pause_rate:.1f} /min\n"
        text += f"Target: <5\n\n"
        text += f"Mean Pause:\n{mean_pause:.2f} s"
        
        ax3.text(0.1, 0.5, text, transform=ax3.transAxes, fontsize=12, va='center')
        
        self.save_fig(fig, "3_speech_pause")

    def graph4_voice_quality(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))
        
        # Subplot 1: Jitter/Shimmer bars
        jitter = self.feats['jitter']
        shimmer = self.feats['shimmer']
        
        bars = ax1.bar(['Jitter (%)', 'Shimmer (%)'], [jitter, shimmer], 
                 color=[COLORS['primary'], COLORS['secondary']], alpha=0.7)
        
        # Threshold lines
        ax1.axhline(CONFIG['thresholds']['jitter'], color=COLORS['danger'], linestyle='--', xmin=0, xmax=0.5)
        ax1.text(0, CONFIG['thresholds']['jitter'], ' Threshold 1.0%', color=COLORS['danger'], va='bottom')
        
        ax1.axhline(CONFIG['thresholds']['shimmer'], color=COLORS['danger'], linestyle='--', xmin=0.5, xmax=1)
        ax1.text(1, CONFIG['thresholds']['shimmer'], ' Threshold 3.0%', color=COLORS['danger'], va='bottom')
        
        # Add values on top
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.2f}%", ha='center', va='bottom', fontweight='bold')
            
        ax1.set_title('Voice Quality Perturbations', fontweight='bold')
        ax1.set_ylim(0, max(shimmer, 4) * 1.2)
        
        # Subplot 2: Energy Contour
        # Calculate RMS from audio signal directly
        rms = librosa.feature.rms(y=self.analyzer.y)[0]
        # Times need to be calculated based on the hop length (default 512)
        times = librosa.times_like(rms, sr=self.analyzer.sr)
        
        ax2.plot(times, rms, color=COLORS['success'], label='Energy (RMS)')
        ax2.fill_between(times, 0, rms, color=COLORS['success'], alpha=0.3)
        ax2.axhline(CONFIG['thresholds']['low_energy'], color=COLORS['danger'], linestyle='--')
        
        ax2.set_title('Energy Contour')
        ax2.set_xlabel('Time (s)')
        ax2.legend()
        
        self.save_fig(fig, "4_voice_quality")

    def graph5_mfcc_heatmap(self):
        fig, ax = plt.subplots(figsize=(14, 6))
        
        mfccs = self.feats['mfcc']
        img = librosa.display.specshow(mfccs, x_axis='time', sr=self.analyzer.sr, ax=ax, cmap='magma')
        fig.colorbar(img, ax=ax)
        
        ax.set_title(f"MFCC Heatmap (13 Coefficients) - {self.analyzer.patient_id}", fontweight='bold')
        ax.set_ylabel('MFCC Coefficient')
        
        self.save_fig(fig, "5_mfcc_heatmap")

    def graph6_summary_radar(self):
        # Normalize metrics for radar chart (0-1 scale approx)
        # We define rough max values for normalization
        metrics = {
            'Pitch Instability': min(self.feats['f0_std'] / 50, 1),
            'Jitter': min(self.feats['jitter'] / 2, 1),
            'Shimmer': min(self.feats['shimmer'] / 6, 1),
            'Pause Rate': min(self.feats['pause_rate'] / 10, 1),
            'Speech Slowness': min((200 - self.feats['articulation_rate']) / 150, 1) if self.feats['articulation_rate'] < 200 else 0,
            'Low HNR': min((20 - self.feats['hnr']) / 20, 1) if self.feats['hnr'] < 20 else 0,
            'Low Energy': min((0.05 - self.feats['energy_mean']) / 0.05, 1) if self.feats['energy_mean'] < 0.05 else 0
        }
        
        # Clean up negative values
        metrics = {k: max(0, v) for k, v in metrics.items()}
        
        labels = list(metrics.keys())
        stats = list(metrics.values())
        
        # Close the loop
        stats += stats[:1]
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(angles, stats, color=COLORS['warning'], alpha=0.4)
        ax.plot(angles, stats, color=COLORS['warning'], linewidth=2)
        
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        risk_level = "High" if len(self.analyzer.indicators) >= 5 else "Moderate" if len(self.analyzer.indicators) >= 3 else "Low"
        color = COLORS['danger'] if risk_level == "High" else COLORS['warning'] if risk_level == "Moderate" else COLORS['success']
        
        ax.set_title(f"Risk Assessment: {risk_level} ({len(self.analyzer.indicators)} indicators)", 
                    fontweight='bold', color=color, pad=20)
        
        self.save_fig(fig, "6_summary_radar")

    def create_all_graphs(self):
        print(f"  Creating graphs for {self.pid}...")
        self.graph1_waveform_spectrogram()
        self.graph2_pitch_analysis()
        self.graph3_speech_rate_pause()
        self.graph4_voice_quality()
        self.graph5_mfcc_heatmap()
        self.graph6_summary_radar()

# ============================================================
# 4. REPORT GENERATION
# ============================================================

def generate_summary_report(results):
    path = os.path.join(CONFIG['output_dir'], 'reports', 'summary_report.txt')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("MCI/AD PATIENT AUDIO ANALYSIS - SUMMARY REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("OVERALL SUMMARY\n")
        f.write("-" * 80 + "\n")
        
        # Sort by risk (indicators count)
        sorted_results = sorted(results, key=lambda x: len(x['indicators']), reverse=True)
        
        for res in sorted_results:
            n_inds = len(res['indicators'])
            risk = "High" if n_inds >= 5 else "Moderate" if n_inds >= 3 else "Low"
            f.write(f"{res['id']} (Age: {res['meta']['age']}, Gender: {res['meta']['gender']}, Label: {res['meta']['label']}): {risk} Risk ({n_inds}/7 indicators)\n")
            
        f.write("\n")
        
        for res in results:
            f.write("=" * 80 + "\n")
            f.write(f"{res['id'].upper()}\n")
            f.write("=" * 80 + "\n")
            f.write("Metadata:\n")
            f.write(f"  Age: {res['meta']['age']}\n")
            f.write(f"  Gender: {res['meta']['gender']}\n")
            f.write(f"  Clinical Label: {res['meta']['label']}\n\n")
            
            f.write("BASIC METRICS:\n")
            f.write(f"  Audio Duration: {res['feats']['duration']:.2f} s\n")
            f.write(f"  Speaking Time Ratio: {res['feats']['speech_ratio']*100:.1f}%\n")
            f.write(f"  Total Pause Time: {(res['feats']['duration'] - res['feats']['speech_duration']):.2f} s\n\n")
            
            f.write("ACOUSTIC FEATURES:\n")
            f.write(f"  F0 Mean: {res['feats']['f0_mean']:.1f} Hz\n")
            f.write(f"  F0 Std: {res['feats']['f0_std']:.1f} Hz\n")
            f.write(f"  Speech Rate: {res['feats']['articulation_rate']:.1f} wpm\n")
            f.write(f"  Jitter: {res['feats']['jitter']:.2f}%\n")
            f.write(f"  Shimmer: {res['feats']['shimmer']:.2f}%\n")
            f.write(f"  Energy Mean: {res['feats']['energy_mean']:.4f}\n\n")
            
            f.write("MCI/AD INDICATORS DETECTED:\n")
            if res['indicators']:
                for ind in res['indicators']:
                    f.write(f"  [X] {ind}\n")
            else:
                f.write("  None detected\n")
                
            n_inds = len(res['indicators'])
            risk = "High" if n_inds >= 5 else "Moderate" if n_inds >= 3 else "Low"
            f.write(f"\n  RISK LEVEL: {risk.upper()} ({n_inds} indicators)\n\n")

    print(f"Summary report generated at: {path}")

# ============================================================
# 5. MAIN PIPELINE
# ============================================================

def main():
    print("Starting Voice Analysis Pipeline...")
    print("=" * 80)
    
    # Check if labels file exists
    if not os.path.exists(CONFIG['labels_file']):
        print(f"Labels file not found: {CONFIG['labels_file']}")
        return

    labels_df = pd.read_csv(CONFIG['labels_file'])
    print(f"Found {len(labels_df)} entries in labels file.")
    
    all_results = []
    
    for idx, row in labels_df.iterrows():
        patient_id = f"Patient {idx+1}"
        print(f"\nProcessing {patient_id} ({row['filename']})...")
        
        audio_path = os.path.join(CONFIG['audio_dir'], row['filename'])
        if not os.path.exists(audio_path):
            print(f"  Audio file not found: {audio_path}")
            continue
            
        metadata = {
            'age': row['age'],
            'gender': row['gender'],
            'label': row['label']
        }
        
        try:
            # Analyze
            analyzer = DetailedAudioAnalyzer(audio_path, patient_id, metadata)
            features, indicators = analyzer.extract_all_features()
            
            # Visualize
            visualizer = DetailedVisualizer(analyzer, CONFIG['output_dir'])
            visualizer.create_all_graphs()
            
            all_results.append({
                'id': patient_id,
                'meta': metadata,
                'feats': features,
                'indicators': indicators
            })
            
            print(f"  Completed {patient_id}")
            
        except Exception as e:
            print(f"  Error processing {patient_id}: {e}")
            import traceback
            traceback.print_exc()
            
    # Generate Report
    if all_results:
        print("\nGenerating summary report...")
        generate_summary_report(all_results)
        
        print("\nGenerating detailed interpretation reports...")
        for res in all_results:
            report_path = generate_detailed_interpretation(
                patient_id=res['id'],
                features=res['feats'],
                indicators=res['indicators'],
                metadata=res['meta'],
                all_patients_data=all_results
            )
            print(f"  Generated: {report_path}")
            
        print("Analysis complete!")
    else:
        print("No patients processed successfully.")

# ============================================================
# 6. DETAILED INTERPRETATION GENERATOR
# ============================================================

def generate_detailed_interpretation(patient_id, features, indicators, metadata, all_patients_data):
    """Generate detailed interpretation report for each patient"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    n_indicators = len(indicators)
    risk_level = "HIGH" if n_indicators >= 5 else "MODERATE" if n_indicators >= 3 else "LOW"
    
    lines = []
    
    # 1. Header & Executive Summary
    lines.append(f"# 📊 BÁO CÁO PHÂN TÍCH GIỌNG NÓI CHI TIẾT\n")
    lines.append(f"**Patient ID**: {patient_id}")
    lines.append(f"**Metadata**: Age {metadata['age']}, Gender {metadata['gender']}, Clinical Label: {metadata['label']}")
    lines.append(f"**Ngày phân tích**: {timestamp}")
    lines.append(f"**Risk Assessment**: {risk_level} ({n_indicators}/7 indicators detected)\n")
    lines.append("---\n")
    
    lines.append("## 🎯 EXECUTIVE SUMMARY\n")
    lines.append("### Kết luận chính:")
    if risk_level == "HIGH":
        lines.append(f"Bệnh nhân {patient_id} thể hiện các dấu hiệu nghiêm trọng của suy giảm nhận thức thông qua giọng nói. Các chỉ số về độ ổn định cao độ, nhịp điệu và chất lượng giọng đều ở mức bất thường cao ({n_indicators}/7 chỉ báo).")
    elif risk_level == "MODERATE":
        lines.append(f"Bệnh nhân {patient_id} có các dấu hiệu cảnh báo trung bình. Mặc dù một số chỉ số vẫn trong giới hạn, sự xuất hiện của {n_indicators} chỉ báo bất thường gợi ý cần theo dõi thêm.")
    else:
        lines.append(f"Bệnh nhân {patient_id} có hồ sơ giọng nói tương đối bình thường. Các chỉ số chính nằm trong giới hạn cho phép, rủi ro thấp.")
        
    lines.append("\n### Các phát hiện quan trọng:")
    # Simple logic to pick top findings
    if features['f0_std'] > CONFIG['thresholds']['pitch_instability']:
        lines.append(f"- ⚠️ Pitch Instability cao ({features['f0_std']:.1f} Hz)")
    else:
        lines.append("- ✅ Pitch ổn định")
        
    if features['articulation_rate'] < CONFIG['thresholds']['slow_speech']:
        lines.append(f"- ⚠️ Tốc độ nói chậm ({features['articulation_rate']:.1f} wpm)")
    else:
        lines.append(f"- ✅ Tốc độ nói bình thường ({features['articulation_rate']:.1f} wpm)")
        
    if features['jitter'] > CONFIG['thresholds']['jitter']:
        lines.append(f"- ⚠️ Jitter bất thường ({features['jitter']:.2f}%)")
    
    lines.append(f"\n### Mức độ rủi ro: {risk_level}")
    lines.append("\n### Khuyến nghị:")
    if risk_level == "HIGH":
        lines.append("- Khám chuyên khoa thần kinh để đánh giá chi tiết.")
        lines.append("- Thực hiện các bài kiểm tra nhận thức bổ sung (MMSE, MoCA).")
    elif risk_level == "MODERATE":
        lines.append("- Theo dõi sự thay đổi giọng nói trong 3 tháng tới.")
        lines.append("- Đánh giá lại các yếu tố gây stress hoặc mệt mỏi.")
    else:
        lines.append("- Duy trì lối sống lành mạnh và kiểm tra định kỳ.")
        
    lines.append("\n---\n")
    
    # 2. Detailed Graph Analysis
    lines.extend(interpret_graph1_waveform(features))
    lines.extend(interpret_graph2_pitch(features))
    lines.extend(interpret_graph3_speech_pause(features))
    lines.extend(interpret_graph4_voice_quality(features))
    lines.extend(interpret_graph5_mfcc(features))
    lines.extend(interpret_graph6_radar(features, indicators))
    
    # 3. Indicators Analysis
    lines.append("\n## 🔬 PHÂN TÍCH 7 CHỈ BÁO MCI/AD\n")
    lines.append(f"### Indicators Detected: {n_indicators}/7\n")
    if indicators:
        for ind in indicators:
            lines.append(f"#### ⚠️ {ind}")
            lines.append("Ý nghĩa: Chỉ báo này thường liên quan đến sự suy giảm kiểm soát vận động thần kinh hoặc khó khăn trong xử lý ngôn ngữ.\n")
    else:
        lines.append("✅ Không phát hiện chỉ báo bất thường nào.\n")
        
    # 4. Comparative Analysis
    lines.extend(compare_with_others(patient_id, features, indicators, all_patients_data))
    
    # 5. Clinical Indications
    lines.append("\n## 🏥 Ý NGHĨA LÂM SÀNG & KHUYẾN NGHỊ\n")
    lines.append("### Biểu hiện có thể quan sát:")
    if "Slow Speech" in str(indicators):
        lines.append("- Người bệnh có thể nói ngập ngừng, mất nhiều thời gian để tìm từ.")
    if "Pitch Instability" in str(indicators):
        lines.append("- Giọng nói có thể nghe run rẩy hoặc thay đổi tông giọng bất thường.")
    if "High Pause Frequency" in str(indicators):
        lines.append("- Thường xuyên ngắt quãng giữa chừng khi đang nói.")
        
    lines.append("\n### Disclaimer")
    lines.append("⚠️ Kết quả này chỉ mang tính chất sàng lọc và tham khảo, không thay thế chẩn đoán y khoa chính thức.")
    
    # Save
    filename = f"detailed_interpretation_{patient_id.replace(' ', '_')}.md"
    output_path = os.path.join(CONFIG['output_dir'], 'reports', filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    return output_path

def interpret_graph1_waveform(features):
    lines = []
    lines.append("## 📈 PHÂN TÍCH CHI TIẾT TỪNG BIỂU ĐỒ\n")
    lines.append("### Graph 1: Waveform & Mel Spectrogram\n")
    lines.append("#### 🔍 Quan sát:")
    lines.append(f"**Waveform**: Thời lượng {features['duration']:.2f}s. Tỷ lệ tiếng nói {features['speech_ratio']*100:.1f}%.")
    lines.append(f"**Mel Spectrogram**: Phân bố năng lượng {'tập trung' if features['energy_mean'] > 0.05 else 'thấp/phân tán'}.")
    lines.append("\n#### 💡 Ý nghĩa lâm sàng:")
    lines.append("Biểu đồ này cho thấy cấu trúc tổng thể của tín hiệu. Khoảng lặng kéo dài hoặc năng lượng thấp có thể chỉ ra sự mệt mỏi hoặc suy giảm khả năng phát âm.")
    lines.append("\n---\n")
    return lines

def interpret_graph2_pitch(features):
    lines = []
    lines.append("### Graph 2: Pitch Analysis\n")
    lines.append("#### 🔍 Quan sát:")
    lines.append(f"**F0 Contour**: Mean {features['f0_mean']:.1f}Hz, Std {features['f0_std']:.1f}Hz.")
    lines.append(f"**Pitch Instability**: {'⚠️ CAO' if features['f0_std'] > 30 else '✅ BÌNH THƯỜNG'}.")
    lines.append("\n#### 💡 Ý nghĩa lâm sàng:")
    lines.append("Độ ổn định của cao độ (Pitch Check) phản ánh khả năng kiểm soát cơ thanh quản. Sự bất ổn định cao thường gặp ở bệnh nhân thoái hóa thần kinh.")
    lines.append("\n---\n")
    return lines

def interpret_graph3_speech_pause(features):
    lines = []
    lines.append("### Graph 3: Speech Rate & Pause Patterns\n")
    lines.append("#### 🔍 Quan sát:")
    lines.append(f"**Speech Rate**: {features['articulation_rate']:.1f} từ/phút (Mục tiêu >100).")
    lines.append(f"**Pauses**: {features['n_pauses']} lần ngắt quãng. Tần suất {features['pause_rate']:.1f}/phút.")
    lines.append("\n#### 💡 Ý nghĩa lâm sàng:")
    lines.append("Tốc độ nói chậm và ngắt quãng thường xuyên là dấu hiệu của khó khăn trong việc tìm từ (word-finding difficulty) hoặc suy giảm tốc độ xử lý thông tin.")
    lines.append("\n---\n")
    return lines

def interpret_graph4_voice_quality(features):
    lines = []
    lines.append("### Graph 4: Voice Quality Indicators\n")
    lines.append("#### 🔍 Quan sát:")
    lines.append(f"**Jitter**: {features['jitter']:.2f}% (Bình thường <1%).")
    lines.append(f"**Shimmer**: {features['shimmer']:.2f}% (Bình thường <3%).")
    lines.append("\n#### 💡 Ý nghĩa lâm sàng:")
    lines.append("Jitter và Shimmer đo lường độ nhiễu và sự không đều của giọng nói. Giá trị cao cho thấy giọng nói 'thô', 'run', thường gặp trong lão hóa hoặc bệnh lý thần kinh.")
    lines.append("\n---\n")
    return lines

def interpret_graph5_mfcc(features):
    lines = []
    lines.append("### Graph 5: MFCC Heatmap\n")
    lines.append("#### 🔍 Quan sát:")
    lines.append(f"**Variability**: {features['mfcc_variability']:.1f} (Ngưỡng <35).")
    lines.append("\n#### 💡 Ý nghĩa lâm sàng:")
    lines.append("MFCC phản ánh đặc trưng quang phổ của giọng nói. Sự biến thiên quá mức hoặc bất thường trong heatmap có thể chỉ ra sự mất kiểm soát trong việc định hình âm thanh.")
    lines.append("\n---\n")
    return lines

def interpret_graph6_radar(features, indicators):
    lines = []
    lines.append("### Graph 6: Summary Radar Chart\n")
    lines.append(f"#### 🔍 Tổng quan:")
    lines.append(f"Biểu đồ radar tổng hợp 7 khía cạnh rủi ro. Bệnh nhân có {len(indicators)}/7 khía cạnh vượt ngưỡng cảnh báo.")
    lines.append("\n---\n")
    return lines

def compare_with_others(patient_id, features, indicators, all_patients_data):
    lines = []
    lines.append("\n## 📊 SO SÁNH VỚI CÁC BỆNH NHÂN KHÁC\n")
    
    # Calculate ranks
    sorted_patients = sorted(all_patients_data, key=lambda x: len(x['indicators']), reverse=True)
    rank = next((i for i, p in enumerate(sorted_patients) if p['id'] == patient_id), -1) + 1
    
    lines.append(f"### Ranking Risk:")
    lines.append(f"Bệnh nhân đứng thứ **{rank}/{len(all_patients_data)}** về mức độ rủi ro trong nhóm phân tích.")
    
    # Compare with averages
    avg_f0_std = np.mean([p['feats']['f0_std'] for p in all_patients_data])
    avg_speech_rate = np.mean([p['feats']['articulation_rate'] for p in all_patients_data])
    
    lines.append("\n### So sánh Key Metrics (vs Trung bình nhóm):")
    lines.append(f"| Metric | Patient | Group Mean | Status |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| F0 Std | {features['f0_std']:.1f} | {avg_f0_std:.1f} | {'Cao hơn' if features['f0_std'] > avg_f0_std else 'Thấp hơn'} |")
    lines.append(f"| Speech Rate | {features['articulation_rate']:.1f} | {avg_speech_rate:.1f} | {'Nhanh hơn' if features['articulation_rate'] > avg_speech_rate else 'Chậm hơn'} |")
    
    return lines


if __name__ == '__main__':
    main()
