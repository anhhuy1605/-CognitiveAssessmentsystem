# -*- coding: utf-8 -*-
"""
SHAP Visualizations Module
==========================

Creates static and animated visualizations for SHAP explanations.

Author: Cognitive Assessment System
Version: 1.0
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, FancyBboxPatch
import seaborn as sns
import io
import base64
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import plotly for interactive charts
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Interactive charts will be limited.")

# Color palette
COLORS = {
    'positive': '#2ecc71',      # Green - good factors
    'negative': '#e74c3c',      # Red - risk factors
    'neutral': '#95a5a6',       # Gray - minimal impact
    'warning': '#f39c12',       # Orange - moderate concern
    'info': '#3498db',          # Blue - information
    'background': '#ecf0f1',    # Light gray
    'text': '#2c3e50'           # Dark gray
}

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def create_waterfall_plot(shap_result: Dict[str, Any],
                          language: str = 'vi',
                          top_n: int = 10) -> str:
    """
    Create SHAP waterfall plot showing feature contributions
    
    Requirements:
    - Start from base value (expected MMSE)
    - Show each feature pushing prediction up/down
    - End at final prediction
    - Color: green (positive), red (negative)
    - Annotate with Vietnamese labels
    
    Returns:
        Base64-encoded PNG image
    """
    try:
        feature_contributions = shap_result.get('feature_contributions', {})
        base_value = shap_result.get('base_value', 0.0)
        prediction = shap_result.get('prediction', 0.0)
        
        # Sort by absolute contribution
        sorted_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:top_n]
        
        # Prepare data
        features = []
        contributions = []
        colors_list = []
        
        for feat, contrib in sorted_features:
            features.append(feat)
            contributions.append(contrib)
            colors_list.append(COLORS['positive'] if contrib > 0 else COLORS['negative'])
        
        # Create waterfall
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Starting point
        current_value = base_value
        y_positions = [current_value]
        
        # Plot each feature
        for i, (feat, contrib) in enumerate(sorted_features):
            # Bar from current to new value
            ax.barh(i, contrib, left=current_value, 
                   color=colors_list[i], alpha=0.7, edgecolor='black', linewidth=1)
            
            # Add value label
            mid_value = current_value + contrib / 2
            ax.text(mid_value, i, f'{contrib:+.2f}', 
                   ha='center', va='center', fontweight='bold', fontsize=9)
            
            current_value += contrib
            y_positions.append(current_value)
        
        # Final prediction line
        ax.axvline(prediction, color='black', linestyle='--', linewidth=2, label='Final Prediction')
        ax.text(prediction, len(sorted_features) / 2, f'Prediction: {prediction:.1f}',
               rotation=90, va='center', fontsize=12, fontweight='bold')
        
        # Base value line
        ax.axvline(base_value, color='gray', linestyle=':', linewidth=1, label='Base Value')
        
        # Labels
        ax.set_yticks(range(len(sorted_features)))
        ax.set_yticklabels([f[:30] for f in features], fontsize=9)
        ax.set_xlabel('MMSE Score Contribution' if language == 'en' else 'Đóng góp vào điểm MMSE', fontsize=11)
        ax.set_title('SHAP Waterfall Plot' if language == 'en' else 'Biểu đồ Phân tích Đóng góp', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Legend
        ax.legend(loc='best')
        
        # Grid
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error creating waterfall plot: {e}", exc_info=True)
        return ""


def create_feature_importance_bar(shap_result: Dict[str, Any],
                                  top_n: int = 10,
                                  language: str = 'vi') -> str:
    """
    Bar chart of top N contributing features
    
    Two versions:
    1. Absolute importance (|SHAP value|)
    2. Directional importance (signed SHAP value)
    
    Returns:
        Base64-encoded PNG image
    """
    try:
        feature_importance = shap_result.get('feature_importance', {})
        
        # Get top N
        top_features = list(feature_importance.items())[:top_n]
        features = [f[0] for f in top_features]
        importances = [f[1] for f in top_features]
        
        # Get contributions for color
        contributions = shap_result.get('feature_contributions', {})
        colors_list = [
            COLORS['positive'] if contributions.get(feat, 0) > 0 else COLORS['negative']
            for feat in features
        ]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.barh(range(len(features)), importances, color=colors_list, alpha=0.7, edgecolor='black')
        
        # Labels
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels([f[:40] for f in features], fontsize=9)
        ax.set_xlabel('Importance' if language == 'en' else 'Mức độ quan trọng', fontsize=11)
        ax.set_title(f'Top {top_n} Contributing Features' if language == 'en' else f'Top {top_n} Đặc trưng Ảnh hưởng Nhất',
                    fontsize=14, fontweight='bold')
        
        # Value labels
        for i, (bar, imp) in enumerate(zip(bars, importances)):
            ax.text(imp, i, f' {imp:.3f}', va='center', fontsize=8)
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error creating importance bar: {e}", exc_info=True)
        return ""


def create_radar_chart(grouped_contributions: Dict[str, Dict[str, Any]],
                      language: str = 'vi') -> str:
    """
    Radar chart showing performance across cognitive domains
    
    Axes:
    - Voice Quality (acoustic)
    - Speech Fluency (acoustic + linguistic)
    - Vocabulary (linguistic)
    - Grammar (linguistic)
    - Coherence (linguistic + semantic)
    - Content (GPT-4o)
    
    Returns:
        Base64-encoded PNG image
    """
    try:
        # Map groups to radar axes
        group_mapping = {
            'Voice Quality': 'acoustic_spectral',
            'Voice Stability': 'acoustic_voice_quality',
            'Speech Melody': 'acoustic_prosodic',
            'Speech Fluency': 'acoustic_temporal',
            'Vocabulary Richness': 'linguistic_lexical',
            'Grammar Complexity': 'linguistic_syntactic',
            'Content Coherence': 'linguistic_semantic'
        }
        
        # Extract values
        categories = []
        values = []
        
        for display_name, group_key in group_mapping.items():
            group_data = grouped_contributions.get(display_name)
            if group_data:
                # Normalize contribution to 0-1 scale
                contrib = group_data.get('contribution', 0.0)
                normalized = max(0, min(1, (contrib + 2) / 4))  # Map -2 to 2 -> 0 to 1
                categories.append(display_name)
                values.append(normalized)
            else:
                categories.append(display_name)
                values.append(0.5)  # Neutral
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # Close the circle
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, color=COLORS['info'])
        ax.fill(angles, values, alpha=0.25, color=COLORS['info'])
        
        # Labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['Low', 'Medium', 'High', 'Very High'], fontsize=8)
        ax.grid(True)
        
        ax.set_title('Cognitive Domain Assessment' if language == 'en' else 'Đánh giá Các Lĩnh vực Nhận thức',
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error creating radar chart: {e}", exc_info=True)
        return ""


def create_contribution_animation(shap_result: Dict[str, Any],
                                 duration: float = 5.0,
                                 language: str = 'vi') -> Optional[str]:
    """
    Animated visualization of how features contribute to prediction
    
    Animation sequence:
    1. Start: Show base value (expected MMSE for population)
    2. Step-by-step: Add each feature's contribution with smooth transition
    3. Highlight: Feature name + value + interpretation pops up
    4. Accumulate: Running total updates
    5. End: Final prediction with confidence interval
    
    Returns:
        Base64-encoded MP4 or HTML with animation
    """
    try:
        feature_contributions = shap_result.get('feature_contributions', {})
        base_value = shap_result.get('base_value', 0.0)
        prediction = shap_result.get('prediction', 0.0)
        
        # Sort by absolute contribution
        sorted_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]  # Top 10
        
        if not sorted_features:
            return None
        
        # Setup figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Animation data
        current_value = base_value
        accumulated_values = [base_value]
        feature_names = []
        
        def animate(frame):
            ax.clear()
            
            if frame == 0:
                # Initial state
                ax.barh(0, base_value, left=0, color=COLORS['neutral'], alpha=0.5)
                ax.text(base_value/2, 0, f'Base: {base_value:.1f}', 
                       ha='center', va='center', fontsize=12, fontweight='bold')
                ax.set_xlim(0, 30)
                ax.set_ylim(-0.5, len(sorted_features) + 0.5)
                ax.set_xlabel('MMSE Score' if language == 'en' else 'Điểm MMSE', fontsize=11)
                ax.set_title('Starting from baseline...' if language == 'en' else 'Bắt đầu từ giá trị cơ bản...',
                            fontsize=14, fontweight='bold')
                return
            
            # Calculate which feature to show
            feature_idx = min(frame - 1, len(sorted_features) - 1)
            feat, contrib = sorted_features[feature_idx]
            
            # Accumulate
            current = base_value + sum(c[1] for c in sorted_features[:feature_idx+1])
            accumulated_values.append(current)
            
            # Plot accumulated bars
            for i, (f, c) in enumerate(sorted_features[:feature_idx+1]):
                start_val = base_value + sum(prev_c for prev_f, prev_c in sorted_features[:i])
                color = COLORS['positive'] if c > 0 else COLORS['negative']
                ax.barh(i, c, left=start_val, color=color, alpha=0.7, edgecolor='black')
                
                # Label
                mid = start_val + c / 2
                ax.text(mid, i, f'{c:+.2f}', ha='center', va='center', 
                       fontsize=9, fontweight='bold')
            
            # Current total
            ax.axvline(current, color='black', linestyle='--', linewidth=2)
            ax.text(current, len(sorted_features) / 2, f'Total: {current:.1f}',
                   rotation=90, va='center', fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
            
            # Feature name
            ax.text(15, feature_idx, f'{feat[:30]}', fontsize=10, 
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            ax.set_xlim(0, 30)
            ax.set_ylim(-0.5, len(sorted_features) + 0.5)
            ax.set_xlabel('MMSE Score' if language == 'en' else 'Điểm MMSE', fontsize=11)
            ax.set_title(f'Adding: {feat[:30]}...' if language == 'en' else f'Thêm: {feat[:30]}...',
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
        
        # Create animation
        frames = len(sorted_features) + 1
        anim = animation.FuncAnimation(fig, animate, frames=frames, 
                                       interval=duration*1000/frames, repeat=False)
        
        # Save as HTML (interactive)
        html_str = anim.to_jshtml()
        
        return html_str
        
    except Exception as e:
        logger.error(f"Error creating animation: {e}", exc_info=True)
        return None


def create_risk_gauge_animation(mmse_prediction: float,
                                confidence_interval: Tuple[float, float],
                                language: str = 'vi') -> str:
    """
    Animated gauge showing risk level
    
    Design:
    - Semicircular gauge (0-30 MMSE scale)
    - Zones: Green (24-30), Yellow (18-23), Red (0-17)
    - Needle animates from center to predicted value
    - Confidence interval shown as shaded arc
    - Final state: Risk text appears with icon
    
    Returns:
        Base64-encoded PNG (static) or HTML (animated)
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
        
        # Gauge parameters
        theta_min = np.pi  # Start from left (180 degrees)
        theta_max = 0      # End at right (0 degrees)
        theta_range = np.linspace(theta_min, theta_max, 100)
        
        # Risk zones
        zones = [
            (24, 30, COLORS['positive'], 'Normal'),
            (18, 24, COLORS['warning'], 'MCI'),
            (0, 18, COLORS['negative'], 'Dementia')
        ]
        
        # Draw zones
        for low, high, color, label in zones:
            zone_theta = np.linspace(
                theta_min - (low / 30) * (theta_min - theta_max),
                theta_min - (high / 30) * (theta_min - theta_max),
                50
            )
            ax.fill_between(zone_theta, 0, 1, color=color, alpha=0.3, label=label)
        
        # Prediction needle
        pred_theta = theta_min - (mmse_prediction / 30) * (theta_min - theta_max)
        ax.plot([pred_theta, pred_theta], [0, 1], 'k-', linewidth=3, label='Prediction')
        
        # Confidence interval
        ci_low, ci_high = confidence_interval
        theta_low = theta_min - (ci_low / 30) * (theta_min - theta_max)
        theta_high = theta_min - (ci_high / 30) * (theta_min - theta_max)
        ax.fill_between([theta_low, theta_high], [0, 0], [1, 1], 
                       color='gray', alpha=0.2, label='Confidence Interval')
        
        # Labels
        ax.set_xticks([theta_min, theta_min - np.pi/2, theta_max])
        ax.set_xticklabels(['0', '15', '30'], fontsize=12)
        ax.set_ylim(0, 1.2)
        ax.set_yticks([])
        
        # Title
        risk_level = 'Normal' if mmse_prediction >= 24 else 'MCI' if mmse_prediction >= 18 else 'Dementia'
        ax.set_title(f'MMSE Risk Assessment: {risk_level} ({mmse_prediction:.1f}/30)' 
                    if language == 'en' else 
                    f'Đánh giá Nguy cơ MMSE: {risk_level} ({mmse_prediction:.1f}/30)',
                    fontsize=14, fontweight='bold', pad=20)
        
        ax.legend(loc='upper right')
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error creating risk gauge: {e}", exc_info=True)
        return ""


