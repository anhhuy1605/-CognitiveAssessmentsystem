#!/usr/bin/env python3
"""
Script để extract features từ audio files cho training data
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

try:
    from app import extract_audio_features
    import numpy as np
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

def extract_features_batch(csv_path: str, audio_dir: str = 'audio', output_path: str = 'extracted_features.csv'):
    """
    Extract features từ audio files trong CSV
    
    Args:
        csv_path: Path to CSV file với columns: session_id, audio_path, mmse
        audio_dir: Directory chứa audio files
        output_path: Path để save extracted features CSV
    """
    print("=" * 60)
    print("EXTRACTING FEATURES FROM AUDIO FILES")
    print("=" * 60)
    
    # Load CSV
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"Loaded CSV: {len(df)} rows")
    
    # Check required columns
    required_cols = ['session_id', 'audio_path', 'mmse']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return None
    
    # Extract features
    features_list = []
    errors = []
    
    for idx, row in df.iterrows():
        session_id = row['session_id']
        audio_path = row['audio_path']
        mmse = row['mmse']
        
        # Build full path
        if os.path.isabs(audio_path):
            full_audio_path = audio_path
        else:
            full_audio_path = os.path.join(audio_dir, audio_path)
        
        print(f"\n[{idx+1}/{len(df)}] Processing: {session_id}")
        print(f"  Audio: {full_audio_path}")
        
        # Check file exists
        if not os.path.exists(full_audio_path):
            error_msg = f"Audio file not found: {full_audio_path}"
            print(f"  ERROR: {error_msg}")
            errors.append({'session_id': session_id, 'error': error_msg})
            continue
        
        # Extract features
        try:
            features = extract_audio_features(full_audio_path)
            
            # Prepare output row
            output_row = {
                'session_id': session_id,
                'speech_rate': features.get('speech_rate', 0.0),
                'number_utterances': features.get('number_utterances', 0),
                'silence_mean': features.get('silence_mean', 0.0),
                'pitch_mean': features.get('pitch_mean', 0.0),
                'mmse': mmse
            }
            
            # Add optional metadata if available
            if 'age' in df.columns:
                output_row['age'] = row.get('age', None)
            if 'gender' in df.columns:
                output_row['gender'] = row.get('gender', None)
            if 'education_years' in df.columns:
                output_row['education_years'] = row.get('education_years', None)
            if 'region' in df.columns:
                output_row['region'] = row.get('region', None)
            
            features_list.append(output_row)
            
            print(f"  SUCCESS: speech_rate={output_row['speech_rate']:.2f}, "
                  f"utterances={output_row['number_utterances']}, "
                  f"silence={output_row['silence_mean']:.2f}, "
                  f"pitch={output_row['pitch_mean']:.1f}")
            
        except Exception as e:
            error_msg = f"Error extracting features: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append({'session_id': session_id, 'error': error_msg})
    
    # Create output DataFrame
    if not features_list:
        print("\nERROR: No features extracted successfully!")
        return None
    
    output_df = pd.DataFrame(features_list)
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Successfully extracted: {len(features_list)}/{len(df)} samples")
    print(f"Output saved to: {output_path}")
    
    # Show summary
    print("\nFeature Summary:")
    print(f"  speech_rate: {output_df['speech_rate'].min():.2f} - {output_df['speech_rate'].max():.2f} (mean: {output_df['speech_rate'].mean():.2f})")
    print(f"  number_utterances: {output_df['number_utterances'].min()} - {output_df['number_utterances'].max()} (mean: {output_df['number_utterances'].mean():.1f})")
    print(f"  silence_mean: {output_df['silence_mean'].min():.2f} - {output_df['silence_mean'].max():.2f} (mean: {output_df['silence_mean'].mean():.2f})")
    print(f"  pitch_mean: {output_df['pitch_mean'].min():.1f} - {output_df['pitch_mean'].max():.1f} (mean: {output_df['pitch_mean'].mean():.1f})")
    print(f"  mmse: {output_df['mmse'].min()} - {output_df['mmse'].max()} (mean: {output_df['mmse'].mean():.1f})")
    
    # Show errors if any
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:5]:  # Show first 5
            print(f"  - {err['session_id']}: {err['error']}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    return output_df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract features from audio files')
    parser.add_argument('--csv', type=str, default='data.csv',
                       help='Path to CSV file with session_id, audio_path, mmse')
    parser.add_argument('--audio-dir', type=str, default='audio',
                       help='Directory containing audio files')
    parser.add_argument('--output', type=str, default='extracted_features.csv',
                       help='Output CSV path for extracted features')
    
    args = parser.parse_args()
    
    extract_features_batch(args.csv, args.audio_dir, args.output)

