# -*- coding: utf-8 -*-
"""
Training Script for Multimodal MCI Fusion Model

This script:
1. Loads labeled dataset (audio + transcripts + MMSE/MCI labels)
2. Extracts acoustic and linguistic features
3. Trains multimodal fusion model
4. Evaluates performance
5. Saves trained model

Author: Cognitive Assessment System
Version: 1.0
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from modules.acoustic_analyzer import AcousticAnalyzer
    from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
    from modules.multimodal_fusion import MultimodalFusion, FusionConfig
    from modules.mci_predictor import MCIPredictor
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False

# Import sklearn
try:
    from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
    from sklearn.metrics import (
        accuracy_score, roc_auc_score, confusion_matrix, 
        classification_report, mean_squared_error, mean_absolute_error,
        precision_recall_fscore_support
    )
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.error("sklearn not available. Please install: pip install scikit-learn")


class DatasetLoader:
    """Load and prepare training dataset"""
    
    def __init__(self, data_folder: str):
        """
        Initialize dataset loader
        
        Expected folder structure:
        data_folder/
            audio/
                participant001.wav
                participant002.wav
                ...
            labels.csv
        
        labels.csv columns:
            participant_id, mmse_score, mci_label, transcript, [task_type]
        """
        self.data_folder = Path(data_folder)
        self.audio_folder = self.data_folder / 'audio'
        self.labels_file = self.data_folder / 'labels.csv'
        
        # Validate
        if not self.data_folder.exists():
            raise FileNotFoundError(f"Data folder not found: {data_folder}")
        if not self.labels_file.exists():
            raise FileNotFoundError(f"Labels file not found: {self.labels_file}")
    
    def load_labels(self) -> pd.DataFrame:
        """Load labels from CSV"""
        df = pd.read_csv(self.labels_file)
        
        # Validate required columns
        required_cols = ['participant_id', 'mmse_score', 'mci_label', 'transcript']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        logger.info(f"Loaded {len(df)} samples from labels.csv")
        logger.info(f"MCI distribution: {df['mci_label'].value_counts().to_dict()}")
        logger.info(f"MMSE range: {df['mmse_score'].min():.1f} - {df['mmse_score'].max():.1f}")
        
        return df
    
    def get_audio_path(self, participant_id: str) -> str:
        """Get audio file path for participant"""
        # Try different extensions
        for ext in ['.wav', '.mp3', '.m4a', '.flac']:
            path = self.audio_folder / f"{participant_id}{ext}"
            if path.exists():
                return str(path)
        
        raise FileNotFoundError(f"Audio file not found for: {participant_id}")


def extract_features(data_folder: str, 
                     output_file: Optional[str] = None,
                     use_phobert: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Extract acoustic and linguistic features from dataset
    
    Args:
        data_folder: Path to data folder
        output_file: Optional path to save extracted features
        use_phobert: Whether to use PhoBERT
    
    Returns:
        Tuple of (acoustic_df, linguistic_df, mmse_labels, mci_labels)
    """
    logger.info("="*60)
    logger.info("FEATURE EXTRACTION")
    logger.info("="*60)
    
    # Load dataset
    loader = DatasetLoader(data_folder)
    labels_df = loader.load_labels()
    
    # Initialize analyzers
    acoustic_analyzer = AcousticAnalyzer()
    linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=use_phobert)
    
    acoustic_features_list = []
    linguistic_features_list = []
    valid_indices = []
    
    for idx, row in labels_df.iterrows():
        participant_id = row['participant_id']
        transcript = row['transcript']
        task_type = row.get('task_type', None)
        
        logger.info(f"Processing {idx+1}/{len(labels_df)}: {participant_id}")
        
        try:
            # Get audio path
            audio_path = loader.get_audio_path(participant_id)
            
            # Extract acoustic features
            acoustic_feat = acoustic_analyzer.extract_all_features(audio_path, transcript)
            
            # Extract linguistic features
            linguistic_feat = linguistic_analyzer.extract_all_features(transcript, task_type)
            
            acoustic_features_list.append(acoustic_feat)
            linguistic_features_list.append(linguistic_feat)
            valid_indices.append(idx)
            
        except Exception as e:
            logger.error(f"Error processing {participant_id}: {e}")
            continue
    
    # Filter labels to valid indices
    labels_df = labels_df.iloc[valid_indices].reset_index(drop=True)
    
    # Convert to DataFrames
    acoustic_df = pd.DataFrame(acoustic_features_list)
    linguistic_df = pd.DataFrame(linguistic_features_list)
    
    # Handle NaN and inf values
    acoustic_df = acoustic_df.replace([np.inf, -np.inf], np.nan)
    acoustic_df = acoustic_df.fillna(0)
    
    linguistic_df = linguistic_df.replace([np.inf, -np.inf], np.nan)
    linguistic_df = linguistic_df.fillna(0)
    
    logger.info(f"\nExtraction complete:")
    logger.info(f"  Valid samples: {len(acoustic_df)}")
    logger.info(f"  Acoustic features: {len(acoustic_df.columns)}")
    logger.info(f"  Linguistic features: {len(linguistic_df.columns)}")
    
    # Save if output file specified
    if output_file:
        output_data = {
            'acoustic': acoustic_df.to_dict('records'),
            'linguistic': linguistic_df.to_dict('records'),
            'labels': labels_df.to_dict('records')
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Features saved to {output_file}")
    
    return (acoustic_df, linguistic_df, 
            labels_df['mmse_score'].values, 
            labels_df['mci_label'].values)


def train_and_evaluate(acoustic_features: pd.DataFrame,
                       linguistic_features: pd.DataFrame,
                       mmse_labels: np.ndarray,
                       mci_labels: np.ndarray,
                       test_size: float = 0.2,
                       n_folds: int = 5) -> Dict[str, Any]:
    """
    Train and evaluate multimodal fusion model
    
    Args:
        acoustic_features: DataFrame of acoustic features
        linguistic_features: DataFrame of linguistic features
        mmse_labels: MMSE scores (0-30)
        mci_labels: MCI labels (0=healthy, 1=MCI)
        test_size: Test set proportion
        n_folds: Number of cross-validation folds
    
    Returns:
        dict: Training results and metrics
    """
    logger.info("="*60)
    logger.info("MODEL TRAINING AND EVALUATION")
    logger.info("="*60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_samples': len(mmse_labels),
        'n_acoustic_features': len(acoustic_features.columns),
        'n_linguistic_features': len(linguistic_features.columns),
        'metrics': {}
    }
    
    # Combine features for unified model
    combined_features = pd.concat([acoustic_features, linguistic_features], axis=1)
    
    # Handle duplicate column names
    combined_features.columns = [f"{col}_{i}" if combined_features.columns.tolist().count(col) > 1 
                                  else col for i, col in enumerate(combined_features.columns)]
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(combined_features)
    
    # Split data
    X_train, X_test, y_mmse_train, y_mmse_test, y_mci_train, y_mci_test = train_test_split(
        X_scaled, mmse_labels, mci_labels,
        test_size=test_size,
        random_state=42,
        stratify=mci_labels
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    logger.info(f"Features: {X_scaled.shape[1]}")
    
    # =========================================================================
    # MCI Classification
    # =========================================================================
    logger.info("\n--- MCI Classification ---")
    
    # Train classifier
    classifier = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42
    )
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(classifier, X_train, y_mci_train, cv=cv, scoring='accuracy')
    cv_auc_scores = cross_val_score(classifier, X_train, y_mci_train, cv=cv, scoring='roc_auc')
    
    logger.info(f"Cross-validation Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    logger.info(f"Cross-validation AUC: {cv_auc_scores.mean():.3f} (+/- {cv_auc_scores.std():.3f})")
    
    # Train on full training set
    classifier.fit(X_train, y_mci_train)
    
    # Test set evaluation
    y_pred_mci = classifier.predict(X_test)
    y_pred_proba = classifier.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_mci_test, y_pred_mci)
    auc = roc_auc_score(y_mci_test, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_mci_test, y_pred_mci)
    tn, fp, fn, tp = cm.ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    logger.info(f"\nTest Set Results:")
    logger.info(f"  Accuracy: {accuracy:.3f}")
    logger.info(f"  AUC: {auc:.3f}")
    logger.info(f"  Sensitivity: {sensitivity:.3f}")
    logger.info(f"  Specificity: {specificity:.3f}")
    logger.info(f"  PPV: {ppv:.3f}")
    logger.info(f"  NPV: {npv:.3f}")
    
    results['metrics']['classification'] = {
        'cv_accuracy': float(cv_scores.mean()),
        'cv_accuracy_std': float(cv_scores.std()),
        'cv_auc': float(cv_auc_scores.mean()),
        'cv_auc_std': float(cv_auc_scores.std()),
        'test_accuracy': float(accuracy),
        'test_auc': float(auc),
        'sensitivity': float(sensitivity),
        'specificity': float(specificity),
        'ppv': float(ppv),
        'npv': float(npv),
        'confusion_matrix': cm.tolist()
    }
    
    # =========================================================================
    # MMSE Regression
    # =========================================================================
    logger.info("\n--- MMSE Regression ---")
    
    regressor = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42
    )
    
    # Cross-validation
    cv_rmse = cross_val_score(regressor, X_train, y_mmse_train, cv=cv, 
                              scoring='neg_root_mean_squared_error')
    cv_mae = cross_val_score(regressor, X_train, y_mmse_train, cv=cv,
                             scoring='neg_mean_absolute_error')
    
    logger.info(f"Cross-validation RMSE: {-cv_rmse.mean():.3f} (+/- {cv_rmse.std():.3f})")
    logger.info(f"Cross-validation MAE: {-cv_mae.mean():.3f} (+/- {cv_mae.std():.3f})")
    
    # Train on full training set
    regressor.fit(X_train, y_mmse_train)
    
    # Test set evaluation
    y_pred_mmse = regressor.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_mmse_test, y_pred_mmse))
    mae = mean_absolute_error(y_mmse_test, y_pred_mmse)
    
    # Correlation
    correlation = np.corrcoef(y_mmse_test, y_pred_mmse)[0, 1]
    
    logger.info(f"\nTest Set Results:")
    logger.info(f"  RMSE: {rmse:.3f}")
    logger.info(f"  MAE: {mae:.3f}")
    logger.info(f"  Correlation: {correlation:.3f}")
    
    results['metrics']['regression'] = {
        'cv_rmse': float(-cv_rmse.mean()),
        'cv_rmse_std': float(cv_rmse.std()),
        'cv_mae': float(-cv_mae.mean()),
        'cv_mae_std': float(cv_mae.std()),
        'test_rmse': float(rmse),
        'test_mae': float(mae),
        'correlation': float(correlation)
    }
    
    # =========================================================================
    # Feature Importance
    # =========================================================================
    logger.info("\n--- Feature Importance (Top 20) ---")
    
    feature_importance = pd.DataFrame({
        'feature': combined_features.columns,
        'importance': classifier.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in feature_importance.head(20).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    results['feature_importance'] = feature_importance.head(50).to_dict('records')
    
    # Store models
    results['models'] = {
        'classifier': classifier,
        'regressor': regressor,
        'scaler': scaler,
        'feature_columns': combined_features.columns.tolist()
    }
    
    return results


def save_model(results: Dict[str, Any], output_dir: str):
    """
    Save trained model and results
    
    Args:
        results: Training results dict
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_data = {
        'classifier': results['models']['classifier'],
        'regressor': results['models']['regressor'],
        'scaler': results['models']['scaler'],
        'feature_columns': results['models']['feature_columns']
    }
    
    model_path = output_dir / 'mci_fusion_model.pkl'
    joblib.dump(model_data, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics_data = {
        'timestamp': results['timestamp'],
        'n_samples': results['n_samples'],
        'n_acoustic_features': results['n_acoustic_features'],
        'n_linguistic_features': results['n_linguistic_features'],
        'metrics': results['metrics'],
        'feature_importance': results.get('feature_importance', [])
    }
    
    metrics_path = output_dir / 'training_metrics.json'
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train MCI Screening Model')
    parser.add_argument('--data-folder', type=str, required=True,
                        help='Path to data folder with audio/ and labels.csv')
    parser.add_argument('--output-dir', type=str, default='models',
                        help='Output directory for trained model')
    parser.add_argument('--features-file', type=str, default=None,
                        help='Path to save/load extracted features')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Test set proportion')
    parser.add_argument('--n-folds', type=int, default=5,
                        help='Number of cross-validation folds')
    parser.add_argument('--no-phobert', action='store_true',
                        help='Disable PhoBERT for faster processing')
    
    args = parser.parse_args()
    
    if not MODULES_AVAILABLE:
        logger.error("Required modules not available. Please install dependencies.")
        sys.exit(1)
    
    if not SKLEARN_AVAILABLE:
        logger.error("sklearn not available. Please install: pip install scikit-learn")
        sys.exit(1)
    
    # Extract features
    logger.info("Starting feature extraction...")
    acoustic_df, linguistic_df, mmse_labels, mci_labels = extract_features(
        args.data_folder,
        output_file=args.features_file,
        use_phobert=not args.no_phobert
    )
    
    # Train and evaluate
    logger.info("\nStarting model training...")
    results = train_and_evaluate(
        acoustic_df, linguistic_df,
        mmse_labels, mci_labels,
        test_size=args.test_size,
        n_folds=args.n_folds
    )
    
    # Save model
    save_model(results, args.output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Samples: {results['n_samples']}")
    print(f"Features: {results['n_acoustic_features']} acoustic + {results['n_linguistic_features']} linguistic")
    print(f"\nMCI Classification:")
    print(f"  Test Accuracy: {results['metrics']['classification']['test_accuracy']:.1%}")
    print(f"  Test AUC: {results['metrics']['classification']['test_auc']:.3f}")
    print(f"  Sensitivity: {results['metrics']['classification']['sensitivity']:.1%}")
    print(f"  Specificity: {results['metrics']['classification']['specificity']:.1%}")
    print(f"\nMMSE Regression:")
    print(f"  Test RMSE: {results['metrics']['regression']['test_rmse']:.2f}")
    print(f"  Test MAE: {results['metrics']['regression']['test_mae']:.2f}")
    print(f"  Correlation: {results['metrics']['regression']['correlation']:.3f}")
    print(f"\nModel saved to: {args.output_dir}/mci_fusion_model.pkl")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

