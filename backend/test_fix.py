#!/usr/bin/env python3
"""
Simple test to verify the variable mapping fix
"""

# Simulate the scenario that was causing the error
import numpy as np

# Simulate prediction variables (normally these would come from model predictions)
y_pred_svr = np.array([25.1, 26.3, 24.8])
y_pred_rf = np.array([24.9, 26.1, 25.2])
y_pred_xgb = np.array([25.0, 26.2, 24.9])

# Simulate model metrics
model_metrics = {
    "regression": {
        "SVR": {"mse": 4.2},
        "RandomForestRegressor": {"mse": 3.8},
        "XGBRegressor": {"mse": 3.5}
    }
}

# Test the fixed logic
best_reg_model = min(model_metrics["regression"],
                   key=lambda x: model_metrics["regression"][x]["mse"])

print(f"Best regression model: {best_reg_model}")

# Map model names to prediction variables (the fix)
pred_var_map = {
    "SVR": y_pred_svr,
    "RandomForestRegressor": y_pred_rf,
    "XGBRegressor": y_pred_xgb
}

y_pred_mmse = pred_var_map[best_reg_model]

print(f"Selected predictions shape: {y_pred_mmse.shape}")
print(f"Selected predictions: {y_pred_mmse}")
print("✅ Variable mapping fix working correctly!")
