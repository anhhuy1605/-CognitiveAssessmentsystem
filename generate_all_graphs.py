import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import os

# Set style
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# Colors
COLORS = {
    'healthy': '#22c55e',
    'mci': '#f59e0b',
    'ad': '#ef4444'
}

# Create output directory
os.makedirs('graphs', exist_ok=True)

# ============================================================
# 1. ACOUSTIC FEATURES - LINE GRAPHS
# ============================================================

def graph1_f0_tracking():
    """F0 Tracking Over Time"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    time = np.linspace(0, 10, 100)
    healthy_f0 = 180 + 10 * np.sin(time * 0.5) + np.random.normal(0, 2, 100)
    mci_f0 = 175 + 15 * np.sin(time * 0.5) + np.random.normal(0, 5, 100)
    ad_f0 = 170 + 20 * np.sin(time * 0.5) + np.random.normal(0, 8, 100)
    
    ax.plot(time, healthy_f0, color=COLORS['healthy'], linewidth=2, label='Healthy', alpha=0.8)
    ax.plot(time, mci_f0, color=COLORS['mci'], linewidth=2, label='MCI', alpha=0.8)
    ax.plot(time, ad_f0, color=COLORS['ad'], linewidth=2, label='AD', alpha=0.8)
    
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('F0 (Hz)', fontsize=11)
    ax.set_title('Fundamental Frequency (F0) Tracking', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(0, 10)
    ax.set_ylim(140, 220)
    
    plt.tight_layout()
    plt.savefig('graphs/01_f0_tracking.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 1: F0 Tracking")

def graph2_speech_rate():
    """Speech Rate Across Task Types"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    tasks = ['QA', 'Spontaneous\nSpeech', 'Repetition', 'Naming', 'Open\nQuestions']
    x = np.arange(len(tasks))
    
    healthy_rate = [4.2, 3.8, 4.5, 4.0, 3.5]
    mci_rate = [3.5, 3.0, 3.8, 3.2, 2.8]
    ad_rate = [2.8, 2.3, 3.0, 2.5, 2.0]
    
    ax.plot(x, healthy_rate, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(x, mci_rate, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(x, ad_rate, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Task Type', fontsize=11)
    ax.set_ylabel('Speech Rate (syllables/sec)', fontsize=11)
    ax.set_title('Speech Rate Comparison', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=9)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(1.5, 5.0)
    
    plt.tight_layout()
    plt.savefig('graphs/02_speech_rate.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 2: Speech Rate")

def graph3_pause_duration():
    """Pause Duration Evolution"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    tasks = ['QA', 'Spontaneous\nSpeech', 'Repetition', 'Naming', 'Recall', 'Open\nQuestions']
    x = np.arange(len(tasks))
    
    healthy_pause = [0.3, 0.5, 0.2, 0.4, 0.6, 0.7]
    mci_pause = [0.6, 1.0, 0.5, 0.8, 1.2, 1.4]
    ad_pause = [1.0, 1.6, 0.9, 1.3, 1.8, 2.1]
    
    healthy_std = [0.1, 0.15, 0.08, 0.12, 0.18, 0.2]
    mci_std = [0.15, 0.25, 0.12, 0.2, 0.3, 0.35]
    ad_std = [0.2, 0.35, 0.18, 0.28, 0.4, 0.45]
    
    ax.errorbar(x, healthy_pause, yerr=healthy_std, fmt='o-', color=COLORS['healthy'], 
                linewidth=2.5, markersize=8, capsize=5, capthick=2, label='Healthy', alpha=0.8)
    ax.errorbar(x, mci_pause, yerr=mci_std, fmt='s-', color=COLORS['mci'], 
                linewidth=2.5, markersize=8, capsize=5, capthick=2, label='MCI', alpha=0.8)
    ax.errorbar(x, ad_pause, yerr=ad_std, fmt='^-', color=COLORS['ad'], 
                linewidth=2.5, markersize=8, capsize=5, capthick=2, label='AD', alpha=0.8)
    
    ax.set_xlabel('Task Type', fontsize=11)
    ax.set_ylabel('Mean Pause Duration (seconds)', fontsize=11)
    ax.set_title('Pause Duration Evolution', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=9)
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(0, 2.8)
    
    plt.tight_layout()
    plt.savefig('graphs/03_pause_duration.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 3: Pause Duration")

def graph4_jitter_shimmer():
    """Jitter & Shimmer Progression"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    groups = ['Healthy', 'MCI', 'AD']
    x = np.arange(len(groups))
    
    # Jitter (%)
    jitter = [0.5, 0.9, 1.5]
    jitter_std = [0.1, 0.15, 0.25]
    
    ax1.bar(x, jitter, color=[COLORS['healthy'], COLORS['mci'], COLORS['ad']], 
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.errorbar(x, jitter, yerr=jitter_std, fmt='none', color='black', 
                 capsize=5, capthick=2)
    ax1.set_xlabel('Group', fontsize=11)
    ax1.set_ylabel('Jitter (%)', fontsize=11)
    ax1.set_title('Jitter Comparison', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(groups, fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax1.set_ylim(0, 2.0)
    
    # Shimmer (%)
    shimmer = [2.5, 4.2, 6.8]
    shimmer_std = [0.5, 0.8, 1.2]
    
    ax2.bar(x, shimmer, color=[COLORS['healthy'], COLORS['mci'], COLORS['ad']], 
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.errorbar(x, shimmer, yerr=shimmer_std, fmt='none', color='black', 
                 capsize=5, capthick=2)
    ax2.set_xlabel('Group', fontsize=11)
    ax2.set_ylabel('Shimmer (%)', fontsize=11)
    ax2.set_title('Shimmer Comparison', fontsize=11, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(groups, fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax2.set_ylim(0, 9.0)
    
    plt.tight_layout()
    plt.savefig('graphs/04_jitter_shimmer.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 4: Jitter & Shimmer")

def graph5_spectral_energy():
    """Spectral Energy Distribution"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    freq_bands = ['0-500Hz', '500-1kHz', '1-2kHz', '2-4kHz', '4-8kHz']
    x = np.arange(len(freq_bands))
    
    healthy_energy = [0.35, 0.28, 0.20, 0.12, 0.05]
    mci_energy = [0.32, 0.26, 0.22, 0.14, 0.06]
    ad_energy = [0.30, 0.25, 0.24, 0.15, 0.06]
    
    ax.plot(x, healthy_energy, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(x, mci_energy, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(x, ad_energy, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Frequency Band', fontsize=11)
    ax.set_ylabel('Normalized Energy', fontsize=11)
    ax.set_title('Spectral Energy Distribution', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(freq_bands, fontsize=9)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_ylim(0, 0.40)
    
    plt.tight_layout()
    plt.savefig('graphs/05_spectral_energy.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 5: Spectral Energy")

# ============================================================
# 2. ACOUSTIC FEATURES - BOX PLOTS
# ============================================================

def graph6_f0_boxplot():
    """F0 Statistics Box Plot"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    np.random.seed(42)
    healthy_f0 = np.random.normal(180, 15, 50)
    mci_f0 = np.random.normal(175, 20, 50)
    ad_f0 = np.random.normal(170, 25, 50)
    
    data = [healthy_f0, mci_f0, ad_f0]
    positions = [1, 2, 3]
    
    bp = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True,
                    boxprops=dict(linewidth=1.5),
                    medianprops=dict(color='black', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    
    colors = [COLORS['healthy'], COLORS['mci'], COLORS['ad']]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xlabel('Group', fontsize=11)
    ax.set_ylabel('F0 (Hz)', fontsize=11)
    ax.set_title('F0 Distribution Across Groups', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(positions)
    ax.set_xticklabels(['Healthy', 'MCI', 'AD'], fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(100, 250)
    
    plt.tight_layout()
    plt.savefig('graphs/06_f0_boxplot.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 6: F0 Box Plot")

def graph7_voice_quality():
    """Voice Quality Metrics Box Plot"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    np.random.seed(42)
    # HNR (dB) - Higher is better
    healthy_hnr = np.random.normal(18, 2, 30)
    mci_hnr = np.random.normal(15, 3, 30)
    ad_hnr = np.random.normal(12, 4, 30)
    
    data = [healthy_hnr, mci_hnr, ad_hnr]
    positions = [1, 2, 3]
    
    bp = ax.boxplot(data, positions=positions, widths=0.5, patch_artist=True,
                    boxprops=dict(linewidth=1.5),
                    medianprops=dict(color='black', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    
    colors = [COLORS['healthy'], COLORS['mci'], COLORS['ad']]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xlabel('Group', fontsize=11)
    ax.set_ylabel('HNR (dB)', fontsize=11)
    ax.set_title('Harmonics-to-Noise Ratio (HNR)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(positions)
    ax.set_xticklabels(['Healthy', 'MCI', 'AD'], fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(0, 28)
    
    plt.tight_layout()
    plt.savefig('graphs/07_voice_quality.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 7: Voice Quality")

# ============================================================
# 3. LINGUISTIC FEATURES - LINE GRAPHS
# ============================================================

def graph8_lexical_diversity():
    """Lexical Diversity (TTR/MATTR)"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    segments = np.arange(1, 6)
    
    healthy_ttr = [0.75, 0.72, 0.70, 0.68, 0.67]
    mci_ttr = [0.68, 0.64, 0.60, 0.58, 0.56]
    ad_ttr = [0.60, 0.55, 0.50, 0.48, 0.45]
    
    healthy_mattr = [0.78, 0.77, 0.76, 0.76, 0.75]
    mci_mattr = [0.70, 0.68, 0.67, 0.66, 0.65]
    ad_mattr = [0.62, 0.59, 0.57, 0.56, 0.54]
    
    ax.plot(segments, healthy_ttr, '-', color=COLORS['healthy'], linewidth=2.5, 
            marker='o', markersize=7, label='Healthy (TTR)', alpha=0.8)
    ax.plot(segments, mci_ttr, '-', color=COLORS['mci'], linewidth=2.5, 
            marker='s', markersize=7, label='MCI (TTR)', alpha=0.8)
    ax.plot(segments, ad_ttr, '-', color=COLORS['ad'], linewidth=2.5, 
            marker='^', markersize=7, label='AD (TTR)', alpha=0.8)
    
    ax.plot(segments, healthy_mattr, '--', color=COLORS['healthy'], linewidth=2, 
            marker='o', markersize=6, alpha=0.5)
    ax.plot(segments, mci_mattr, '--', color=COLORS['mci'], linewidth=2, 
            marker='s', markersize=6, alpha=0.5)
    ax.plot(segments, ad_mattr, '--', color=COLORS['ad'], linewidth=2, 
            marker='^', markersize=6, alpha=0.5)
    
    ax.set_xlabel('Utterance Segment (50 tokens each)', fontsize=11)
    ax.set_ylabel('Lexical Diversity Score', fontsize=11)
    ax.set_title('Lexical Diversity: TTR (solid) vs MATTR (dashed)', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.40, 0.85)
    
    plt.tight_layout()
    plt.savefig('graphs/08_lexical_diversity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 8: Lexical Diversity")

def graph9_mlu_progression():
    """MLU Progression"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    tasks = ['QA', 'Spontaneous\nSpeech', 'Naming', 'Recall', 'Open\nQuestions']
    x = np.arange(len(tasks))
    
    healthy_mlu = [8.5, 10.2, 6.8, 7.5, 11.0]
    mci_mlu = [7.0, 8.5, 5.5, 6.0, 9.0]
    ad_mlu = [5.5, 6.8, 4.2, 4.5, 7.0]
    
    ax.plot(x, healthy_mlu, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(x, mci_mlu, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(x, ad_mlu, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Task Type', fontsize=11)
    ax.set_ylabel('MLU (words/utterance)', fontsize=11)
    ax.set_title('Mean Length of Utterance (MLU)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=9)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(3, 13)
    
    plt.tight_layout()
    plt.savefig('graphs/09_mlu_progression.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 9: MLU Progression")

def graph10_information_density():
    """Information Content Density"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    time = np.arange(0, 61, 10)
    
    healthy_density = [0, 12, 24, 35, 45, 54, 62]
    mci_density = [0, 9, 18, 26, 33, 39, 44]
    ad_density = [0, 6, 12, 17, 22, 26, 30]
    
    ax.plot(time, healthy_density, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(time, mci_density, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(time, ad_density, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Information Units', fontsize=11)
    ax.set_title('Information Content Density Over Time', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(-2, 63)
    ax.set_ylim(-2, 70)
    
    plt.tight_layout()
    plt.savefig('graphs/10_information_density.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 10: Information Density")

def graph11_semantic_coherence():
    """Semantic Coherence Score"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    segments = np.arange(1, 9)
    
    healthy_coherence = [0.9, 0.88, 0.87, 0.86, 0.85, 0.85, 0.84, 0.84]
    mci_coherence = [0.85, 0.80, 0.76, 0.73, 0.70, 0.68, 0.66, 0.65]
    ad_coherence = [0.78, 0.70, 0.63, 0.58, 0.54, 0.50, 0.48, 0.45]
    
    ax.plot(segments, healthy_coherence, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(segments, mci_coherence, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(segments, ad_coherence, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Conversation Segment', fontsize=11)
    ax.set_ylabel('Coherence Score', fontsize=11)
    ax.set_title('Semantic Coherence Progression', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(0.5, 8.5)
    ax.set_ylim(0.40, 0.95)
    
    plt.tight_layout()
    plt.savefig('graphs/11_semantic_coherence.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 11: Semantic Coherence")

def graph12_content_word_ratio():
    """Content Word Ratio Evolution"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    tasks = ['QA', 'Spontaneous\nSpeech', 'Naming', 'Recall', 'Open\nQuestions']
    x = np.arange(len(tasks))
    
    healthy_ratio = [0.58, 0.62, 0.65, 0.60, 0.64]
    mci_ratio = [0.52, 0.55, 0.58, 0.53, 0.56]
    ad_ratio = [0.45, 0.48, 0.50, 0.46, 0.49]
    
    ax.plot(x, healthy_ratio, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=8, label='Healthy', alpha=0.8)
    ax.plot(x, mci_ratio, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=8, label='MCI', alpha=0.8)
    ax.plot(x, ad_ratio, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=8, label='AD', alpha=0.8)
    
    ax.set_xlabel('Task Type', fontsize=11)
    ax.set_ylabel('Content Word Ratio', fontsize=11)
    ax.set_title('Content vs Function Words Ratio', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=9)
    ax.legend(loc='lower right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(0.40, 0.70)
    
    plt.tight_layout()
    plt.savefig('graphs/12_content_word_ratio.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 12: Content Word Ratio")

def graph13_feature_correlation():
    """Feature Correlation Heatmap"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    np.random.seed(42)
    features = ['F0 Mean', 'Jitter', 'Shimmer', 'HNR', 'Speech Rate', 
                'Pause Dur.', 'TTR', 'MLU', 'Info Density', 'Coherence']
    n_features = len(features)
    
    # Generate correlation matrix
    corr_matrix = np.random.rand(n_features, n_features)
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix, 1.0)
    corr_matrix = corr_matrix * 2 - 1  # Scale to [-1, 1]
    
    im = ax.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    
    ax.set_xticks(np.arange(n_features))
    ax.set_yticks(np.arange(n_features))
    ax.set_xticklabels(features, fontsize=9, rotation=45, ha='right')
    ax.set_yticklabels(features, fontsize=9)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Correlation', fontsize=10)
    ax.set_title('Feature Correlation Matrix', fontsize=12, fontweight='bold', pad=10)
    
    plt.tight_layout()
    plt.savefig('graphs/13_feature_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 13: Feature Correlation")

# ============================================================
# 4. TASK-SPECIFIC ANALYSIS
# ============================================================

def graph14_utterance_length():
    """Utterance Length Distribution"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    time = np.arange(0, 61, 5)
    
    np.random.seed(42)
    healthy_length = 10 + 2 * np.sin(time/10) + np.random.normal(0, 1, len(time))
    mci_length = 8 + 1.5 * np.sin(time/10) + np.random.normal(0, 1.5, len(time))
    ad_length = 6 + 1 * np.sin(time/10) + np.random.normal(0, 2, len(time))
    
    ax.plot(time, healthy_length, 'o-', color=COLORS['healthy'], linewidth=2.5, 
            markersize=7, label='Healthy', alpha=0.8)
    ax.plot(time, mci_length, 's-', color=COLORS['mci'], linewidth=2.5, 
            markersize=7, label='MCI', alpha=0.8)
    ax.plot(time, ad_length, '^-', color=COLORS['ad'], linewidth=2.5, 
            markersize=7, label='AD', alpha=0.8)
    
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Utterance Length (words)', fontsize=11)
    ax.set_title('Utterance Length Distribution Over Time', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(-2, 62)
    ax.set_ylim(2, 14)
    
    plt.tight_layout()
    plt.savefig('graphs/14_utterance_length.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 14: Utterance Length")

def graph15_pause_frequency():
    """Pause Frequency & Location"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    locations = ['Start\nSentence', 'Mid\nSentence', 'End\nSentence', 'Between\nSentences']
    x = np.arange(len(locations))
    
    healthy_freq = [2, 3, 4, 8]
    mci_freq = [3, 6, 5, 9]
    ad_freq = [4, 10, 6, 10]
    
    width = 0.25
    
    ax.bar(x - width, healthy_freq, width, label='Healthy', color=COLORS['healthy'], 
           alpha=0.7, edgecolor='black', linewidth=1)
    ax.bar(x, mci_freq, width, label='MCI', color=COLORS['mci'], 
           alpha=0.7, edgecolor='black', linewidth=1)
    ax.bar(x + width, ad_freq, width, label='AD', color=COLORS['ad'], 
           alpha=0.7, edgecolor='black', linewidth=1)
    
    ax.set_xlabel('Pause Location', fontsize=11)
    ax.set_ylabel('Pause Frequency (per minute)', fontsize=11)
    ax.set_title('Pause Frequency by Location', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(locations, fontsize=9)
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
    ax.set_ylim(0, 12)
    
    plt.tight_layout()
    plt.savefig('graphs/15_pause_frequency.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Graph 15: Pause Frequency")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("\n" + "="*60)
    print("GENERATING ALL GRAPHS")
    print("="*60 + "\n")
    
    # Acoustic Features - Line Graphs
    graph1_f0_tracking()
    graph2_speech_rate()
    graph3_pause_duration()
    graph4_jitter_shimmer()
    graph5_spectral_energy()
    
    # Acoustic Features - Box Plots
    graph6_f0_boxplot()
    graph7_voice_quality()
    
    # Linguistic Features
    graph8_lexical_diversity()
    graph9_mlu_progression()
    graph10_information_density()
    graph11_semantic_coherence()
    graph12_content_word_ratio()
    graph13_feature_correlation()
    
    # Task-Specific Analysis
    graph14_utterance_length()
    graph15_pause_frequency()
    
    print("\n" + "="*60)
    print("[OK] ALL 15 GRAPHS GENERATED SUCCESSFULLY")
    print("[OK] Location: ./graphs/")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