def create_all_visualizations(shap_result: Dict[str, Any],
                             grouped_contributions: Dict[str, Dict[str, Any]],
                             mmse_score: int = 0,
                             language: str = 'vi') -> Dict[str, str]:
    """
    Create all visualizations and return as base64 images
    
    Returns:
        {
            'waterfall': base64_string,
            'importance_bar': base64_string,
            'radar_chart': base64_string,
            'risk_gauge': base64_string,
            'animation_html': html_string (optional)
        }
    """
    visualizations = {}
    
    try:
        visualizations['waterfall'] = create_waterfall_plot(shap_result, language)
        visualizations['importance_bar'] = create_feature_importance_bar(shap_result, language=language)
        visualizations['radar_chart'] = create_radar_chart(grouped_contributions, language)
        
        # Risk gauge with confidence interval
        confidence_interval = (mmse_score - 2, mmse_score + 2)  # Simple ±2
        visualizations['risk_gauge'] = create_risk_gauge_animation(
            float(mmse_score), confidence_interval, language
        )
        
        # Animation (optional, can be slow)
        try:
            anim_html = create_contribution_animation(shap_result, language=language)
            if anim_html:
                visualizations['animation_html'] = anim_html
        except Exception as e:
            logger.warning(f"Animation creation skipped: {e}")
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}", exc_info=True)
    
    return visualizations


