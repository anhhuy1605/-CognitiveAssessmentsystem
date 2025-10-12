#!/usr/bin/env python3
"""
MMSE Evaluator for Clinical Performance Assessment
================================================

Comprehensive evaluation framework for speech-based MMSE assessment:
- Clinical performance metrics (RMSE, MAE, correlation, ICC)
- Classification metrics (sensitivity, specificity, AUC)
- Fairness analysis (demographic subgroups)
- Uncertainty quantification
- Bootstrap confidence intervals
- Bland-Altman agreement analysis

Author: AI Assistant
Date: September 2025
"""

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import logging
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MMSEEvaluator:
    """
    Comprehensive evaluator for speech-based MMSE assessment.

    Provides clinical-grade evaluation metrics and fairness analysis.
    """

    def __init__(self, output_dir: str = 'evaluation_results'):
        """
        Initialize MMSE evaluator.

        Args:
            output_dir: Directory to save evaluation results and plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Clinical performance targets
        self.targets = {
            'rmse_max': 2.5,      # RMSE ≤ 2.5 points
            'mae_max': 2.0,       # MAE ≤ 2.0 points
            'r2_min': 0.7,        # R² ≥ 0.7
            'corr_min': 0.85,     # Correlation ≥ 0.85
            'sensitivity_min': 0.80,  # Sensitivity ≥ 0.80
            'specificity_min': 0.75   # Specificity ≥ 0.75
        }

        logger.info(f"✅ MMSE Evaluator initialized - Results will be saved to {output_dir}")

    def evaluate_regression_performance(self,
                                       y_true: np.ndarray,
                                       y_pred: np.ndarray,
                                       save_plots: bool = True) -> Dict[str, Any]:
        """
        Evaluate regression performance for total MMSE scores.

        Args:
            y_true: True MMSE scores
            y_pred: Predicted MMSE scores
            save_plots: Whether to save plots

        Returns:
            Comprehensive regression metrics
        """
        results = {}

        # Basic regression metrics
        results['rmse'] = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        results['mae'] = float(mean_absolute_error(y_true, y_pred))
        results['r2'] = float(r2_score(y_true, y_pred))

        # Correlation metrics
        pearson_corr, pearson_p = pearsonr(y_true, y_pred)
        spearman_corr, spearman_p = spearmanr(y_true, y_pred)

        results['pearson_correlation'] = float(pearson_corr)
        results['pearson_p_value'] = float(pearson_p)
        results['spearman_correlation'] = float(spearman_corr)
        results['spearman_p_value'] = float(spearman_p)

        # Intraclass Correlation Coefficient (ICC)
        icc_results = self._compute_icc(y_true, y_pred)
        results['icc'] = icc_results['icc']
        results['icc_95ci'] = icc_results['ci']

        # Bland-Altman analysis
        bland_altman = self._bland_altman_analysis(y_true, y_pred)
        results['bland_altman'] = bland_altman

        # Error distribution analysis
        errors = y_pred - y_true
        results['error_stats'] = {
            'mean_error': float(np.mean(errors)),
            'std_error': float(np.std(errors)),
            'median_error': float(np.median(errors)),
            'error_range': [float(np.min(errors)), float(np.max(errors))],
            'error_percentiles': [float(np.percentile(errors, p)) for p in [5, 25, 75, 95]]
        }

        # Clinical performance assessment
        results['clinical_targets'] = self._assess_clinical_targets(results)

        # Bootstrap confidence intervals
        bootstrap_results = self._bootstrap_confidence_intervals(y_true, y_pred, n_boot=1000)
        results['bootstrap_ci'] = bootstrap_results

        if save_plots:
            self._plot_regression_analysis(y_true, y_pred, results)

        logger.info("✅ Regression evaluation completed")
        logger.info(f"   RMSE: {results['rmse']:.3f}, MAE: {results['mae']:.3f}, R²: {results['r2']:.3f}")
        logger.info(f"   Pearson r: {results['pearson_correlation']:.3f}, ICC: {results['icc']:.3f}")

        return results

    def evaluate_classification_performance(self,
                                          y_true: np.ndarray,
                                          y_pred_proba: np.ndarray,
                                          threshold: float = 0.5,
                                          save_plots: bool = True) -> Dict[str, Any]:
        """
        Evaluate classification performance for cognitive impairment detection.

        Args:
            y_true: True binary labels (0=normal, 1=impaired)
            y_pred_proba: Predicted probabilities
            threshold: Classification threshold
            save_plots: Whether to save plots

        Returns:
            Comprehensive classification metrics
        """
        # Convert probabilities to binary predictions
        y_pred = (y_pred_proba >= threshold).astype(int)

        results = {}

        # Basic classification metrics
        results['accuracy'] = float(accuracy_score(y_true, y_pred))
        results['precision'] = float(precision_score(y_true, y_pred, zero_division=0))
        results['recall'] = float(recall_score(y_true, y_pred, zero_division=0))
        results['f1'] = float(f1_score(y_true, y_pred, zero_division=0))

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        results['confusion_matrix'] = cm.tolist()

        # Sensitivity and specificity
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            results['sensitivity'] = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            results['specificity'] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            results['npv'] = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0  # Negative predictive value
            results['ppv'] = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0  # Positive predictive value

        # AUC and ROC analysis
        if len(np.unique(y_true)) == 2:
            results['auc_roc'] = float(roc_auc_score(y_true, y_pred_proba))

            # ROC curve data
            fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
            results['roc_curve'] = {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'thresholds': thresholds.tolist()
            }

            # Precision-Recall curve
            precision_curve, recall_curve, pr_thresholds = precision_recall_curve(y_true, y_pred_proba)
            results['pr_curve'] = {
                'precision': precision_curve.tolist(),
                'recall': recall_curve.tolist(),
                'thresholds': pr_thresholds.tolist()
            }

        # Optimal threshold analysis
        optimal_threshold = self._find_optimal_threshold(y_true, y_pred_proba)
        results['optimal_threshold'] = optimal_threshold

        # Performance at optimal threshold
        y_pred_optimal = (y_pred_proba >= optimal_threshold).astype(int)
        results['performance_at_optimal'] = {
            'accuracy': float(accuracy_score(y_true, y_pred_optimal)),
            'sensitivity': float(recall_score(y_true, y_pred_optimal, zero_division=0)),
            'specificity': float(recall_score(1 - y_true, 1 - y_pred_optimal, zero_division=0)),
            'threshold': optimal_threshold
        }

        # Clinical targets assessment
        results['clinical_targets'] = self._assess_classification_targets(results)

        if save_plots:
            self._plot_classification_analysis(y_true, y_pred_proba, results)

        logger.info("✅ Classification evaluation completed")
        logger.info(f"   AUC: {results.get('auc_roc', 'N/A'):.3f}, F1: {results['f1']:.3f}")
        logger.info(f"   Sensitivity: {results.get('sensitivity', 'N/A'):.3f}, Specificity: {results.get('specificity', 'N/A'):.3f}")

        return results

    def evaluate_per_item_performance(self,
                                    item_predictions: Dict[int, np.ndarray],
                                    item_targets: Dict[int, np.ndarray],
                                    save_plots: bool = True) -> Dict[str, Any]:
        """
        Evaluate performance for each MMSE item individually.

        Args:
            item_predictions: Dict mapping item_id to predictions
            item_targets: Dict mapping item_id to true values
            save_plots: Whether to save plots

        Returns:
            Per-item performance analysis
        """
        results = {}

        for item_id in sorted(item_predictions.keys()):
            if item_id not in item_targets:
                continue

            y_pred = item_predictions[item_id]
            y_true = item_targets[item_id]

            # Determine if binary or ordinal classification
            unique_values = np.unique(y_true)
            is_binary = len(unique_values) == 2 and set(unique_values) <= {0, 1}

            if is_binary:
                # Binary classification metrics
                item_results = self.evaluate_classification_performance(y_true, y_pred, save_plots=False)
                item_results['type'] = 'binary'
            else:
                # Regression metrics for ordinal items
                item_results = self.evaluate_regression_performance(y_true, y_pred, save_plots=False)
                item_results['type'] = 'ordinal'

            results[item_id] = item_results

        # Overall item performance summary
        results['summary'] = self._compute_item_summary(results)

        if save_plots:
            self._plot_per_item_analysis(results)

        logger.info(f"✅ Per-item evaluation completed for {len(results)-1} items")

        return results

    def evaluate_fairness_analysis(self,
                                 predictions: np.ndarray,
                                 targets: np.ndarray,
                                 demographics: pd.DataFrame,
                                 protected_attributes: List[str] = ['age', 'sex', 'education'],
                                 save_plots: bool = True) -> Dict[str, Any]:
        """
        Evaluate fairness across demographic subgroups.

        Args:
            predictions: Model predictions
            targets: True values
            demographics: DataFrame with demographic information
            protected_attributes: List of attributes to analyze fairness for
            save_plots: Whether to save plots

        Returns:
            Fairness analysis results
        """
        results = {}

        for attribute in protected_attributes:
            if attribute not in demographics.columns:
                logger.warning(f"⚠️ Attribute '{attribute}' not found in demographics")
                continue

            fairness_results = self._analyze_attribute_fairness(
                predictions, targets, demographics[attribute], attribute
            )
            results[attribute] = fairness_results

        # Overall fairness assessment
        results['overall'] = self._compute_overall_fairness(results)

        if save_plots:
            self._plot_fairness_analysis(results)

        logger.info(f"✅ Fairness analysis completed for {len(results)-1} attributes")

        return results

    def _compute_icc(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Compute Intraclass Correlation Coefficient."""
        # Simplified ICC calculation (ICC(2,1) - absolute agreement)
        try:
            # Combine into single dataset for ICC calculation
            data = np.column_stack([y_true, y_pred])

            # Compute ICC using scipy
            icc_value = self._calculate_icc_scipy(data)

            # Bootstrap confidence interval
            icc_boot = []
            n_boot = 1000
            for _ in range(n_boot):
                indices = np.random.choice(len(data), len(data), replace=True)
                boot_data = data[indices]
                icc_boot.append(self._calculate_icc_scipy(boot_data))

            ci_lower = np.percentile(icc_boot, 2.5)
            ci_upper = np.percentile(icc_boot, 97.5)

            return {
                'icc': float(icc_value),
                'ci': [float(ci_lower), float(ci_upper)],
                'interpretation': self._interpret_icc(icc_value)
            }

        except Exception as e:
            logger.warning(f"⚠️ ICC calculation failed: {e}")
            return {'icc': 0.0, 'ci': [0.0, 0.0], 'interpretation': 'calculation_failed'}

    def _calculate_icc_scipy(self, data: np.ndarray) -> float:
        """Calculate ICC using scipy.stats."""
        # This is a simplified implementation
        # In practice, you'd use pingouin or other specialized libraries
        n_subjects, n_raters = data.shape

        # Compute means
        subject_means = np.mean(data, axis=1)
        rater_means = np.mean(data, axis=0)
        grand_mean = np.mean(data)

        # Compute sum of squares
        ss_subjects = n_raters * np.sum((subject_means - grand_mean) ** 2)
        ss_raters = n_subjects * np.sum((rater_means - grand_mean) ** 2)
        ss_residual = np.sum((data - subject_means[:, np.newaxis] - rater_means + grand_mean) ** 2)

        # Compute ICC
        n = n_subjects
        k = n_raters

        icc = (ss_subjects - ss_residual / (k - 1)) / (ss_subjects + ss_raters * (k - 1) + ss_residual)

        return max(0.0, min(1.0, icc))  # Clamp to [0, 1]

    def _bland_altman_analysis(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Perform Bland-Altman agreement analysis."""
        differences = y_pred - y_true
        means = (y_true + y_pred) / 2

        mean_diff = np.mean(differences)
        std_diff = np.std(differences)

        # 95% limits of agreement
        loa_lower = mean_diff - 1.96 * std_diff
        loa_upper = mean_diff + 1.96 * std_diff

        # Percentage of points within LOA
        within_loa = np.sum((differences >= loa_lower) & (differences <= loa_upper))
        percentage_within_loa = within_loa / len(differences) * 100

        return {
            'mean_difference': float(mean_diff),
            'std_difference': float(std_diff),
            'loa_lower': float(loa_lower),
            'loa_upper': float(loa_upper),
            'percentage_within_loa': float(percentage_within_loa),
            'agreement_interpretation': 'good' if percentage_within_loa >= 95 else 'moderate' if percentage_within_loa >= 90 else 'poor'
        }

    def _bootstrap_confidence_intervals(self, y_true: np.ndarray, y_pred: np.ndarray,
                                       n_boot: int = 1000) -> Dict[str, Any]:
        """Compute bootstrap confidence intervals for performance metrics."""
        metrics_boot = {
            'rmse': [],
            'mae': [],
            'r2': [],
            'pearson_r': []
        }

        n_samples = len(y_true)

        for _ in range(n_boot):
            # Bootstrap sample
            indices = np.random.choice(n_samples, n_samples, replace=True)
            y_true_boot = y_true[indices]
            y_pred_boot = y_pred[indices]

            # Compute metrics
            metrics_boot['rmse'].append(np.sqrt(mean_squared_error(y_true_boot, y_pred_boot)))
            metrics_boot['mae'].append(mean_absolute_error(y_true_boot, y_pred_boot))
            metrics_boot['r2'].append(r2_score(y_true_boot, y_pred_boot))

            try:
                pearson_r, _ = pearsonr(y_true_boot, y_pred_boot)
                metrics_boot['pearson_r'].append(pearson_r)
            except:
                metrics_boot['pearson_r'].append(0.0)

        # Compute confidence intervals
        ci_results = {}
        for metric, values in metrics_boot.items():
            values = np.array(values)
            ci_lower = np.percentile(values, 2.5)
            ci_upper = np.percentile(values, 97.5)
            ci_mean = np.mean(values)

            ci_results[metric] = {
                'mean': float(ci_mean),
                'ci_95': [float(ci_lower), float(ci_upper)],
                'ci_width': float(ci_upper - ci_lower)
            }

        return ci_results

    def _find_optimal_threshold(self, y_true: np.ndarray, y_pred_proba: np.ndarray) -> float:
        """Find optimal classification threshold using Youden's J statistic."""
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        return float(thresholds[optimal_idx])

    def _assess_clinical_targets(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess whether clinical performance targets are met."""
        targets_met = {}

        targets_met['rmse_target'] = results['rmse'] <= self.targets['rmse_max']
        targets_met['mae_target'] = results['mae'] <= self.targets['mae_max']
        targets_met['r2_target'] = results['r2'] >= self.targets['r2_min']
        targets_met['correlation_target'] = results['pearson_correlation'] >= self.targets['corr_min']

        overall_success = all(targets_met.values())

        return {
            'targets_met': targets_met,
            'overall_success': overall_success,
            'summary': f"{'✅' if overall_success else '❌'} {sum(targets_met.values())}/4 clinical targets met"
        }

    def _assess_classification_targets(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess classification performance targets."""
        targets_met = {}

        if 'sensitivity' in results:
            targets_met['sensitivity_target'] = results['sensitivity'] >= self.targets['sensitivity_min']
        if 'specificity' in results:
            targets_met['specificity_target'] = results['specificity'] >= self.targets['specificity_min']

        overall_success = all(targets_met.values()) if targets_met else False

        return {
            'targets_met': targets_met,
            'overall_success': overall_success,
            'summary': f"{'✅' if overall_success else '❌'} {sum(targets_met.values())}/2 classification targets met"
        }

    def _analyze_attribute_fairness(self, predictions: np.ndarray, targets: np.ndarray,
                                   attribute_values: pd.Series, attribute_name: str) -> Dict[str, Any]:
        """Analyze fairness for a specific demographic attribute."""
        results = {}

        # Define subgroups based on attribute
        if attribute_name == 'age':
            # Age groups: <65, 65-74, 75-84, ≥85
            bins = [0, 65, 75, 85, float('inf')]
            labels = ['<65', '65-74', '75-84', '≥85']
        elif attribute_name == 'education':
            # Education groups: ≤6y, 7-9y, 10-12y, >12y
            bins = [0, 6, 9, 12, float('inf')]
            labels = ['≤6y', '7-9y', '10-12y', '>12y']
        elif attribute_name == 'sex':
            # Binary attribute
            subgroups = attribute_values.unique()
            results_subgroups = {}

            for subgroup in subgroups:
                mask = attribute_values == subgroup
                if mask.sum() < 10:  # Skip small subgroups
                    continue

                subgroup_results = self.evaluate_regression_performance(
                    targets[mask], predictions[mask], save_plots=False
                )

                results_subgroups[str(subgroup)] = {
                    'n_samples': int(mask.sum()),
                    'mae': subgroup_results['mae'],
                    'rmse': subgroup_results['rmse'],
                    'r2': subgroup_results['r2'],
                    'pearson_r': subgroup_results['pearson_correlation']
                }

            results['subgroups'] = results_subgroups
            return results

        # For ordinal attributes
        attribute_binned = pd.cut(attribute_values, bins=bins, labels=labels, right=False)
        subgroups = attribute_binned.unique()

        results_subgroups = {}
        for subgroup in subgroups:
            if pd.isna(subgroup):
                continue

            mask = attribute_binned == subgroup
            if mask.sum() < 10:  # Skip small subgroups
                continue

            subgroup_results = self.evaluate_regression_performance(
                targets[mask], predictions[mask], save_plots=False
            )

            results_subgroups[str(subgroup)] = {
                'n_samples': int(mask.sum()),
                'mae': subgroup_results['mae'],
                'rmse': subgroup_results['rmse'],
                'r2': subgroup_results['r2'],
                'pearson_r': subgroup_results['pearson_correlation']
            }

        results['subgroups'] = results_subgroups

        # Fairness metrics
        if len(results_subgroups) > 1:
            mae_values = [sg['mae'] for sg in results_subgroups.values()]
            results['fairness_metrics'] = {
                'mae_range': float(max(mae_values) - min(mae_values)),
                'mae_std': float(np.std(mae_values)),
                'mae_cv': float(np.std(mae_values) / np.mean(mae_values)) if np.mean(mae_values) > 0 else 0.0,
                'max_disparity_group': max(results_subgroups.keys(), key=lambda k: results_subgroups[k]['mae'])
            }

        return results

    def _compute_overall_fairness(self, fairness_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute overall fairness assessment."""
        if not fairness_results:
            return {'fairness_assessment': 'insufficient_data'}

        # Collect disparity metrics across all attributes
        disparities = []
        for attr_results in fairness_results.values():
            if 'fairness_metrics' in attr_results:
                disparities.extend([
                    attr_results['fairness_metrics']['mae_range'],
                    attr_results['fairness_metrics']['mae_std']
                ])

        if disparities:
            max_disparity = max(disparities)
            mean_disparity = np.mean(disparities)

            # Fairness thresholds (configurable)
            if max_disparity <= 0.5:
                fairness_level = 'excellent'
            elif max_disparity <= 1.0:
                fairness_level = 'good'
            elif max_disparity <= 2.0:
                fairness_level = 'moderate'
            else:
                fairness_level = 'poor'

            return {
                'fairness_level': fairness_level,
                'max_disparity': float(max_disparity),
                'mean_disparity': float(mean_disparity),
                'assessment': f"{fairness_level.capitalize()} fairness (max disparity: {max_disparity:.2f})"
            }

        return {'fairness_assessment': 'incomplete_analysis'}

    def _plot_regression_analysis(self, y_true: np.ndarray, y_pred: np.ndarray,
                                results: Dict[str, Any]) -> None:
        """Create comprehensive regression analysis plots."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('MMSE Regression Performance Analysis', fontsize=16)

        # Scatter plot with regression line
        axes[0, 0].scatter(y_true, y_pred, alpha=0.6, s=30)
        axes[0, 0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()],
                       'r--', linewidth=2, label='Perfect prediction')
        axes[0, 0].set_xlabel('True MMSE Score')
        axes[0, 0].set_ylabel('Predicted MMSE Score')
        axes[0, 0].set_title('Predicted vs True MMSE Scores')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Bland-Altman plot
        differences = y_pred - y_true
        means = (y_true + y_pred) / 2
        mean_diff = np.mean(differences)
        std_diff = np.std(differences)

        axes[0, 1].scatter(means, differences, alpha=0.6, s=30)
        axes[0, 1].axhline(mean_diff, color='red', linestyle='-', linewidth=2,
                           label=f'Mean difference: {mean_diff:.2f}')
        axes[0, 1].axhline(mean_diff + 1.96*std_diff, color='orange', linestyle='--',
                           label=f'+1.96 SD: {mean_diff + 1.96*std_diff:.2f}')
        axes[0, 1].axhline(mean_diff - 1.96*std_diff, color='orange', linestyle='--',
                           label=f'-1.96 SD: {mean_diff - 1.96*std_diff:.2f}')
        axes[0, 1].set_xlabel('Mean of True and Predicted')
        axes[0, 1].set_ylabel('Difference (Predicted - True)')
        axes[0, 1].set_title('Bland-Altman Agreement Plot')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Error distribution
        errors = y_pred - y_true
        axes[1, 0].hist(errors, bins=30, alpha=0.7, edgecolor='black')
        axes[1, 0].axvline(np.mean(errors), color='red', linestyle='-', linewidth=2,
                          label=f'Mean: {np.mean(errors):.2f}')
        axes[1, 0].axvline(np.median(errors), color='orange', linestyle='--', linewidth=2,
                          label=f'Median: {np.median(errors):.2f}')
        axes[1, 0].set_xlabel('Prediction Error')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Error Distribution')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Performance metrics summary
        axes[1, 1].axis('off')
        metrics_text = ".3f"".3f"".3f"".3f"".3f"".3f"".3f"f"Targets: {'✅' if results['clinical_targets']['overall_success'] else '❌'} {sum(results['clinical_targets']['targets_met'].values())}/4 met"
        axes[1, 1].text(0.1, 0.8, metrics_text, fontsize=11, verticalalignment='top',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))

        plt.tight_layout()
        plt.savefig(self.output_dir / 'regression_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_classification_analysis(self, y_true: np.ndarray, y_pred_proba: np.ndarray,
                                    results: Dict[str, Any]) -> None:
        """Create classification analysis plots."""
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('MMSE Classification Performance Analysis', fontsize=16)

        # ROC Curve
        if 'roc_curve' in results:
            roc_data = results['roc_curve']
            axes[0].plot(roc_data['fpr'], roc_data['tpr'], linewidth=2,
                        label=f"AUC = {results.get('auc_roc', 0):.3f}")
            axes[0].plot([0, 1], [0, 1], 'r--', linewidth=1, label='Random classifier')
            axes[0].set_xlabel('False Positive Rate')
            axes[0].set_ylabel('True Positive Rate')
            axes[0].set_title('ROC Curve')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

        # Precision-Recall Curve
        if 'pr_curve' in results:
            pr_data = results['pr_curve']
            axes[1].plot(pr_data['recall'], pr_data['precision'], linewidth=2)
            axes[1].set_xlabel('Recall')
            axes[1].set_ylabel('Precision')
            axes[1].set_title('Precision-Recall Curve')
            axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'classification_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_per_item_analysis(self, item_results: Dict[str, Any]) -> None:
        """Create per-item performance plots."""
        summary = item_results.get('summary', {})
        if not summary:
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Per-Item MMSE Performance Analysis', fontsize=16)

        # Item-wise MAE
        items = list(summary.get('item_mae', {}).keys())
        mae_values = list(summary.get('item_mae', {}).values())
        axes[0, 0].bar(items, mae_values, alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel('MMSE Item ID')
        axes[0, 0].set_ylabel('MAE')
        axes[0, 0].set_title('Mean Absolute Error by Item')
        axes[0, 0].grid(True, alpha=0.3)

        # Item-wise R²
        r2_values = list(summary.get('item_r2', {}).values())
        axes[0, 1].bar(items, r2_values, alpha=0.7, edgecolor='black', color='green')
        axes[0, 1].set_xlabel('MMSE Item ID')
        axes[0, 1].set_ylabel('R² Score')
        axes[0, 1].set_title('R² Score by Item')
        axes[0, 1].grid(True, alpha=0.3)

        # Item difficulty analysis
        difficulty = summary.get('item_difficulty', {})
        if difficulty:
            diff_items = list(difficulty.keys())
            diff_scores = list(difficulty.values())
            axes[1, 0].bar(diff_items, diff_scores, alpha=0.7, edgecolor='black', color='orange')
            axes[1, 0].set_xlabel('MMSE Item ID')
            axes[1, 0].set_ylabel('Difficulty Score')
            axes[1, 0].set_title('Item Difficulty Analysis')
            axes[1, 0].grid(True, alpha=0.3)

        # Performance summary
        axes[1, 1].axis('off')
        summary_text = f"""Performance Summary:
Best performing item: {summary.get('best_item', 'N/A')}
Worst performing item: {summary.get('worst_item', 'N/A')}
Items with MAE < 0.5: {summary.get('high_accuracy_items', 0)}
Items with R² > 0.8: {summary.get('high_correlation_items', 0)}
"""
        axes[1, 1].text(0.1, 0.8, summary_text, fontsize=11, verticalalignment='top',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))

        plt.tight_layout()
        plt.savefig(self.output_dir / 'per_item_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_fairness_analysis(self, fairness_results: Dict[str, Any]) -> None:
        """Create fairness analysis plots."""
        overall = fairness_results.get('overall', {})
        if not overall:
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Fairness Analysis Across Demographic Groups', fontsize=16)

        # Plot fairness for each attribute
        attributes = [k for k in fairness_results.keys() if k != 'overall']
        colors = ['blue', 'green', 'red', 'orange']

        for i, attr in enumerate(attributes[:4]):  # Max 4 attributes
            ax = axes[i // 2, i % 2]

            attr_results = fairness_results[attr]
            subgroups = attr_results.get('subgroups', {})

            if subgroups:
                group_names = list(subgroups.keys())
                mae_values = [sg['mae'] for sg in subgroups.values()]

                ax.bar(group_names, mae_values, alpha=0.7, edgecolor='black',
                      color=colors[i % len(colors)])
                ax.set_xlabel(f'{attr.capitalize()} Groups')
                ax.set_ylabel('MAE')
                ax.set_title(f'Performance by {attr.capitalize()}')
                ax.grid(True, alpha=0.3)

                # Rotate x labels if needed
                if len(group_names) > 3:
                    ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'fairness_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def save_evaluation_report(self, results: Dict[str, Any], filename: str = 'evaluation_report.json') -> None:
        """Save comprehensive evaluation report."""
        # Convert numpy types to native Python types
        def make_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            else:
                return obj

        serializable_results = make_serializable(results)

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Evaluation report saved to {output_path}")

    def _compute_item_summary(self, item_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary statistics for per-item performance."""
        summary = {}

        # Extract item metrics
        item_mae = {}
        item_r2 = {}
        item_corr = {}

        for item_id, results in item_results.items():
            if isinstance(item_id, int):  # Skip 'summary' key
                item_mae[item_id] = results.get('mae', 0)
                item_r2[item_id] = results.get('r2', 0)
                item_corr[item_id] = results.get('pearson_correlation', 0)

        summary['item_mae'] = item_mae
        summary['item_r2'] = item_r2
        summary['item_correlation'] = item_corr

        # Best and worst performing items
        if item_mae:
            summary['best_item'] = min(item_mae.keys(), key=lambda k: item_mae[k])
            summary['worst_item'] = max(item_mae.keys(), key=lambda k: item_mae[k])

        # Performance thresholds
        summary['high_accuracy_items'] = sum(1 for mae in item_mae.values() if mae < 0.5)
        summary['high_correlation_items'] = sum(1 for r2 in item_r2.values() if r2 > 0.8)

        # Item difficulty (based on MAE - higher MAE = more difficult)
        if item_mae:
            max_mae = max(item_mae.values())
            min_mae = min(item_mae.values())
            if max_mae > min_mae:
                summary['item_difficulty'] = {
                    item_id: (mae - min_mae) / (max_mae - min_mae)
                    for item_id, mae in item_mae.items()
                }

        return summary

    def _interpret_icc(self, icc_value: float) -> str:
        """Interpret ICC value according to clinical standards."""
        if icc_value >= 0.9:
            return "excellent"
        elif icc_value >= 0.75:
            return "good"
        elif icc_value >= 0.5:
            return "moderate"
        else:
            return "poor"


if __name__ == "__main__":
    # Test the evaluator
    print("🧪 Testing MMSE Evaluator...")

    evaluator = MMSEEvaluator()

    # Generate synthetic data
    np.random.seed(42)
    n_samples = 200

    # True MMSE scores (18-30 range)
    y_true = np.random.uniform(18, 30, n_samples)

    # Simulated predictions with realistic error
    error = np.random.normal(0, 2, n_samples)  # Mean error 0, std 2
    y_pred = y_true + error
    y_pred = np.clip(y_pred, 0, 30)  # Clip to valid range

    # Binary classification for impairment detection
    impairment_threshold = 24
    y_true_binary = (y_true < impairment_threshold).astype(int)
    y_pred_proba = 1 / (1 + np.exp(-(y_true - impairment_threshold) / 2))  # Sigmoid probabilities

    print("📊 Testing regression evaluation...")
    reg_results = evaluator.evaluate_regression_performance(y_true, y_pred, save_plots=False)
    print(f"   RMSE: {reg_results['rmse']:.3f}, MAE: {reg_results['mae']:.3f}, R²: {reg_results['r2']:.3f}")
    print(f"   Pearson r: {reg_results['pearson_correlation']:.3f}, ICC: {reg_results['icc']:.3f}")

    print("\n📊 Testing classification evaluation...")
    clf_results = evaluator.evaluate_classification_performance(y_true_binary, y_pred_proba, save_plots=False)
    print(f"   AUC: {clf_results.get('auc_roc', 'N/A'):.3f}, F1: {clf_results['f1']:.3f}")
    print(f"   Sensitivity: {clf_results.get('sensitivity', 'N/A'):.3f}, Specificity: {clf_results.get('specificity', 'N/A'):.3f}")

    print("\n✅ MMSE Evaluator test completed!")
