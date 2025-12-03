#!/usr/bin/env python3
"""
Script để validate training data trước khi train model
"""

import os
import sys
import pandas as pd
from pathlib import Path

def validate_dataset(csv_path: str, audio_dir: str = 'audio', check_audio: bool = True):
    """
    Validate dataset trước khi train
    
    Args:
        csv_path: Path to CSV file
        audio_dir: Directory chứa audio files
        check_audio: Whether to check audio files exist
    """
    print("=" * 60)
    print("VALIDATING TRAINING DATASET")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check CSV exists
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        return False
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"ERROR: Cannot read CSV file: {e}")
        return False
    
    # Check required columns
    required_cols = ['session_id', 'mmse']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check MMSE column
    if 'mmse' in df.columns:
        # Check for missing values
        missing_mmse = df['mmse'].isna().sum()
        if missing_mmse > 0:
            errors.append(f"Missing MMSE scores: {missing_mmse} rows")
        
        # Check range
        invalid_mmse = df[(df['mmse'] < 0) | (df['mmse'] > 30)]
        if len(invalid_mmse) > 0:
            errors.append(f"Invalid MMSE scores (not in 0-30): {len(invalid_mmse)} rows")
            print(f"  Invalid MMSE values: {invalid_mmse['mmse'].tolist()}")
        
        # Check data type
        if not pd.api.types.is_numeric_dtype(df['mmse']):
            errors.append("MMSE column must be numeric")
        
        # Check distribution
        normal = len(df[(df['mmse'] >= 24) & (df['mmse'] <= 30)])
        mci = len(df[(df['mmse'] >= 18) & (df['mmse'] < 24)])
        dementia = len(df[df['mmse'] < 18])
        
        print(f"\nMMSE Distribution:")
        print(f"  Normal (24-30): {normal} ({normal/len(df)*100:.1f}%)")
        print(f"  MCI (18-23): {mci} ({mci/len(df)*100:.1f}%)")
        print(f"  Dementia (0-17): {dementia} ({dementia/len(df)*100:.1f}%)")
        
        # Warning if unbalanced
        if normal < len(df) * 0.2 or dementia < len(df) * 0.1:
            warnings.append("MMSE distribution may be unbalanced")
    
    # Check if features already extracted
    feature_cols = ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']
    has_features = all(col in df.columns for col in feature_cols)
    
    if has_features:
        print(f"\nFeatures already extracted in CSV:")
        for col in feature_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    warnings.append(f"Missing values in {col}: {missing} rows")
                else:
                    print(f"  {col}: OK (range: {df[col].min():.2f} - {df[col].max():.2f})")
    else:
        print(f"\nFeatures not extracted yet - will need to extract from audio")
        if 'audio_path' not in df.columns:
            errors.append("Need 'audio_path' column to extract features from audio")
    
    # Check audio files if needed
    if check_audio and 'audio_path' in df.columns:
        print(f"\nChecking audio files...")
        missing_files = []
        for idx, row in df.iterrows():
            audio_path = row['audio_path']
            if pd.isna(audio_path):
                missing_files.append(f"Row {idx+1}: audio_path is NaN")
                continue
            
            if os.path.isabs(audio_path):
                full_path = audio_path
            else:
                full_path = os.path.join(audio_dir, audio_path)
            
            if not os.path.exists(full_path):
                missing_files.append(f"Row {idx+1}: {audio_path}")
        
        if missing_files:
            errors.append(f"Missing audio files: {len(missing_files)} files")
            print(f"  First 5 missing files:")
            for f in missing_files[:5]:
                print(f"    - {f}")
            if len(missing_files) > 5:
                print(f"    ... and {len(missing_files) - 5} more")
    
    # Check minimum sample size
    if len(df) < 50:
        warnings.append(f"Dataset size ({len(df)}) is below recommended minimum (50)")
    elif len(df) < 200:
        warnings.append(f"Dataset size ({len(df)}) is below recommended (200+)")
    
    # Check for duplicates
    if 'session_id' in df.columns:
        duplicates = df['session_id'].duplicated().sum()
        if duplicates > 0:
            errors.append(f"Duplicate session_id: {duplicates} rows")
    
    # Report results
    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        print("=" * 60)
        print("ERRORS:")
        for e in errors:
            print(f"  ❌ {e}")
        return False
    else:
        print("VALIDATION PASSED")
        print("=" * 60)
        if warnings:
            print("WARNINGS:")
            for w in warnings:
                print(f"  ⚠️ {w}")
        else:
            print("✅ No issues found!")
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate training dataset')
    parser.add_argument('--csv', type=str, default='data.csv',
                       help='Path to CSV file')
    parser.add_argument('--audio-dir', type=str, default='audio',
                       help='Directory containing audio files')
    parser.add_argument('--no-audio-check', action='store_true',
                       help='Skip audio file existence check')
    
    args = parser.parse_args()
    
    success = validate_dataset(args.csv, args.audio_dir, check_audio=not args.no_audio_check)
    sys.exit(0 if success else 1)

