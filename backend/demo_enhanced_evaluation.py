#!/usr/bin/env python3
"""
Demo script showcasing the enhanced evaluation system
Shows improved classification and regression metrics
"""

print("🧠 Enhanced Evaluation System Demo")
print("=" * 80)

print("\n✅ ENHANCED CLASSIFICATION EVALUATION:")
print("• StratifiedKFold Cross-Validation (k=5)")
print("• GridSearchCV Hyperparameter Tuning")
print("• Detailed Classification Reports (precision, recall, f1)")
print("• Confusion Matrix Generation & PNG Export")
print("• Cross-validation F1 scores with mean ± std")

print("\n✅ ENHANCED REGRESSION EVALUATION:")
print("• MSE, MAE, R² comprehensive metrics")
print("• Overfitting detection (R² < 0 warnings)")
print("• Enhanced logging with detailed performance")
print("• Best model selection based on validation metrics")

print("\n📊 NEW EVALUATION PIPELINE:")
print("""
1. Classification Evaluation:
   - cross_val_predict() for robust CV predictions
   - classification_report() with detailed metrics
   - ConfusionMatrixDisplay() for visualization
   - PNG export for all confusion matrices

2. Regression Evaluation:
   - predict() on test set
   - mean_absolute_error() for MAE
   - r2_score() for R² with overfitting warnings
   - Enhanced logging with model-specific metrics

3. System-wide Evaluation:
   - evaluate_system() function for complete assessment
   - JSON export of all results
   - Summary logging for quick performance overview
""")

print("\n🔧 SAMPLE USAGE:")
print("""
# Enhanced evaluation after training
results = evaluate_system(
    classifiers=model.classifiers,
    regressors=model.regressors,
    X=X_scaled,
    y=y_class,
    X_test=X_test_scaled,
    y_test=y_reg_test,
    cv=StratifiedKFold(n_splits=5),
    results_path="results/evaluation_results.json"
)

# Individual model evaluation
report, cm = evaluate_classification(
    model=rf_classifier,
    X=X_train,
    y=y_train,
    cv=StratifiedKFold(n_splits=5),
    model_name="RandomForest"
)

metrics = evaluate_regression(
    model=svr_regressor,
    X_test=X_test,
    y_test=y_test,
    model_name="SVR"
)
""")

print("\n📈 EXPECTED OUTPUTS:")
print("""
=== RandomForest Classification Report ===
              precision    recall  f1-score   support
           0       0.875     0.933     0.903        30
           1       0.917     0.846     0.880        26
    accuracy                           0.893        56
   macro avg       0.896     0.890     0.892        56
weighted avg       0.894     0.893     0.893        56

Confusion matrix saved to plots/confusion_matrix_randomforest.png

=== SVR Regression Metrics ===
MSE=4.234, MAE=1.567, R²=0.789

=== XGB Regression Metrics ===
MSE=3.891, MAE=1.423, R²=0.812
⚠ XGB may be overfitting (R² < 0)  # Only if R² < 0
""")

print("\n💾 EXPORTED FILES:")
print("• results/evaluation_results.json - Complete evaluation results")
print("• plots/confusion_matrix_*.png - Confusion matrices for each classifier")
print("• results/training_results_comprehensive.json - Training evaluation")

print("\n🎯 KEY IMPROVEMENTS:")
print("• Robust cross-validation prevents overfitting")
print("• Detailed metrics for clinical decision making")
print("• Visual confusion matrices for error analysis")
print("• JSON export for further analysis")
print("• Overfitting warnings for model validation")

print("\n" + "=" * 80)
print("✨ Enhanced evaluation system successfully implemented!")
print("🚀 Ready for comprehensive model assessment and clinical validation.")
print("=" * 80)
