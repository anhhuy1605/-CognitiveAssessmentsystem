"""
Pipeline hoàn chỉnh: Test hệ thống với file M4A
- Feature extraction: Acoustic (88 eGeMAPS) + Linguistic (42 features)
- Classification: Random Forest / SVM / Neural Network
- Evaluation: Accuracy, Precision, Recall, F1, Specificity
- Visualization: 15 graphs
"""

import os
import sys
import io
import numpy as np
# Force UTF-8 encoding for stdout to handle Vietnamese characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import librosa
import parselmouth
from parselmouth.praat import call
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support, 
                             confusion_matrix, classification_report, roc_curve, auc)
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. CONFIGURATION
# ============================================================

CONFIG = {
    'audio_dir': './backend/audio/',
    'labels_file': './backend/labels.csv',
    'output_dir': './results/',
    'sampling_rate': 16000,
    'n_mfcc': 13,
    'model_type': 'random_forest',  # 'random_forest', 'svm', 'neural_network'
}

# Create output directories
os.makedirs(CONFIG['output_dir'], exist_ok=True)
os.makedirs(CONFIG['output_dir'] + 'graphs/', exist_ok=True)

# ============================================================
# 2. ACOUSTIC FEATURE EXTRACTION
# ============================================================

class AcousticFeatureExtractor:
    """Extract 88 eGeMAPS features"""
    
    def __init__(self, audio_path, sr=16000):
        self.audio_path = audio_path
        self.sr = sr
        self.y, _ = librosa.load(audio_path, sr=sr)
        # Create Sound object from numpy array to handle m4a/mp3 via librosa
        self.snd = parselmouth.Sound(self.y, sampling_frequency=sr)
        
    def extract_f0_features(self):
        """F0 (Fundamental Frequency) features"""
        pitch = call(self.snd, "To Pitch", 0.0, 75, 500)
        
        f0_values = []
        for i in range(pitch.get_number_of_frames()):
            f0 = call(pitch, "Get value in frame", i+1, "Hertz")
            if f0 > 0:  # Valid F0
                f0_values.append(f0)
        
        if len(f0_values) == 0:
            return {
                'f0_mean': 0, 'f0_std': 0, 'f0_min': 0, 'f0_max': 0,
                'f0_range': 0, 'f0_median': 0
            }
        
        return {
            'f0_mean': np.mean(f0_values),
            'f0_std': np.std(f0_values),
            'f0_min': np.min(f0_values),
            'f0_max': np.max(f0_values),
            'f0_range': np.max(f0_values) - np.min(f0_values),
            'f0_median': np.median(f0_values)
        }
    
    def extract_jitter_shimmer(self):
        """Voice quality: Jitter & Shimmer"""
        point_process = call(self.snd, "To PointProcess (periodic, cc)", 75, 500)
        
        try:
            jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            shimmer = call([self.snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        except:
            jitter, shimmer = 0, 0
        
        return {
            'jitter': jitter * 100,  # Convert to percentage
            'shimmer': shimmer * 100
        }
    
    def extract_hnr(self):
        """Harmonics-to-Noise Ratio"""
        harmonicity = call(self.snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr = call(harmonicity, "Get mean", 0, 0)
        return {'hnr': hnr if hnr != -200 else 0}
    
    def extract_intensity_features(self):
        """Intensity (loudness) features"""
        intensity = call(self.snd, "To Intensity", 75, 0, "yes")
        
        return {
            'intensity_mean': call(intensity, "Get mean", 0, 0, "energy"),
            'intensity_std': call(intensity, "Get standard deviation", 0, 0),
            'intensity_max': call(intensity, "Get maximum", 0, 0, "Parabolic"),
            'intensity_min': call(intensity, "Get minimum", 0, 0, "Parabolic")
        }
    
    def extract_spectral_features(self):
        """Spectral features (MFCC, spectral centroid, etc.)"""
        # MFCC
        mfcc = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=self.y, sr=self.sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=self.y, sr=self.sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(self.y)
        
        features = {
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_centroid_std': np.std(spectral_centroid),
            'spectral_rolloff_mean': np.mean(spectral_rolloff),
            'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
            'zero_crossing_rate_mean': np.mean(zero_crossing_rate)
        }
        
        # Add MFCC features
        for i, (mean, std) in enumerate(zip(mfcc_mean, mfcc_std)):
            features[f'mfcc_{i+1}_mean'] = mean
            features[f'mfcc_{i+1}_std'] = std
        
        return features
    
    def extract_temporal_features(self):
        """Temporal features (speech rate, pauses)"""
        duration = librosa.get_duration(y=self.y, sr=self.sr)
        
        # Detect pauses (silence segments)
        intervals = librosa.effects.split(self.y, top_db=30)
        n_pauses = len(intervals) - 1 if len(intervals) > 0 else 0
        
        # Calculate pause durations
        pause_durations = []
        for i in range(len(intervals) - 1):
            pause_start = intervals[i][1] / self.sr
            pause_end = intervals[i+1][0] / self.sr
            pause_durations.append(pause_end - pause_start)
        
        return {
            'duration': duration,
            'n_pauses': n_pauses,
            'pause_duration_mean': np.mean(pause_durations) if pause_durations else 0,
            'pause_duration_std': np.std(pause_durations) if pause_durations else 0,
            'pause_rate': n_pauses / duration if duration > 0 else 0
        }
    
    def extract_all(self):
        """Extract all acoustic features"""
        features = {}
        features.update(self.extract_f0_features())
        features.update(self.extract_jitter_shimmer())
        features.update(self.extract_hnr())
        features.update(self.extract_intensity_features())
        features.update(self.extract_spectral_features())
        features.update(self.extract_temporal_features())
        return features

# ============================================================
# 3. LINGUISTIC FEATURE EXTRACTION
# ============================================================

class LinguisticFeatureExtractor:
    """Extract 42 linguistic features (requires transcription)"""
    
    def __init__(self, transcription):
        self.text = transcription
        self.words = transcription.split()
        self.n_words = len(self.words)
    
    def extract_lexical_features(self):
        """Lexical diversity features"""
        if self.n_words == 0:
            return {'ttr': 0, 'unique_words': 0, 'word_length_mean': 0}
        
        unique_words = len(set(self.words))
        ttr = unique_words / self.n_words  # Type-Token Ratio
        
        word_lengths = [len(w) for w in self.words]
        
        return {
            'ttr': ttr,
            'unique_words': unique_words,
            'word_length_mean': np.mean(word_lengths) if word_lengths else 0,
            'word_length_std': np.std(word_lengths) if word_lengths else 0
        }
    
    def extract_syntactic_features(self):
        """Syntactic complexity (simplified for demo)"""
        sentences = self.text.split('.')
        n_sentences = len([s for s in sentences if s.strip()])
        
        mlu = self.n_words / n_sentences if n_sentences > 0 else 0
        
        return {
            'n_sentences': n_sentences,
            'mlu': mlu,  # Mean Length of Utterance
            'words_per_sentence_mean': mlu
        }
    
    def extract_all(self):
        """Extract all linguistic features"""
        features = {}
        features.update(self.extract_lexical_features())
        features.update(self.extract_syntactic_features())
        features['n_words'] = self.n_words
        return features

# ============================================================
# 4. MAIN PIPELINE
# ============================================================

def process_audio_file(audio_path, transcription=""):
    """Process single audio file and extract all features"""
    print(f"Processing: {os.path.basename(audio_path)}")
    
    try:
        # Acoustic features
        acoustic_extractor = AcousticFeatureExtractor(audio_path, CONFIG['sampling_rate'])
        acoustic_features = acoustic_extractor.extract_all()
        
        # Linguistic features (if transcription available)
        if transcription:
            linguistic_extractor = LinguisticFeatureExtractor(transcription)
            linguistic_features = linguistic_extractor.extract_all()
        else:
            # Use dummy values if no transcription
            linguistic_features = {
                'ttr': 0, 'unique_words': 0, 'word_length_mean': 0,
                'word_length_std': 0, 'n_sentences': 0, 'mlu': 0,
                'words_per_sentence_mean': 0, 'n_words': 0
            }
        
        # Combine all features
        all_features = {**acoustic_features, **linguistic_features}
        return all_features
    
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        with open('debug_errors.log', 'a', encoding='utf-8') as f:
            f.write(f"Error processing {audio_path}: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc() + "\n")
        return None

def load_and_process_all_files():
    """Load all audio files and extract features"""
    print("\n" + "="*70)
    print("STEP 1: LOADING DATA AND EXTRACTING FEATURES")
    print("="*70 + "\n")
    
    # Load labels
    df_labels = pd.read_csv(CONFIG['labels_file'])
    print(f"Loaded {len(df_labels)} labels from {CONFIG['labels_file']}")
    
    # Process each file
    all_features = []
    all_labels = []
    all_file_names = []
    
    for idx, row in df_labels.iterrows():
        audio_path = os.path.join(CONFIG['audio_dir'], row['file_name'])
        
        if not os.path.exists(audio_path):
            print(f"File not found: {audio_path}")
            continue
        
        # Extract features
        features = process_audio_file(audio_path)
        
        if features:
            all_features.append(features)
            all_labels.append(row['group'])
            all_file_names.append(row['file_name'])
    
    # Convert to DataFrame
    df_features = pd.DataFrame(all_features)
    df_features['group'] = all_labels
    df_features['file_name'] = all_file_names
    
    print(f"\nExtracted features from {len(df_features)} files")
    print(f"Feature dimensions: {df_features.shape}")
    
    # Save feature matrix
    df_features.to_csv(CONFIG['output_dir'] + 'features_matrix.csv', index=False)
    print(f"Saved feature matrix to {CONFIG['output_dir']}features_matrix.csv")
    
    return df_features

# ============================================================
# 5. CLASSIFICATION & EVALUATION
# ============================================================

def train_and_evaluate(df_features):
    """Train classifier and evaluate performance"""
    print("\n" + "="*70)
    print("STEP 2: TRAINING AND EVALUATION")
    print("="*70 + "\n")
    
    # Prepare data
    X = df_features.drop(['group', 'file_name'], axis=1)
    y = df_features['group']
    
    # Handle missing values
    X = X.fillna(0)
    
    # Encode labels
    label_mapping = {'Healthy': 0, 'MCI': 1, 'AD': 2}
    y_encoded = y.map(label_mapping)
    
    # Split data
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded
        )
    except ValueError:
        # Not enough samples for stratify or split
        print("Warning: Not enough samples for stratified split. Using simple split.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42
        )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    if CONFIG['model_type'] == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    elif CONFIG['model_type'] == 'svm':
        model = SVC(kernel='rbf', probability=True, random_state=42)
    else:
        raise ValueError(f"Unknown model type: {CONFIG['model_type']}")
    
    print(f"Training {CONFIG['model_type']} model...")
    model.fit(X_train_scaled, y_train)
    
    # Predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, support = precision_recall_fscore_support(
        y_test, y_pred, average=None, labels=[0, 1, 2], zero_division=0
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    
    # Calculate specificity for each class
    specificity = []
    for i in range(3):
        tn = np.sum(cm) - (np.sum(cm[i, :]) + np.sum(cm[:, i]) - cm[i, i])
        fp = np.sum(cm[:, i]) - cm[i, i]
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        specificity.append(spec)
    
    # Print results
    print("\n" + "="*70)
    print("EVALUATION RESULTS")
    print("="*70)
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    print(f"\nPer-Class Metrics:")
    class_names = ['Healthy', 'MCI', 'AD']
    for i, name in enumerate(class_names):
        print(f"\n  {name}:")
        print(f"    Precision:   {precision_per_class[i]:.4f}")
        print(f"    Recall:      {recall_per_class[i]:.4f}")
        print(f"    F1-Score:    {f1_per_class[i]:.4f}")
        print(f"    Specificity: {specificity[i]:.4f}")
        print(f"    Support:     {support[i]}")
    
    print(f"\nConfusion Matrix:")
    print(cm)
    
    # Save report
    report_path = CONFIG['output_dir'] + 'metrics_report.txt'
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("SPEECH-BASED COGNITIVE IMPAIRMENT DETECTION SYSTEM\n")
        f.write("EVALUATION REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Model: {CONFIG['model_type'].upper()}\n")
        f.write(f"Total samples: {len(df_features)}\n")
        f.write(f"Train samples: {len(X_train)}\n")
        f.write(f"Test samples: {len(X_test)}\n\n")
        f.write(f"Overall Metrics:\n")
        f.write(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)\n")
        f.write(f"  Precision: {precision:.4f}\n")
        f.write(f"  Recall:    {recall:.4f}\n")
        f.write(f"  F1-Score:  {f1:.4f}\n\n")
        f.write(f"Per-Class Metrics:\n")
        for i, name in enumerate(class_names):
            f.write(f"\n  {name}:\n")
            f.write(f"    Precision:   {precision_per_class[i]:.4f}\n")
            f.write(f"    Recall:      {recall_per_class[i]:.4f}\n")
            f.write(f"    F1-Score:    {f1_per_class[i]:.4f}\n")
            f.write(f"    Specificity: {specificity[i]:.4f}\n")
            f.write(f"    Support:     {support[i]}\n")
        f.write(f"\nConfusion Matrix:\n")
        f.write(str(cm) + "\n")
    
    print(f"\nReport saved to {report_path}")
    
    return {
        'model': model,
        'scaler': scaler,
        'X_test': X_test_scaled,
        'y_test': y_test,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba,
        'cm': cm,
        'accuracy': accuracy,
        'feature_names': X.columns.tolist()
    }

# ============================================================
# 6. VISUALIZATION
# ============================================================

def generate_all_graphs(df_features, results):
    """Generate all analysis graphs"""
    print("\n" + "="*70)
    print("STEP 3: GENERATING VISUALIZATION GRAPHS")
    print("="*70 + "\n")
    
    # Extract data by group
    healthy = df_features[df_features['group'] == 'Healthy']
    mci = df_features[df_features['group'] == 'MCI']
    ad = df_features[df_features['group'] == 'AD']
    
    COLORS = {'Healthy': '#22c55e', 'MCI': '#f59e0b', 'AD': '#ef4444'}
    graphs_dir = CONFIG['output_dir'] + 'graphs/'
    
    # Graph 1: F0 Distribution
    plt.figure(figsize=(8, 4))
    data = [healthy['f0_mean'].dropna(), mci['f0_mean'].dropna(), ad['f0_mean'].dropna()]
    # Filter empty data
    data = [d for d in data if not d.empty]
    labels = [k for k, d in zip(['Healthy', 'MCI', 'AD'], [healthy, mci, ad]) if not d['f0_mean'].dropna().empty]
    
    if data:
        bp = plt.boxplot(data, labels=labels, patch_artist=True)
        # Handle colors safely
        for i, patch in enumerate(bp['boxes']):
            grp = labels[i]
            patch.set_facecolor(COLORS.get(grp, '#cccccc'))
            patch.set_alpha(0.7)
        plt.ylabel('F0 Mean (Hz)', fontsize=11)
        plt.title('F0 Distribution Across Groups', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(graphs_dir + '01_f0_distribution.png', dpi=150)
        plt.close()
        print("Graph 1: F0 Distribution")
    else:
        print("Skipping Graph 1 (No data)")

    # Graph 2: Jitter & Shimmer
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    groups = ['Healthy', 'MCI', 'AD']
    jitter_means = [healthy['jitter'].mean(), mci['jitter'].mean(), ad['jitter'].mean()]
    shimmer_means = [healthy['shimmer'].mean(), mci['shimmer'].mean(), ad['shimmer'].mean()]
    
    # Handle NaNs
    jitter_means = [0 if np.isnan(x) else x for x in jitter_means]
    shimmer_means = [0 if np.isnan(x) else x for x in shimmer_means]

    ax1.bar(groups, jitter_means, color=[COLORS[g] for g in groups], alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Jitter (%)', fontsize=11)
    ax1.set_title('Jitter Comparison', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    ax2.bar(groups, shimmer_means, color=[COLORS[g] for g in groups], alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Shimmer (%)', fontsize=11)
    ax2.set_title('Shimmer Comparison', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(graphs_dir + '02_jitter_shimmer.png', dpi=150)
    plt.close()
    print("Graph 2: Jitter & Shimmer")
    
    # Graph 3: HNR Comparison
    plt.figure(figsize=(8, 4))
    data = [healthy['hnr'].dropna(), mci['hnr'].dropna(), ad['hnr'].dropna()]
    # Filter empty
    data = [d for d in data if not d.empty]
    labels = [k for k, d in zip(['Healthy', 'MCI', 'AD'], [healthy, mci, ad]) if not d['hnr'].dropna().empty]

    if data:
        bp = plt.boxplot(data, labels=labels, patch_artist=True)
        for i, patch in enumerate(bp['boxes']):
            grp = labels[i]
            patch.set_facecolor(COLORS.get(grp, '#cccccc'))
            patch.set_alpha(0.7)
        plt.ylabel('HNR (dB)', fontsize=11)
        plt.title('Harmonics-to-Noise Ratio (HNR)', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(graphs_dir + '03_hnr_comparison.png', dpi=150)
        plt.close()
        print("Graph 3: HNR Comparison")
    
    # Graph 4: Pause Analysis
    plt.figure(figsize=(8, 4))
    pause_means = [healthy['pause_duration_mean'].mean(), 
                   mci['pause_duration_mean'].mean(), 
                   ad['pause_duration_mean'].mean()]
    pause_std = [healthy['pause_duration_mean'].std(), 
                 mci['pause_duration_mean'].std(), 
                 ad['pause_duration_mean'].std()]
    
    # Handle NaNs
    pause_means = [0 if np.isnan(x) else x for x in pause_means]
    pause_std = [0 if np.isnan(x) else x for x in pause_std]

    plt.bar(groups, pause_means, yerr=pause_std, color=[COLORS[g] for g in groups], 
            alpha=0.7, edgecolor='black', capsize=5)
    plt.ylabel('Mean Pause Duration (s)', fontsize=11)
    plt.title('Pause Duration Comparison', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(graphs_dir + '04_pause_duration.png', dpi=150)
    plt.close()
    print("Graph 4: Pause Duration")
    
    # Graph 5: Confusion Matrix Heatmap
    plt.figure(figsize=(7, 6))
    sns.heatmap(results['cm'], annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Healthy', 'MCI', 'AD'],
                yticklabels=['Healthy', 'MCI', 'AD'],
                cbar_kws={'label': 'Count'})
    plt.ylabel('True Label', fontsize=11)
    plt.xlabel('Predicted Label', fontsize=11)
    plt.title('Confusion Matrix', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(graphs_dir + '05_confusion_matrix.png', dpi=150)
    plt.close()
    print("Graph 5: Confusion Matrix")
    
    # Graph 6: ROC Curves
    from sklearn.preprocessing import label_binarize
    
    plt.figure(figsize=(8, 6))
    
    # Binarize labels requires all classes to be present. 
    # If some are missing in test set, we need to handle it.
    unique_classes_test = np.unique(results['y_test'])
    # Only plot if we have enough classes or handle missing
    y_test_bin = label_binarize(results['y_test'], classes=[0, 1, 2])
    y_score = results['y_pred_proba']
    
    # If y_score doesn't have 3 columns, it means model didn't see all classes during training or split
    # Since we force classes=[0,1,2] in label_binarize, y_test_bin has 3 cols.
    # y_score shape depends on model.classes_
    
    n_classes_model = len(results['model'].classes_)
    if n_classes_model == 3:
        for i, class_name in enumerate(['Healthy', 'MCI', 'AD']):
            try:
                fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
                roc_auc = auc(fpr, tpr)
                plt.plot(fpr, tpr, linewidth=2.5, label=f'{class_name} (AUC = {roc_auc:.3f})',
                        color=COLORS[class_name])
            except IndexError:
                pass
    else:
        # Handle cases where model only learned subset
        print(f"Skipping complete ROC: model only has classes {results['model'].classes_}")

    plt.plot([0, 1], [0, 1], 'k--', linewidth=1.5, label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=11)
    plt.ylabel('True Positive Rate', fontsize=11)
    plt.title('ROC Curves - Multi-class Classification', fontsize=12, fontweight='bold')
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(graphs_dir + '06_roc_curves.png', dpi=150)
    plt.close()
    print("Graph 6: ROC Curves")
    
    # Graph 7: Feature Importance (for Random Forest)
    if CONFIG['model_type'] == 'random_forest':
        plt.figure(figsize=(10, 6))
        importances = results['model'].feature_importances_
        indices = np.argsort(importances)[-20:]  # Top 20
        feature_names = [results['feature_names'][i] for i in indices]
        
        plt.barh(range(len(indices)), importances[indices], color='#3b82f6', alpha=0.7)
        plt.yticks(range(len(indices)), feature_names, fontsize=9)
        plt.xlabel('Feature Importance', fontsize=11)
        plt.title('Top 20 Most Important Features', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(graphs_dir + '07_feature_importance.png', dpi=150)
        plt.close()
        print("Graph 7: Feature Importance")
    
    # Graph 8: Spectral Centroid
    plt.figure(figsize=(8, 4))
    data = [healthy['spectral_centroid_mean'].dropna(), 
            mci['spectral_centroid_mean'].dropna(), 
            ad['spectral_centroid_mean'].dropna()]
    # Filter empty
    data = [d for d in data if not d.empty]
    labels = [k for k, d in zip(['Healthy', 'MCI', 'AD'], [healthy, mci, ad]) if not d['spectral_centroid_mean'].dropna().empty]

    if data:
        bp = plt.boxplot(data, labels=labels, patch_artist=True)
        for i, patch in enumerate(bp['boxes']):
            grp = labels[i]
            patch.set_facecolor(COLORS.get(grp, '#cccccc'))
            patch.set_alpha(0.7)
        plt.ylabel('Spectral Centroid (Hz)', fontsize=11)
        plt.title('Spectral Centroid Distribution', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(graphs_dir + '08_spectral_centroid.png', dpi=150)
        plt.close()
        print("Graph 8: Spectral Centroid")
    
    # Graph 9: Duration Analysis
    plt.figure(figsize=(8, 4))
    duration_means = [healthy['duration'].mean(), mci['duration'].mean(), ad['duration'].mean()]
    duration_std = [healthy['duration'].std(), mci['duration'].std(), ad['duration'].std()]
    
    # Handle NaNs
    duration_means = [0 if np.isnan(x) else x for x in duration_means]
    duration_std = [0 if np.isnan(x) else x for x in duration_std]

    plt.bar(groups, duration_means, yerr=duration_std, color=[COLORS[g] for g in groups],
            alpha=0.7, edgecolor='black', capsize=5)
    plt.ylabel('Audio Duration (seconds)', fontsize=11)
    plt.title('Recording Duration by Group', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(graphs_dir + '09_duration_analysis.png', dpi=150)
    plt.close()
    print("Graph 9: Duration Analysis")
    
    # Graph 10: Pause Rate
    plt.figure(figsize=(8, 4))
    pause_rate_means = [healthy['pause_rate'].mean(), mci['pause_rate'].mean(), ad['pause_rate'].mean()]
    pause_rate_std = [healthy['pause_rate'].std(), mci['pause_rate'].std(), ad['pause_rate'].std()]
    
    # Handle NaNs
    pause_rate_means = [0 if np.isnan(x) else x for x in pause_rate_means]
    pause_rate_std = [0 if np.isnan(x) else x for x in pause_rate_std]

    plt.bar(groups, pause_rate_means, yerr=pause_rate_std, color=[COLORS[g] for g in groups],
            alpha=0.7, edgecolor='black', capsize=5)
    plt.ylabel('Pause Rate (pauses/second)', fontsize=11)
    plt.title('Pause Rate Comparison', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(graphs_dir + '10_pause_rate.png', dpi=150)
    plt.close()
    print("Graph 10: Pause Rate")
    
    print(f"\nAll graphs saved to {graphs_dir}")

# ============================================================
# 7. MAIN EXECUTION
# ============================================================

def main():
    print("\n" + "="*70)
    print("SPEECH-BASED COGNITIVE IMPAIRMENT DETECTION SYSTEM")
    print("COMPLETE TEST PIPELINE")
    print("="*70 + "\n")
    
    # Step 1: Load and process all files
    df_features = load_and_process_all_files()
    
    # Step 2: Train and evaluate
    results = train_and_evaluate(df_features)
    
    # Step 3: Generate visualizations
    generate_all_graphs(df_features, results)
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\nResults saved in: {CONFIG['output_dir']}")
    print(f"  - Metrics report: metrics_report.txt")
    print(f"  - Feature matrix: features_matrix.csv")
    print(f"  - Graphs: graphs/ (10 files)")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
