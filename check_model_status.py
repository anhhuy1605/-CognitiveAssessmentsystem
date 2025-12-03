#!/usr/bin/env python3
"""
Script kiểm tra trạng thái model ML và dữ liệu
"""

import os
import sys
import json
from pathlib import Path

def check_model_bundle():
    """Kiểm tra model bundle"""
    print("=" * 60)
    print("KIEM TRA MODEL BUNDLE")
    print("=" * 60)
    
    bundle_path = Path("model_bundle/improved_regression_model")
    
    if not bundle_path.exists():
        print("ERROR: Model bundle khong ton tai!")
        return False
    
        print(f"OK: Model bundle ton tai: {bundle_path}")
    
    # Check các files
    required_files = ['model.pkl', 'scaler.pkl', 'selector.pkl', 'feature_names.pkl', 'metadata.json']
    all_exist = True
    
    for file in required_files:
        file_path = bundle_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  OK: {file} ({size:,} bytes)")
        else:
            print(f"  ERROR: {file} KHONG TON TAI")
            all_exist = False
    
    # Load metadata
    metadata_path = bundle_path / 'metadata.json'
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"\nMetadata:")
            print(f"  Model: {metadata.get('model_name', 'N/A')}")
            print(f"  Version: {metadata.get('version', 'N/A')}")
            print(f"  Training date: {metadata.get('training_date', 'N/A')}")
        except Exception as e:
            print(f"  WARNING: Khong the doc metadata: {e}")
    
    return all_exist

def check_training_data():
    """Kiểm tra dữ liệu training"""
    print("\n" + "=" * 60)
    print("KIEM TRA DU LIEU TRAINING")
    print("=" * 60)
    
    data_paths = [
        "backend/dx-mmse.csv",
        "dx-mmse.csv",
        "backend/dx-mmse.csv"
    ]
    
    found = False
    for path in data_paths:
        if os.path.exists(path):
            print(f"OK: Tim thay du lieu: {path}")
            try:
                import pandas as pd
                df = pd.read_csv(path)
                print(f"  Shape: {df.shape}")
                print(f"  Columns: {len(df.columns)}")
                
                # Check MMSE column
                if 'mmse' in df.columns:
                    mmse_values = df['mmse'].dropna()
                    print(f"  MMSE range: {mmse_values.min():.1f} - {mmse_values.max():.1f}")
                    print(f"  MMSE samples: {len(mmse_values)}")
                else:
                    print(f"  WARNING: Khong co cot 'mmse'")
                
                found = True
                break
            except Exception as e:
                    print(f"  ERROR: Loi doc file: {e}")
    
    if not found:
        print("ERROR: KHONG TIM THAY DU LIEU TRAINING!")
        print("   Code sẽ fallback sang synthetic data (không chính xác)")
    
    return found

def check_model_loading():
    """Kiểm tra cách model được load trong app.py"""
    print("\n" + "=" * 60)
    print("KIEM TRA MODEL LOADING TRONG APP.PY")
    print("=" * 60)
    
    app_path = Path("backend/app.py")
    if not app_path.exists():
        print("ERROR: Khong tim thay backend/app.py")
        return False
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check cognitive_model initialization
    if 'cognitive_model = None' in content:
        print("WARNING: cognitive_model duoc khoi tao la None")
    
    # Check if model bundle is loaded
    if 'model_bundle' in content and 'joblib.load' in content:
        print("OK: Co code load model bundle")
    else:
        print("ERROR: KHONG CO CODE LOAD MODEL BUNDLE!")
        print("   Model chi duoc train moi moi lan start server")
    
    # Check train_five_feature_model
    if 'train_five_feature_model' in content:
        print("WARNING: Code su dung train_five_feature_model() - train model moi moi lan")
    
    # Check feature names
    if 'feature_names = None' in content:
        print("WARNING: feature_names duoc khoi tao la None")
    
    return True

def check_feature_extraction():
    """Kiểm tra feature extraction"""
    print("\n" + "=" * 60)
    print("KIEM TRA FEATURE EXTRACTION")
    print("=" * 60)
    
    # Check required features
    required_features = ['speech_rate', 'number_utterances', 'silence_mean', 'pitch_mean']
    print(f"Features yeu cau boi model: {required_features}")
    
    # Check if extract_audio_features exists
    app_path = Path("backend/app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def extract_audio_features' in content:
            print("OK: Co function extract_audio_features")
        else:
            print("WARNING: Khong tim thay extract_audio_features")
    
    return True

def check_model_usage():
    """Kiểm tra cách model được sử dụng"""
    print("\n" + "=" * 60)
    print("KIEM TRA MODEL USAGE")
    print("=" * 60)
    
    app_path = Path("backend/app.py")
    if not app_path.exists():
        return False
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check predict_cognitive_score
    if 'def predict_cognitive_score' in content:
        print("OK: Co function predict_cognitive_score")
        
        # Check if it handles None model
        if 'if not cognitive_model' in content:
            print("WARNING: Code co fallback khi model la None (tra ve gia tri mac dinh)")
    else:
        print("ERROR: Khong tim thay predict_cognitive_score")
    
    return True

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("CHAN DOAN MODEL ML - KIEM TRA TRANG THAI")
    print("=" * 60)
    
    results = {
        'model_bundle': check_model_bundle(),
        'training_data': check_training_data(),
        'model_loading': check_model_loading(),
        'feature_extraction': check_feature_extraction(),
        'model_usage': check_model_usage()
    }
    
    print("\n" + "=" * 60)
    print("TONG KET")
    print("=" * 60)
    
    for check, result in results.items():
        status = "OK" if result else "ERROR"
        print(f"{status}: {check}")
    
    print("\n" + "=" * 60)
    print("KHUYEN NGHI")
    print("=" * 60)
    
    if not results['model_bundle']:
        print("1. ERROR: Model bundle khong day du - can train lai model")
    
    if not results['training_data']:
        print("2. ERROR: Khong co du lieu training - can co file dx-mmse.csv")
    
    if not results['model_loading']:
        print("3. ERROR: Model khong duoc load dung cach - can fix code loading")
    
    print("\nXem chi tiet trong MODEL_DIAGNOSTIC_REPORT.md")

if __name__ == "__main__":
    main()

