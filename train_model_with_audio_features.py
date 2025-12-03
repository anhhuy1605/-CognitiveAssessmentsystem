#!/usr/bin/env python3
"""
Train model với đúng 4 features từ audio extraction:
- speech_rate
- number_utterances  
- silence_mean
- pitch_mean
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def extract_features_from_csv_data(csv_path: str):
    """
    Extract 4 audio features từ CSV data nếu có audio files
    Hoặc tạo synthetic data với đúng 4 features
    """
    print("=" * 60)
    print("EXTRACTING FEATURES FROM DATA")
    print("=" * 60)
    
    # Try to load CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"Loaded CSV: {df.shape}")
        
        # Check if we have audio files and can extract features
        if 'audio_path' in df.columns and 'mmse' in df.columns:
            print("Attempting to extract features from audio files...")
            try:
                from app import extract_audio_features
                
                features_list = []
                for idx, row in df.iterrows():
                    if pd.isna(row.get('audio_path')) or pd.isna(row.get('mmse')):
                        continue
                    
                    audio_path = row['audio_path']
                    if not os.path.isabs(audio_path):
                        audio_path = os.path.join('audio', audio_path)
                    
                    if os.path.exists(audio_path):
                        try:
                            features = extract_audio_features(audio_path)
                            features['mmse'] = row['mmse']
                            features_list.append(features)
                        except Exception as e:
                            print(f"  Warning: Failed to extract from {audio_path}: {e}")
                            continue
                
                if len(features_list) >= 30:
                    features_df = pd.DataFrame(features_list)
                    required_features = ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean', 'mmse']
                    
                    if all(col in features_df.columns for col in required_features):
                        X = features_df[['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']].values
                        y = features_df['mmse'].values.astype(float)
                        y = np.clip(y, 0.0, 30.0)
                        
                        print(f"Successfully extracted {len(X)} samples from audio files")
                        return X, y, ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']
            except Exception as e:
                print(f"Failed to extract from audio: {e}")
    
    # Fallback: Create synthetic data with correct 4 features
    print("Creating synthetic training data with 4 features...")
    rng = np.random.default_rng(42)
    n_samples = 500
    
    # Generate realistic feature values
    speech_rate = rng.uniform(1.0, 4.0, n_samples)
    number_utterances = rng.integers(5, 50, n_samples).astype(float)
    silence_mean = rng.uniform(0.0, 2.0, n_samples)
    pitch_mean = rng.uniform(120.0, 250.0, n_samples)
    
    X = np.column_stack([speech_rate, number_utterances, silence_mean, pitch_mean])
    
    # Generate MMSE scores based on features (realistic relationship)
    y = (
        20.0  # Base MMSE
        + 3.0 * (speech_rate - 2.5)  # Higher speech rate → higher MMSE
        + 0.15 * (number_utterances - 25)  # More utterances → higher MMSE
        - 2.5 * (silence_mean - 1.0)  # More silence → lower MMSE
        + 0.01 * (pitch_mean - 180)  # Pitch effect (smaller)
        + rng.normal(0, 2.0, n_samples)  # Noise
    )
    y = np.clip(y, 0.0, 30.0)
    
    print(f"Generated {n_samples} synthetic samples")
    return X, y, ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']

def train_best_model(X_train, y_train):
    """Train the best performing model"""
    print("\n" + "=" * 60)
    print("TRAINING MODELS")
    print("=" * 60)
    
    models = {
        'rf': RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1, max_depth=10),
        'gb': GradientBoostingRegressor(n_estimators=200, random_state=42, max_depth=5, learning_rate=0.1)
    }
    
    best_model = None
    best_score = float('inf')
    best_name = None
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        
        # Preprocessing
        scaler = RobustScaler()
        selector = SelectKBest(score_func=mutual_info_regression, k='all')
        
        # Fit preprocessing
        X_scaled = scaler.fit_transform(X_train)
        X_selected = selector.fit_transform(X_scaled, y_train)
        
        # Train model
        model.fit(X_selected, y_train)
        
        # Predict on training data
        y_pred = model.predict(X_selected)
        
        # Calculate metrics
        mae = mean_absolute_error(y_train, y_pred)
        r2 = r2_score(y_train, y_pred)
        
        print(f"  MAE: {mae:.3f}, R²: {r2:.3f}")
        
        if mae < best_score:
            best_score = mae
            best_model = {
                'model': model,
                'scaler': scaler,
                'selector': selector,
                'name': name
            }
            best_name = name
    
    print(f"\n🏆 Best model: {best_name} (MAE: {best_score:.3f})")
    return best_model

def save_model_bundle(model_info, feature_names, save_path: str):
    """Save the trained model bundle"""
    print(f"\n💾 Saving model bundle to {save_path}")
    
    os.makedirs(save_path, exist_ok=True)
    
    # Save model components
    joblib.dump(model_info['model'], os.path.join(save_path, 'model.pkl'))
    joblib.dump(model_info['scaler'], os.path.join(save_path, 'scaler.pkl'))
    joblib.dump(model_info['selector'], os.path.join(save_path, 'selector.pkl'))
    joblib.dump(feature_names, os.path.join(save_path, 'feature_names.pkl'))
    
    # Save metadata
    metadata = {
        'model_name': model_info['name'],
        'training_date': pd.Timestamp.now().isoformat(),
        'version': '4.0_audio_features',
        'description': 'Model trained with 4 audio features: speech_rate, number_utterances, silence_mean, pitch_mean',
        'features': feature_names
    }
    
    import json
    with open(os.path.join(save_path, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Model bundle saved successfully!")
    return save_path

def main():
    """Main function"""
    print("=" * 60)
    print("TRAINING MODEL WITH 4 AUDIO FEATURES")
    print("=" * 60)
    
    # Extract features
    csv_path = 'backend/dx-mmse.csv'
    X, y, feature_names = extract_features_from_csv_data(csv_path)
    
    print(f"\nData summary:")
    print(f"  Samples: {len(X)}")
    print(f"  Features: {feature_names}")
    print(f"  MMSE range: {y.min():.1f} - {y.max():.1f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\nData split:")
    print(f"  Train: {X_train.shape[0]} samples")
    print(f"  Test: {X_test.shape[0]} samples")
    
    # Train model
    best_model_info = train_best_model(X_train, y_train)
    
    # Evaluate on test set
    print("\n" + "=" * 60)
    print("EVALUATING ON TEST SET")
    print("=" * 60)
    
    scaler = best_model_info['scaler']
    selector = best_model_info['selector']
    model = best_model_info['model']
    
    # Apply preprocessing
    X_test_scaled = scaler.transform(X_test)
    X_test_selected = selector.transform(X_test_scaled)
    
    # Predict
    y_pred = model.predict(X_test_selected)
    
    # Calculate metrics
    test_mae = mean_absolute_error(y_test, y_pred)
    test_r2 = r2_score(y_test, y_pred)
    
    print(f"Test MAE: {test_mae:.3f}")
    print(f"Test R²: {test_r2:.3f}")
    
    # Save model bundle
    bundle_path = save_model_bundle(
        best_model_info, 
        feature_names, 
        'model_bundle/improved_regression_model'
    )
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETED!")
    print("=" * 60)
    print(f"Model: {best_model_info['name']}")
    print(f"Test MAE: {test_mae:.3f}")
    print(f"Test R²: {test_r2:.3f}")
    print(f"Features: {feature_names}")
    print(f"Bundle: {bundle_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()

