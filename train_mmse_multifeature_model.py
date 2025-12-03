#!/usr/bin/env python3
"""
Train MMSE regression model on REAL dataset with both acoustic and linguistic features.

Mục tiêu:
- KHÔNG đụng vào pipeline đang chạy (train_model_with_audio_features.py, backend, frontend).
- Chuẩn bị một mô hình ML có thể học trực tiếp từ:
    * Đặc trưng âm học: speech_rate, pause_rate, f0_mean, f0_variability, number_utterances, silence_mean, pitch_mean, v.v.
    * Đặc trưng ngôn ngữ: TTR, idea_density, fluency (F_flu), word_count, v.v.
- Nhãn (target) là điểm MMSE chuẩn do chuyên gia chấm (0–30).

Yêu cầu dữ liệu:
- CSV có tối thiểu một cột nhãn, mặc định: 'mmse' (có thể đổi bằng --target-col).
- Các cột feature numeric sẽ được tự động chọn (trừ target và các id/text).
- Khuyến nghị:
    acoustic:  speech_rate, speech_rate_wpm, pause_rate, f0_mean, f0_variability,
               number_utterances, silence_mean, pitch_mean, duration, ...
    linguistic: TTR, idea_density, F_flu, word_count, ...

Ví dụ chạy:
    python train_mmse_multifeature_model.py --csv data/mmse_features.csv \\
        --target-col mmse \\
        --output-dir model_bundle/mmse_multifeature_model

Script này CHỈ train & lưu model; việc tích hợp vào backend/frontend bạn có thể làm sau,
giữ nguyên toàn bộ hành vi hiện tại.
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression
import joblib


def load_dataset(
    csv_path: str,
    target_col: str = "mmse",
    id_cols: List[str] | None = None,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load dataset from CSV and split into X (features) and y (target).

    Quy ước:
    - target_col: cột điểm MMSE chuẩn (0–30), ví dụ: 'mmse', 'final_mmse', ...
    - id_cols: các cột nhận dạng sẽ bị loại bỏ khỏi features (vd: session_id, user_id, ...).
    - Các cột còn lại numeric sẽ được dùng làm feature.
    """
    if id_cols is None:
        id_cols = ["session_id", "user_id", "question_id", "audio_path", "text", "transcript"]

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in CSV. Available: {list(df.columns)}")

    # Drop rows without target
    df = df.dropna(subset=[target_col])

    # Candidate feature columns: numeric and not in id/target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c != target_col and c not in id_cols]

    if not feature_cols:
        raise ValueError("No numeric feature columns found. "
                         "Ensure your CSV has numeric acoustic/linguistic features.")

    X = df[feature_cols].values.astype(float)
    y = df[target_col].values.astype(float)

    # Clip MMSE to [0, 30] for safety
    y = np.clip(y, 0.0, 30.0)

    return X, y, feature_cols


def build_models() -> dict:
    """
    Định nghĩa một vài mô hình hồi quy hợp lý cho bài toán MMSE.
    - Ridge: tuyến tính, dễ giải thích.
    - RandomForest: phi tuyến, chịu được feature phức tạp.
    - GradientBoosting: thường cho hiệu năng tốt với dữ liệu vừa phải.
    """
    models: dict[str, Pipeline] = {}

    base_estimators = {
        "ridge": Ridge(alpha=1.0, random_state=42),
        "rf": RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        ),
        "gbr": GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }

    for name, est in base_estimators.items():
        pipe = Pipeline(
            steps=[
                ("scaler", RobustScaler()),
                ("selector", SelectKBest(score_func=mutual_info_regression, k="all")),
                ("reg", est),
            ]
        )
        models[name] = pipe

    return models


