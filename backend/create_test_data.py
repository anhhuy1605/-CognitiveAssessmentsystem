#!/usr/bin/env python3
"""Create test data for CLI testing"""

import numpy as np
import pandas as pd

def create_test_data():
    np.random.seed(42)
    n_samples = 100
    n_features = 20
    
    # Create features
    X = np.random.randn(n_samples, n_features)
    
    # Create realistic targets
    decision_score = (0.5 * X[:, 0] + 0.3 * X[:, 1] - 0.2 * X[:, 2] + 
                     np.random.normal(0, 0.3, n_samples))
    y_class = (decision_score > 0).astype(int)
    
    # MMSE scores
    mmse_base = 25 - 8 * y_class
    mmse_adjustment = 0.2 * X[:, 3] - 0.1 * X[:, 4]
    mmse_noise = np.random.normal(0, 2, n_samples)
    y_mmse = np.clip(mmse_base + mmse_adjustment + mmse_noise, 0, 30)
    
    # Create DataFrame
    data = {
        'participant_id': [f'P{i:04d}' for i in range(n_samples)],
        'dx': y_class,
        'mmse': y_mmse,
        'age': np.random.normal(70, 10, n_samples).clip(50, 90),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'education': np.random.normal(12, 3, n_samples).clip(6, 20)
    }
    
    # Add features
    for i in range(n_features):
        data[f'feature_{i}'] = X[:, i]
    
    df = pd.DataFrame(data)
    df.to_csv('test_data.csv', index=False)
    print(f"Created test data: {n_samples} samples")
    print(f"Class distribution: {pd.Series(y_class).value_counts().to_dict()}")
    
if __name__ == "__main__":
    create_test_data()
