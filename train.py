"""
Train MMSE regression models (Ridge, SVR, GBR) using acoustic + linguistic features.

Spec compliance:
- y_hat_MMSE = f(x_acoustic, x_text)
- Acoustic features via librosa (MFCC + deltas, F0 stats, speech rate, pause metrics, energy)
- Linguistic features via spaCy + BERT CLS + simple n-gram/fillers metrics
- Standardization inside CV pipeline; subject-independent split assumed by dataset
- Metrics: RMSE (mean / std) using 5-fold CV
- Reproducibility: random seed = 42

Input CSV requirements:
    audio_path (str) : path to audio file
    transcript (str) : transcript text
    mmse (float)     : target score (0-30)

Outputs (default paths in config.json):
    models/best_model.pkl
    models/feature_names.json
    models/metadata.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.linear_model import Ridge

RANDOM_SEED = 42


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_row_features(row: pd.Series, lang_model: str, bert_model: str) -> Dict[str, float]:
    """
    If audio_path & transcript exist, extract raw features.
    Otherwise, fall back to existing numeric columns (handled elsewhere).
    """
    from feature_extraction.acoustic import extract_acoustic_features
    from feature_extraction.linguistic import extract_linguistic_features

    acoustic = extract_acoustic_features(row["audio_path"])
    linguistic = extract_linguistic_features(
        row["transcript"], language_model=lang_model, bert_model=bert_model
    )
    feats = {**acoustic, **linguistic}
    return feats


def build_feature_matrix(
    df: pd.DataFrame, lang_model: str, bert_model: str
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Two modes:
    - Preferred: extract from audio_path + transcript if both columns exist.
    - Fallback: use existing numeric columns (drop target/id-like columns).
    """
    has_raw = {"audio_path", "transcript"}.issubset(set(df.columns))
    if has_raw:
        rows = []
        for _, row in df.iterrows():
            feats = _extract_row_features(row, lang_model, bert_model)
            rows.append(feats)
        feat_df = pd.DataFrame(rows)
    else:
        # Fallback: use provided numeric features
        id_like = {"session_id", "user_id", "participant_id", "id", "dx"}
        target_like = {"mmse", "mms", "mmse2"}
        num_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [c for c in num_cols if c not in id_like and c not in target_like]
        if not feature_cols:
            raise ValueError("No numeric features found for fallback training.")
        feat_df = df[feature_cols].copy()

    feat_df = feat_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    feature_names = feat_df.columns.tolist()
    return feat_df, feature_names


def build_models() -> Dict[str, Tuple[Pipeline, dict]]:
    models = {
        "ridge": (
            Pipeline([("scaler", StandardScaler()), ("reg", Ridge(random_state=RANDOM_SEED))]),
            {"reg__alpha": [0.1, 1.0, 10.0]},
        ),
        "svr": (
            Pipeline([("scaler", StandardScaler()), ("reg", SVR())]),
            {"reg__C": [1.0, 10.0], "reg__epsilon": [0.1, 0.5], "reg__kernel": ["rbf"]},
        ),
        "gbr": (
            Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "reg",
                        GradientBoostingRegressor(
                            random_state=RANDOM_SEED,
                            n_estimators=300,
                            learning_rate=0.05,
                            max_depth=3,
                        ),
                    ),
                ]
            ),
            {},
        ),
    }
    return models


def evaluate_models(X: np.ndarray, y: np.ndarray) -> Tuple[str, Pipeline, dict]:
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    best_name, best_model = None, None
    best_rmse = float("inf")
    metrics_summary = {}

    for name, (pipe, grid) in build_models().items():
        if grid:
            search = GridSearchCV(pipe, grid, cv=kf, scoring="neg_mean_squared_error", n_jobs=-1)
            search.fit(X, y)
            model = search.best_estimator_
            rmse_scores = np.sqrt(-search.cv_results_["mean_test_score"])
        else:
            # No grid; do manual CV
            rmses = []
            for train_idx, val_idx in kf.split(X):
                X_tr, X_val = X[train_idx], X[val_idx]
                y_tr, y_val = y[train_idx], y[val_idx]
                pipe.fit(X_tr, y_tr)
                pred = pipe.predict(X_val)
                rmses.append(np.sqrt(mean_squared_error(y_val, pred)))
            model = pipe.fit(X, y)
            rmse_scores = np.array(rmses)

        mean_rmse = float(np.mean(rmse_scores))
        std_rmse = float(np.std(rmse_scores))
        metrics_summary[name] = {"rmse_mean": mean_rmse, "rmse_std": std_rmse}

        if mean_rmse < best_rmse:
            best_rmse = mean_rmse
            best_name = name
            best_model = model

    assert best_model is not None
    return best_name, best_model, metrics_summary


def save_bundle(model: Pipeline, feature_names: List[str], metrics: dict, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "best_model.pkl")
    with open(out / "feature_names.json", "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=2)
    with open(out / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Train MMSE regression models (acoustic + linguistic).")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    args = parser.parse_args()

    cfg = load_config(args.config)
    data_path = Path(cfg["data"]["train_csv"])
    if not data_path.exists():
        raise FileNotFoundError(f"Training CSV not found: {data_path}")

    df = pd.read_csv(data_path)

    # Detect target column
    target_candidates = ["mmse", "mms", "mmse2"]
    target_col = next((c for c in target_candidates if c in df.columns), None)
    if target_col is None:
        raise ValueError(f"No target column found among {target_candidates}")

    X_df, feature_names = build_feature_matrix(
        df, cfg["nlp"]["spacy_model"], cfg["nlp"]["bert_model"]
    )
    y = df[target_col].astype(float).clip(0, 30).values

    X = X_df.values
    best_name, best_model, metrics_summary = evaluate_models(X, y)
    print(f"Best model: {best_name}")
    print(metrics_summary[best_name])

    save_bundle(
        best_model,
        feature_names,
        {
            "best_model": best_name,
            "metrics": metrics_summary,
        },
        cfg["paths"]["model_dir"],
    )


if __name__ == "__main__":
    main()