def evaluate_model(
    model: Pipeline,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_splits: int = 5,
) -> dict:
    """
    Đánh giá model bằng:
    - Cross-validation (KFold) trên train: MAE, R² trung bình.
    - Test set: MAE, R².
    """
    # Cross-val trên train
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    cv_mae: List[float] = []
    cv_r2: List[float] = []

    for train_idx, val_idx in kf.split(X_train):
        X_tr, X_val = X_train[train_idx], X_train[val_idx]
        y_tr, y_val = y_train[train_idx], y_train[val_idx]

        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_val)
        cv_mae.append(mean_absolute_error(y_val, y_pred))
        cv_r2.append(r2_score(y_val, y_pred))

    # Fit lại trên toàn bộ train
    model.fit(X_train, y_train)

    # Đánh giá trên test
    y_pred_test = model.predict(X_test)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    test_r2 = r2_score(y_test, y_pred_test)

    return {
        "cv_mae_mean": float(np.mean(cv_mae)),
        "cv_mae_std": float(np.std(cv_mae)),
        "cv_r2_mean": float(np.mean(cv_r2)),
        "cv_r2_std": float(np.std(cv_r2)),
        "test_mae": float(test_mae),
        "test_r2": float(test_r2),
    }


def save_bundle(
    model: Pipeline,
    feature_names: List[str],
    output_dir: str,
    metadata: dict,
) -> str:
    """
    Lưu model bundle (model + metadata) để backend có thể load và dùng inference.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, out_path / "model.pkl")
    joblib.dump(feature_names, out_path / "feature_names.pkl")

    meta_path = out_path / "metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return str(out_path.resolve())


def main():
    parser = argparse.ArgumentParser(
        description="Train MMSE regression model on REAL acoustic + linguistic features."
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path tới CSV chứa features + nhãn MMSE thật.",
    )
    parser.add_argument(
        "--target-col",
        type=str,
        default="mmse",
        help="Tên cột nhãn MMSE (mặc định: mmse).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="model_bundle/mmse_multifeature_model",
        help="Thư mục lưu model bundle.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Tỉ lệ test set (mặc định: 0.2).",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("TRAINING MMSE MULTI-FEATURE MODEL (REAL DATA)")
    print("=" * 80)
    print(f"CSV path   : {args.csv}")
    print(f"Target col : {args.target_col}")
    print(f"Output dir : {args.output_dir}")
    print(f"Test size  : {args.test_size}")

    # 1. Load data
    X, y, feature_names = load_dataset(args.csv, target_col=args.target_col)
    print(f"\nLoaded dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Features: {feature_names}")
    print(f"MMSE range: {y.min():.2f} - {y.max():.2f}")

    # 2. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=42,
        stratify=None,  # Có thể dùng stratify theo bins của y nếu muốn
    )
    print(f"\nTrain size: {X_train.shape[0]}  |  Test size: {X_test.shape[0]}")

    # 3. Build candidate models
    models = build_models()

    best_name = None
    best_model = None
    best_metric = float("inf")  # dùng MAE (càng thấp càng tốt)
    results_summary: dict[str, dict] = {}

    # 4. Train & evaluate từng model
    for name, model in models.items():
        print("\n" + "-" * 80)
        print(f"Training model: {name}")
        metrics = evaluate_model(model, X_train, y_train, X_test, y_test)
        results_summary[name] = metrics

        print(f"CV MAE    : {metrics['cv_mae_mean']:.3f} ± {metrics['cv_mae_std']:.3f}")
        print(f"CV R²     : {metrics['cv_r2_mean']:.3f} ± {metrics['cv_r2_std']:.3f}")
        print(f"Test MAE  : {metrics['test_mae']:.3f}")
        print(f"Test R²   : {metrics['test_r2']:.3f}")

        if metrics["test_mae"] < best_metric:
            best_metric = metrics["test_mae"]
            best_name = name
            best_model = model

    assert best_model is not None and best_name is not None

    print("\n" + "=" * 80)
    print(f"🏆 Best model: {best_name}")
    print(f"   Test MAE : {results_summary[best_name]['test_mae']:.3f}")
    print(f"   Test R²  : {results_summary[best_name]['test_r2']:.3f}")

    # 5. Save bundle
    metadata = {
        "model_name": best_name,
        "description": (
            "MMSE regression model trained on REAL acoustic + linguistic features. "
            "Target is clinician-rated MMSE (0–30). "
            "This model is for research/decision support, NOT a replacement for clinical diagnosis."
        ),
        "target_col": args.target_col,
        "metrics": results_summary[best_name],
        "all_models": results_summary,
        "feature_names": feature_names,
    }

    bundle_path = save_bundle(best_model, feature_names, args.output_dir, metadata)

    print("\nSaved model bundle to:", bundle_path)
    print("=" * 80)
    print("DONE.")
    print("=" * 80)


if __name__ == "__main__":
    main()


