"""
Publication-ready visualization utilities for a cognitive impairment detection system.

All figures are grayscale-friendly and saved in both vector (PDF/SVG) and raster (PNG) formats.
The library emphasizes line styles, markers, and hatching patterns over color.

Dependencies: matplotlib, seaborn, numpy, pandas, plotly, scikit-learn, scipy, shap, librosa
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import io
import json
import math
import os

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import patches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

# Optional/late imports (used in specific plots)
try:
    import shap  # type: ignore
except Exception:  # pragma: no cover
    shap = None

try:
    import librosa  # type: ignore
    import librosa.display  # type: ignore
except Exception:  # pragma: no cover
    librosa = None  # type: ignore

from sklearn import metrics
from sklearn.calibration import calibration_curve
from scipy import stats


MIN_FONTSIZE = 10
LABEL_FONTSIZE = 12
TITLE_FONTSIZE = 14
LINEWIDTH_MIN_PT = 1.0


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _save(fig: mpl.figure.Figure, base_path: str, dpi: int) -> None:
    directory = os.path.dirname(base_path)
    if directory:
        _ensure_dir(directory)
    fig.savefig(f"{base_path}.png", dpi=dpi, bbox_inches="tight")
    fig.savefig(f"{base_path}.pdf", bbox_inches="tight")
    fig.savefig(f"{base_path}.svg", bbox_inches="tight")


@dataclass
class FigureContext:
    width: float = 7.0  # inches
    height: float = 4.2  # inches


class CognitiveVizualizer:
    """Publication-ready visualization generator for cognitive assessment research.

    Methods return matplotlib Figure(s) and also save to disk if a save path is provided.
    All outputs are grayscale-friendly with appropriate line styles and hatching.
    """

    def __init__(self, style: str = 'paper', dpi: int = 300) -> None:
        self.dpi = int(dpi)
        self.style = style
        self.setup_style(style, dpi)

    # ------------------------------
    # Global style configuration
    # ------------------------------
    def setup_style(self, style: str, dpi: int) -> None:
        """Configure matplotlib for publication-quality grayscale plots.

        - Enforces grayscale colormap and high-contrast styles
        - Sets min font sizes and line widths
        """
        mpl.rcParams.update({
            "figure.dpi": dpi,
            "savefig.dpi": dpi,
            "font.size": MIN_FONTSIZE,
            "axes.titlesize": TITLE_FONTSIZE,
            "axes.labelsize": LABEL_FONTSIZE,
            "legend.fontsize": MIN_FONTSIZE,
            "xtick.labelsize": MIN_FONTSIZE,
            "ytick.labelsize": MIN_FONTSIZE,
            "lines.linewidth": LINEWIDTH_MIN_PT,
            "image.cmap": "gray",
            "axes.prop_cycle": plt.cycler(
                linestyle=["-", "--", ":", "-."] * 4,
                marker=["o", "s", "^", "D", "x", "+"] * 3,
                color=["0.1", "0.3", "0.5", "0.7", "0.2", "0.4"],
            ),
        })
        sns.set_theme(style="whitegrid")

    # ------------------------------
    # Figure 1: Pipeline flowchart
    # ------------------------------
    def plot_pipeline_flowchart(self, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 1: 7-step pipeline flowchart.

        Steps:
        Thu âm → Tiền xử lý → Trích đặc trưng → AI Tầng 1 → AI Tầng 2 → Giải thích → Báo cáo
        Each box lists name, input, output, and technologies used.
        """
        steps: List[Dict[str, str]] = [
            {"title": "Thu âm", "input": "Mic", "output": "Audio WAV", "tech": "16kHz PCM"},
            {"title": "Tiền xử lý", "input": "WAV", "output": "Clean WAV", "tech": "VAD, denoise"},
            {"title": "Trích đặc trưng", "input": "Clean WAV", "output": "MFCC, F0", "tech": "librosa"},
            {"title": "AI Tầng 1", "input": "Features", "output": "Risk P(imp)", "tech": "Transformer"},
            {"title": "AI Tầng 2", "input": "Risk+Meta", "output": "Final Risk", "tech": "Calib/Ensemble"},
            {"title": "Giải thích", "input": "Model", "output": "SHAP", "tech": "shap"},
            {"title": "Báo cáo", "input": "Risk+Expl", "output": "PDF", "tech": "matplotlib/LaTeX"},
        ]

        fig, ax = plt.subplots(figsize=(10, 2.6))
        ax.axis('off')

        x0, y0 = 0.05, 0.5
        box_w, box_h = 0.12, 0.32
        gap = 0.02

        hatches = ["///", "\\\\", "---", "|||", "++", "xx", ".."]
        line_styles = ["-", "--", ":", "-.", "-", "--", ":"]

        for i, step in enumerate(steps):
            x = x0 + i * (box_w + gap)
            rect = FancyBboxPatch((x, y0 - box_h / 2), box_w, box_h,
                                  boxstyle="round,pad=0.02,rounding_size=0.02",
                                  edgecolor="black", facecolor="white",
                                  hatch=hatches[i % len(hatches)],
                                  linestyle=line_styles[i % len(line_styles)],
                                  linewidth=1.2)
            ax.add_patch(rect)
            ax.text(x + box_w/2, y0 + 0.08, step["title"], ha="center", va="center", fontsize=12, fontweight="bold")
            ax.text(x + box_w/2, y0, f"In: {step['input']}\nOut: {step['output']}\n{step['tech']}",
                    ha="center", va="center", fontsize=10)

            # Arrow to next
            if i < len(steps) - 1:
                ax.annotate("", xy=(x + box_w + 0.005, y0), xytext=(x + box_w + gap - 0.005, y0),
                            arrowprops=dict(arrowstyle="->", lw=1.2))

        ax.set_title("Hình 1. Pipeline xử lý đa tầng từ thu âm đến báo cáo lâm sàng", pad=12)
        if save_path:
            _save(fig, os.path.join(save_path, "fig1_pipeline"), self.dpi)
        return fig

    # ------------------------------
    # Figure 2: Demographics
    # ------------------------------
    def plot_demographics(self, data: Mapping[str, pd.DataFrame], save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 2: Demographics charts.

        Parameters
        ----------
        data: Mapping with keys:
            - "region_counts": DataFrame columns [group, region, count]
            - "ages": DataFrame columns [age, group]
            - "summary": DataFrame index=group, columns=[mean_age, sd_age, gender_ratio, edu_years]
        """
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))

        # (a) Stacked bar by region
        ax = axes[0]
        df = data["region_counts"]
        groups = ["Healthy", "MCI", "Dementia"]
        regions = ["Bắc", "Trung", "Nam"]
        hatch_map = {"Bắc": "///", "Trung": "---", "Nam": "\\\\"}
        width = 0.6
        bottoms = np.zeros(len(groups))
        for region in regions:
            counts = np.array([df[(df.group == g) & (df.region == region)]["count"].sum() for g in groups])
            bars = ax.bar(groups, counts, width, bottom=bottoms, color="white", edgecolor="black",
                          hatch=hatch_map[region], linewidth=1.0)
            # annotate
            for b in bars:
                h = b.get_height()
                if h > 0:
                    ax.text(b.get_x() + b.get_width()/2, b.get_y() + h/2, f"{int(h)}", ha="center", va="center", fontsize=10)
            bottoms += counts
        ax.set_ylabel("Số lượng")
        ax.set_title("(a) Vùng miền theo nhóm")
        ax.legend(regions, loc="upper right", frameon=True, fontsize=10)

        # (b) Age histogram + density by group
        ax = axes[1]
        ages = data["ages"]
        bins = [50, 55, 60, 65, 70, 75, 80, 120]
        line_styles = {"Healthy": "-", "MCI": "--", "Dementia": ":"}
        for g in groups:
            a = ages[ages.group == g]["age"].values
            ax.hist(a, bins=bins, histtype='step', linewidth=1.2, label=g)
            # KDE overlay
            if len(a) > 1:
                try:
                    sns.kdeplot(a, ax=ax, linestyle=line_styles[g], color="black")
                except Exception:
                    pass
        ax.set_xlabel("Tuổi")
        ax.set_title("(b) Phân bố tuổi")
        ax.legend(frameon=True)

        # (c) Summary table
        ax = axes[2]
        ax.axis('off')
        summary = data["summary"].copy()
        summary = summary.loc[groups]
        display = summary.copy()
        display["Tuổi (Mean±SD)"] = summary.apply(lambda r: f"{r['mean_age']:.1f} ± {r['sd_age']:.1f}", axis=1)
        display["Tỉ lệ nam/nữ"] = summary["gender_ratio"].astype(str)
        display["Số năm học"] = summary["edu_years"].map(lambda x: f"{x:.1f}")
        table = ax.table(cellText=display[["Tuổi (Mean±SD)", "Tỉ lệ nam/nữ", "Số năm học"]].values,
                         rowLabels=display.index.tolist(), colLabels=["Tuổi (Mean±SD)", "Tỉ lệ nam/nữ", "Số năm học"],
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)
        fig.suptitle("Hình 2. Phân bố nhân khẩu học: (a) tỷ lệ vùng miền, (b) phân bố tuổi, (c) thống kê tổng hợp",
                     y=1.02)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig2_demographics"), self.dpi)
        return fig

    # ------------------------------
    # Figure 3: Audio feature comparison
    # ------------------------------
    def plot_audio_comparison(
        self,
        audio_healthy: Optional[Tuple[np.ndarray, int]],
        audio_mci: Optional[Tuple[np.ndarray, int]],
        save_path: Optional[str],
    ) -> mpl.figure.Figure:
        """Figure 3: Waveform, Spectrogram, and F0 contour for Healthy vs MCI.

        If librosa is unavailable or audio is None, synthetic signals are used.
        """
        fig, axes = plt.subplots(2, 3, figsize=(12, 6))

        def _prepare(audio: Optional[Tuple[np.ndarray, int]]) -> Tuple[np.ndarray, int]:
            if audio is None or librosa is None:
                sr = 16000
                t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
                y = 0.2*np.sin(2*np.pi*180*t) + 0.1*np.sin(2*np.pi*260*t)
                y += 0.05*np.random.randn(len(t))
                return y, sr
            return audio

        def _plot_row(row_idx: int, audio_pair: Optional[Tuple[np.ndarray, int]], label: str) -> None:
            y, sr = _prepare(audio_pair)

            # (a) waveform
            ax = axes[row_idx, 0]
            times = np.arange(len(y)) / sr
            ax.plot(times, y, color="black", linewidth=1.0)
            ax.set_xlabel("Thời gian (s)")
            ax.set_ylabel("Biên độ")
            ax.set_title(f"({ 'a' if row_idx==0 else 'd' }) Dạng sóng - {label}")
            # Dummy pause markers
            for t in [0.6, 1.2, 1.8]:
                ax.axvline(t, linestyle=":", color="0.4", linewidth=1.0)

            # (b) spectrogram
            ax = axes[row_idx, 1]
            if librosa is not None:
                S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
                S_db = librosa.amplitude_to_db(S, ref=np.max)
                librosa.display.specshow(S_db, sr=sr, hop_length=256, x_axis='time', y_axis='linear', ax=ax, cmap='gray_r')
            else:  # fallback simple image
                spec = np.abs(np.fft.rfft(y[: sr*2].reshape(-1, 256), axis=1))
                ax.imshow(spec.T, aspect='auto', origin='lower', cmap='gray')
            ax.set_title(f"({ 'b' if row_idx==0 else 'e' }) Phổ tần số")
            ax.set_ylabel("Tần số (Hz)")

            # (c) F0 contour
            ax = axes[row_idx, 2]
            # Simple proxy F0 via moving RMS peaks
            win = 256
            step = 128
            frames = [y[i:i+win] for i in range(0, len(y)-win, step)]
            f0 = np.array([np.argmax(np.abs(np.fft.rfft(f))) for f in frames])
            t_f0 = np.arange(len(f0)) * (step / sr)
            mean = np.mean(f0)
            sd = np.std(f0)
            ax.plot(t_f0, f0, linestyle="-", color="black", label="F0")
            ax.fill_between(t_f0, mean - sd, mean + sd, color="0.85", alpha=1.0, label="±1 SD")
            # Mark drops
            drops = (np.diff(f0, prepend=f0[0]) < -10)
            ax.plot(t_f0[drops], f0[drops], linestyle="none", marker="v", color="0.2", label="Pitch drop")
            ax.set_xlabel("Thời gian (s)")
            ax.set_ylabel("F0 (proxy)")
            ax.set_title(f"({ 'c' if row_idx==0 else 'f' }) Đường bao F0")
            if row_idx == 0:
                ax.legend(frameon=True)

        _plot_row(0, audio_healthy, "Healthy")
        _plot_row(1, audio_mci, "MCI")

        fig.suptitle("Hình 3. So sánh đặc trưng âm học: (a,d) dạng sóng, (b,e) phổ tần số, (c,f) đường bao F0",
                     y=0.98)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig3_audio_comparison"), self.dpi)
        return fig

    # ------------------------------
    # Figure 4: ROC + Calibration
    # ------------------------------
    def plot_roc_curves(
        self,
        y_true: np.ndarray,
        y_scores: Mapping[str, np.ndarray],
        save_path: Optional[str],
    ) -> mpl.figure.Figure:
        """Figure 4: ROC curves for multiple models + calibration curve with Brier score.

        y_scores: dict of model_name -> predicted probability for the positive class
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # (a) ROC
        ax = axes[0]
        styles = {"Tier-1": "-", "Tier-2": "--", "Ensemble": ":"}
        for name, scores in y_scores.items():
            fpr, tpr, thr = metrics.roc_curve(y_true, scores)
            auc = metrics.roc_auc_score(y_true, scores)
            # 95% CI via DeLong bootstrap (approx):
            try:
                boots = []
                rng = np.random.default_rng(0)
                for _ in range(200):
                    idx = rng.integers(0, len(y_true), len(y_true))
                    boots.append(metrics.roc_auc_score(y_true[idx], scores[idx]))
                lo, hi = np.percentile(boots, [2.5, 97.5])
                label = f"{name} (AUC={auc:.3f} [{lo:.3f},{hi:.3f}])"
            except Exception:
                label = f"{name} (AUC={auc:.3f})"
            ax.plot(fpr, tpr, linestyle=styles.get(name, "-"), label=label)
            # Optimal threshold (Youden)
            j = np.argmax(tpr - fpr)
            ax.plot(fpr[j], tpr[j], marker="o", color="0.2")
        ax.plot([0, 1], [0, 1], linestyle=":", color="0.5", label="Baseline")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("(a) ROC")
        ax.legend(loc="lower right", frameon=True)

        # (b) Calibration
        ax = axes[1]
        # Plot for the Ensemble if present, otherwise first entry
        name_for_cal = "Ensemble" if "Ensemble" in y_scores else next(iter(y_scores))
        prob_true, prob_pred = calibration_curve(y_true, y_scores[name_for_cal], n_bins=10)
        ax.plot([0, 1], [0, 1], linestyle=":", color="0.6", label="Perfect")
        ax.plot(prob_pred, prob_true, marker="s", linestyle="-", color="0.1", label=name_for_cal)
        brier = metrics.brier_score_loss(y_true, y_scores[name_for_cal])
        ax.set_title(f"(b) Calibration (Brier={brier:.3f})")
        ax.set_xlabel("Predicted probability")
        ax.set_ylabel("True probability")
        ax.legend(frameon=True)

        fig.suptitle("Hình 4. Hiệu năng phân loại: (a) ROC với AUC, (b) đường chuẩn hóa xác suất", y=1.02)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig4_roc_calibration"), self.dpi)
        return fig

    # ------------------------------
    # Figure 5: Confusion matrix
    # ------------------------------
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 5: 3x3 confusion matrix with absolute counts, percentages, and metrics."""
        labels = ["Healthy", "MCI", "Dementia"]
        cm = metrics.confusion_matrix(y_true, y_pred, labels=range(3))
        cm_norm = cm / cm.sum(axis=1, keepdims=True)

        fig, ax = plt.subplots(figsize=(5.4, 4.8))
        im = ax.imshow(cm_norm, cmap="gray_r")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cm[i,j]}\n({cm_norm[i,j]*100:.1f}%)", ha="center", va="center", fontsize=10)
        ax.set_xticks(range(3), labels)
        ax.set_yticks(range(3), labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title("Hình 5. Ma trận nhầm lẫn trên tập test")

        # Per-class metrics
        report = metrics.classification_report(y_true, y_pred, labels=range(3), target_names=labels, output_dict=True)
        overall_acc = metrics.accuracy_score(y_true, y_pred)
        macro_f1 = metrics.f1_score(y_true, y_pred, average='macro')
        weighted_f1 = metrics.f1_score(y_true, y_pred, average='weighted')

        text = io.StringIO()
        text.write(f"Accuracy: {overall_acc:.3f}\n")
        text.write(f"Macro F1: {macro_f1:.3f}\nWeighted F1: {weighted_f1:.3f}\n")
        for cls in labels:
            pr = report[cls]
            text.write(f"{cls}: P={pr['precision']:.2f}, R={pr['recall']:.2f}, F1={pr['f1-score']:.2f}\n")
        ax.figure.text(1.02, 0.5, text.getvalue(), va='center', fontsize=10)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig5_confusion_matrix"), self.dpi)
        return fig

    # ------------------------------
    # Figure 6: SHAP analyses
    # ------------------------------
    def plot_shap_analysis(
        self,
        shap_values: Optional["shap._explanation.Explanation"],  # type: ignore
        X: pd.DataFrame,
        save_path: Optional[str],
    ) -> mpl.figure.Figure:
        """Figure 6: SHAP summary and waterfalls.

        If `shap` is not installed or values are None, a bar plot of feature importances is shown instead.
        """
        fig = plt.figure(figsize=(12, 6))

        # (a) summary
        ax1 = plt.subplot2grid((2, 3), (0, 0), colspan=2)
        if shap is not None and shap_values is not None:
            try:
                shap.summary_plot(shap_values, X, show=False, plot_type="dot", color=None)
                plt.title("(a) SHAP summary (beeswarm)")
            except Exception:
                # Fallback to bar
                importances = np.abs(np.asarray(shap_values.values)).mean(axis=0)
                order = np.argsort(importances)[::-1][:20]
                ax1.barh(np.array(X.columns)[order], importances[order], color="white", edgecolor="black", hatch="///")
                ax1.invert_yaxis()
                ax1.set_title("(a) SHAP importance (bar)")
        else:
            # Synthetic importance from standard deviation
            importances = X.std(axis=0).values
            order = np.argsort(importances)[::-1][:20]
            ax1.barh(np.array(X.columns)[order], importances[order], color="white", edgecolor="black", hatch="///")
            ax1.invert_yaxis()
            ax1.set_title("(a) Feature importance (proxy)")

        # (b) and (c) waterfalls (mock using bar contributions)
        def _waterfall(ax: mpl.axes.Axes, contrib: np.ndarray, title: str) -> None:
            base = np.mean(contrib)
            idx = np.argsort(np.abs(contrib))[::-1][:10]
            ax.bar(np.arange(len(idx)), contrib[idx], color="white", edgecolor="black", hatch="---")
            ax.axhline(base, linestyle=":", color="0.3")
            ax.set_xticks(np.arange(len(idx)))
            ax.set_xticklabels(np.array(X.columns)[idx], rotation=45, ha='right')
            ax.set_title(title)

        ax2 = plt.subplot2grid((2, 3), (0, 2))
        ax3 = plt.subplot2grid((2, 3), (1, 2))
        rng = np.random.default_rng(0)
        _waterfall(ax2, rng.normal(0, 1, size=X.shape[1]), "(b) True Positive case")
        _waterfall(ax3, rng.normal(0, 1, size=X.shape[1]), "(c) False Negative case")

        plt.suptitle("Hình 6. Giải thích mô hình SHAP")
        plt.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig6_shap"), self.dpi)
        return fig

    # ------------------------------
    # Figure 7: MMSE prediction scatter
    # ------------------------------
    def plot_mmse_prediction(self, y_true: np.ndarray, y_pred: np.ndarray, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 7: Predicted vs Actual MMSE with metrics and y=x line."""
        fig, ax = plt.subplots(figsize=(5.6, 4.2))
        ax.plot(y_true, y_pred, linestyle="none", marker="o", color="0.2", label="Samples")
        lim = [0, max(30, int(max(y_true.max(), y_pred.max())))]
        ax.plot(lim, lim, linestyle=":", color="0.5", label="y=x")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel("Actual MMSE")
        ax.set_ylabel("Predicted MMSE")

        # Metrics
        pearson_r, _ = stats.pearsonr(y_true, y_pred)
        spearman_r, _ = stats.spearmanr(y_true, y_pred)
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        ax.legend(loc="upper left", frameon=True)
        ax.text(0.98, 0.02, f"r={pearson_r:.2f}\nρ={spearman_r:.2f}\nMAE={mae:.2f}\nRMSE={rmse:.2f}",
                transform=ax.transAxes, ha='right', va='bottom', fontsize=10,
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="black"))
        ax.set_title("Hình 7. Tương quan MMSE dự đoán vs thực tế")
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig7_mmse_scatter"), self.dpi)
        return fig

    # ------------------------------
    # Figure 8: Calibration + threshold table
    # ------------------------------
    def plot_calibration_table(self, y_true: np.ndarray, y_scores: np.ndarray, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 8: Reliability diagram and threshold table."""
        fig = plt.figure(figsize=(10, 4.2))

        # (a) reliability diagram
        ax1 = plt.subplot2grid((1, 2), (0, 0))
        prob_true, prob_pred = calibration_curve(y_true, y_scores, n_bins=10)
        ax1.plot([0, 1], [0, 1], linestyle=":", color="0.6", label="Perfect")
        ax1.plot(prob_pred, prob_true, marker="o", linestyle="-", color="0.1", label="Model")
        ax1.set_xlabel("Predicted probability (binned)")
        ax1.set_ylabel("Observed frequency")
        ax1.legend(frameon=True)

        # Gap histogram underlay (simple vertical bars)
        for x, y in zip(prob_pred, np.abs(prob_pred - prob_true)):
            ax1.vlines(x, 0, y, color="0.3", linestyles="--", linewidth=1.0)

        # (b) threshold table
        ax2 = plt.subplot2grid((1, 2), (0, 1))
        ax2.axis('off')
        thresholds = [0.3, 0.5, 0.7]
        rows = []
        for th in thresholds:
            pred = (y_scores >= th).astype(int)
            tn, fp, fn, tp = metrics.confusion_matrix(y_true, pred, labels=[0,1]).ravel()
            sens = tp / (tp + fn + 1e-9)
            spec = tn / (tn + fp + 1e-9)
            ppv = tp / (tp + fp + 1e-9)
            npv = tn / (tn + fn + 1e-9)
            f1 = metrics.f1_score(y_true, pred)
            rows.append([f"{th:.1f}", f"{sens:.2f}", f"{spec:.2f}", f"{ppv:.2f}", f"{npv:.2f}", f"{f1:.2f}"])
        table = ax2.table(cellText=rows,
                          colLabels=["Threshold", "Sensitivity", "Specificity", "PPV", "NPV", "F1"],
                          loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.2)
        fig.suptitle("Hình 8. Calibration và bảng ngưỡng quyết định", y=1.02)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig8_calibration_threshold"), self.dpi)
        return fig

    # ------------------------------
    # Figure 9: Longitudinal trajectories
    # ------------------------------
    def plot_longitudinal(self, data: pd.DataFrame, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 9: Trajectories over time for Stable vs Declining.

        Expects columns: [id, months, score, group] with group in {Stable, Declining}
        """
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
        for i, grp in enumerate(["Stable", "Declining"]):
            ax = axes[i]
            sub = data[data.group == grp]
            for pid, dfp in sub.groupby("id"):
                ax.plot(dfp["months"], dfp["score"], color="0.5", linewidth=1.0, marker="o", alpha=0.7)
            # group mean with CI
            means = sub.groupby("months")["score"].mean().reset_index()
            stds = sub.groupby("months")["score"].std().reset_index()
            ax.plot(means["months"], means["score"], color="0.1", linewidth=2.0, linestyle="-", label="Mean")
            ax.fill_between(means["months"], (means["score"]-stds["score"]).values, (means["score"]+stds["score"]).values,
                            color="0.85", alpha=1.0, label="±1 SD")
            ax.set_title(grp)
            ax.set_xlabel("Tháng")
        axes[0].set_ylabel("Điểm số")
        axes[0].legend(frameon=True)
        fig.suptitle("Hình 9. Quỹ đạo theo thời gian")
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig9_longitudinal"), self.dpi)
        return fig

    # ------------------------------
    # Figure 10: UI mockups
    # ------------------------------
    def plot_ui_mockup(self, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 10: Simple grayscale wireframes for Recording and Report screens."""
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))

        # (a) Recording screen
        ax = axes[0]
        ax.axis('off')
        ax.set_title("(a) Recording Screen")
        ax.add_patch(patches.Rectangle((0.1, 0.15), 0.8, 0.7, fill=False, hatch="///", edgecolor="black"))
        ax.text(0.5, 0.75, "Instructions: Nói theo hướng dẫn...", ha='center', fontsize=18/1.333)
        ax.add_patch(patches.FancyBboxPatch((0.3, 0.35), 0.4, 0.2, boxstyle="round,pad=0.02",
                                            edgecolor="black", facecolor="white", hatch="---"))
        ax.text(0.5, 0.45, "START / STOP", ha='center', va='center', fontsize=18)
        ax.add_patch(patches.Rectangle((0.2, 0.28), 0.6, 0.03, edgecolor="black", facecolor="white", hatch="xx"))

        # (b) Report PDF sample
        ax = axes[1]
        ax.axis('off')
        ax.set_title("(b) Report PDF Sample")
        ax.add_patch(patches.Rectangle((0.1, 0.1), 0.8, 0.8, fill=False, hatch="\\\\", edgecolor="black"))
        ax.text(0.5, 0.85, "Patient: XXX | Date: YYYY-MM-DD | Risk: 0.42", ha='center', fontsize=12)
        # gauge placeholder
        ax.add_patch(patches.Wedge(center=(0.25, 0.6), r=0.15, theta1=180, theta2=360, fill=False, hatch="..."))
        # sections
        ax.add_patch(patches.Rectangle((0.45, 0.55), 0.4, 0.2, fill=False, hatch="---"))
        ax.text(0.65, 0.65, "Feature breakdown", ha='center', fontsize=12)
        ax.add_patch(patches.Rectangle((0.45, 0.3), 0.4, 0.2, fill=False, hatch="///"))
        ax.text(0.65, 0.38, "Recommendations", ha='center', fontsize=12)

        fig.suptitle("Hình 10. Wireframes UI", y=0.98)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig10_ui_mockups"), self.dpi)
        return fig

    # ------------------------------
    # Figure 11: Deployment architecture
    # ------------------------------
    def plot_architecture(self, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 11: Deployment architecture diagram in grayscale."""
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis('off')

        boxes = [
            (0.05, 0.7, 0.25, 0.2, "Mobile/Web"),
            (0.35, 0.7, 0.25, 0.2, "API Gateway\n+ Auth"),
            (0.65, 0.7, 0.25, 0.2, "Load Balancer"),
            (0.35, 0.4, 0.25, 0.2, "Model Server\nCluster"),
            (0.35, 0.15, 0.25, 0.2, "PostgreSQL\n+ Redis"),
            (0.65, 0.15, 0.25, 0.2, "Audit Log\n+ Encrypted Storage"),
        ]
        hatches = ["///", "---", "\\\\", "xxx", "++", "..."]
        for i, (x, y, w, h, label) in enumerate(boxes):
            ax.add_patch(patches.Rectangle((x, y), w, h, fill=False, hatch=hatches[i % len(hatches)], edgecolor="black"))
            ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=12)
        # arrows
        def arrow(x1, y1, x2, y2):
            ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", lw=1.2))
        arrow(0.3, 0.8, 0.35, 0.8)
        arrow(0.6, 0.8, 0.65, 0.8)
        arrow(0.775, 0.7, 0.775, 0.6)
        arrow(0.475, 0.6, 0.475, 0.5)
        arrow(0.475, 0.35, 0.475, 0.25)
        arrow(0.475, 0.25, 0.775, 0.25)
        # security icons (locks)
        ax.text(0.36, 0.86, "🔒", fontsize=14)
        ax.text(0.68, 0.86, "🔒", fontsize=14)
        ax.set_title("Hình 11. Kiến trúc triển khai")
        if save_path:
            _save(fig, os.path.join(save_path, "fig11_architecture"), self.dpi)
        return fig

    # ------------------------------
    # Figure 12: ASR WER by dialect
    # ------------------------------
    def plot_asr_wer(self, wer_data: pd.DataFrame, save_path: Optional[str]) -> mpl.figure.Figure:
        """Figure 12: WER by dialect with error bars and overall line.

        Expects columns: [dialect, wer_mean, wer_sd]
        """
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        dialects = wer_data["dialect"].values
        means = wer_data["wer_mean"].values
        sds = wer_data["wer_sd"].values
        hatches = ["///", "---", "\\\\", "xxx", "++"]
        bars = ax.bar(dialects, means, yerr=sds, color="white", edgecolor="black", hatch=None, capsize=4)
        for i, b in enumerate(bars):
            b.set_hatch(hatches[i % len(hatches)])
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + sds[i] + 0.5, f"{means[i]:.1f}%", ha='center', fontsize=10)
        overall = np.average(means, weights=np.maximum(1, 1/sds**2)) if (sds > 0).any() else means.mean()
        ax.axhline(overall, linestyle=":", color="0.4", label=f"Overall {overall:.1f}%")
        ax.set_ylabel("WER (%)")
        ax.set_title("Hình 12. WER theo phương ngôn")
        ax.legend(frameon=True)
        fig.tight_layout()
        if save_path:
            _save(fig, os.path.join(save_path, "fig12_asr_wer"), self.dpi)
        return fig

    # ------------------------------
    # Helper to generate everything with dummy data
    # ------------------------------
    def save_all_figures(self, output_dir: str) -> None:
        """Generate all figures with synthetic/dummy data and save to output_dir.

        This is intended for quick end-to-end testing and paper mockups.
        """
        _ensure_dir(output_dir)

        # Fig 1
        self.plot_pipeline_flowchart(output_dir)

        # Fig 2 data
        region_counts = pd.DataFrame({
            "group": np.repeat(["Healthy", "MCI", "Dementia"], 3),
            "region": ["Bắc", "Trung", "Nam"] * 3,
            "count": [60, 30, 50, 40, 25, 35, 30, 20, 25],
        })
        ages = pd.DataFrame({
            "age": np.concatenate([
                np.random.normal(62, 5, 140),
                np.random.normal(68, 6, 100),
                np.random.normal(74, 6, 75),
            ]),
            "group": np.repeat(["Healthy", "MCI", "Dementia"], [140, 100, 75])
        })
        summary = pd.DataFrame(index=["Healthy", "MCI", "Dementia"], data={
            "mean_age": [62.1, 67.8, 73.9],
            "sd_age": [5.1, 5.9, 6.2],
            "gender_ratio": ["1.0:1.0", "0.9:1.1", "0.8:1.2"],
            "edu_years": [10.5, 9.2, 8.1],
        })
        self.plot_demographics({"region_counts": region_counts, "ages": ages, "summary": summary}, output_dir)

        # Fig 3 (audio synthetic)
        self.plot_audio_comparison(None, None, output_dir)

        # Fig 4 ROC/Calibration
        y_true = np.random.randint(0, 2, size=300)
        y1 = np.clip(np.random.beta(2, 4, size=300), 0, 1)
        y2 = np.clip(np.random.beta(3, 3, size=300), 0, 1)
        y3 = (y1 + y2) / 2
        self.plot_roc_curves(y_true, {"Tier-1": y1, "Tier-2": y2, "Ensemble": y3}, output_dir)

        # Fig 5 Confusion matrix
        y_true3 = np.random.randint(0, 3, size=200)
        y_pred3 = (y_true3 + np.random.choice([-1, 0, 1], size=200, p=[0.15, 0.7, 0.15])) % 3
        self.plot_confusion_matrix(y_true3, y_pred3, output_dir)

        # Fig 6 SHAP (synthetic X)
        X = pd.DataFrame(np.random.randn(200, 25), columns=[f"f{i}" for i in range(25)])
        self.plot_shap_analysis(None, X, output_dir)

        # Fig 7 MMSE scatter
        y_true_m = np.random.randint(15, 30, size=120)
        y_pred_m = y_true_m + np.random.normal(0, 2.5, size=120)
        self.plot_mmse_prediction(y_true_m, y_pred_m, output_dir)

        # Fig 8 Calibration + threshold
        y_true_bin = np.random.randint(0, 2, size=250)
        y_scores_bin = np.clip(np.random.beta(2.5, 2.5, size=250), 0, 1)
        self.plot_calibration_table(y_true_bin, y_scores_bin, output_dir)

        # Fig 9 Longitudinal
        ids = np.arange(30)
        months = np.tile(np.array([0, 3, 6, 9, 12]), len(ids))
        stable_scores = np.clip(26 + np.random.randn(len(ids), 5)*0.7, 0, 30)
        declining_scores = np.clip(26 + np.arange(5)*-0.6 + np.random.randn(len(ids), 5)*0.8, 0, 30)
        df_long = []
        for i, pid in enumerate(ids):
            grp = "Stable" if i < 15 else "Declining"
            sc = stable_scores[i % 15] if grp == "Stable" else declining_scores[i % 15]
            for j, m in enumerate([0, 3, 6, 9, 12]):
                df_long.append([pid, m, sc[j], grp])
        df_long = pd.DataFrame(df_long, columns=["id", "months", "score", "group"])
        self.plot_longitudinal(df_long, output_dir)

        # Fig 10 UI
        self.plot_ui_mockup(output_dir)

        # Fig 11 Architecture
        self.plot_architecture(output_dir)

        # Fig 12 ASR WER by dialect
        wer_df = pd.DataFrame({
            "dialect": ["Bắc", "Trung", "Nam", "Tây Nguyên"],
            "wer_mean": [9.8, 12.5, 11.1, 13.2],
            "wer_sd": [1.3, 1.9, 1.6, 2.1],
        })
        self.plot_asr_wer(wer_df, output_dir)


if __name__ == "__main__":  # Manual quick run
    viz = CognitiveVizualizer(style='paper', dpi=300)
    viz.save_all_figures(os.path.join(os.path.dirname(__file__), 'figures'))


