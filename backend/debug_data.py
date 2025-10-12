#!/usr/bin/env python3
"""Debug data loading issues"""

import pandas as pd
import numpy as np

# Load the data
print("Loading dx-mmse.csv...")
dx_df = pd.read_csv('dx-mmse.csv')

print(f"Shape: {dx_df.shape}")
print(f"Columns: {list(dx_df.columns)}")
print(f"Data types:\n{dx_df.dtypes}")
print(f"\nNull counts:\n{dx_df.isnull().sum()}")

# Show sample data
print(f"\nFirst 5 rows:")
print(dx_df.head())

# Check which columns have all nulls
all_null_cols = dx_df.columns[dx_df.isnull().all()]
print(f"\nColumns with all nulls: {list(all_null_cols)}")

# Check which columns have any nulls
any_null_cols = dx_df.columns[dx_df.isnull().any()]
print(f"Columns with any nulls: {list(any_null_cols)}")

# Check for non-numeric columns
non_numeric_cols = dx_df.select_dtypes(exclude=[np.number]).columns
print(f"Non-numeric columns: {list(non_numeric_cols)}")

# Check unique values in non-numeric columns
for col in non_numeric_cols[:5]:  # First 5 only
    unique_vals = dx_df[col].unique()[:10]  # First 10 unique values
    print(f"\n{col} unique values (first 10): {unique_vals}")
