"""
Predict MMSE score from audio + transcript using a trained model bundle.

Outputs JSON:
{
  "predicted_mmse": float,
  "model_used": string,
  "rmse": float,
  "feature_importance": {feature: importance}
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import joblib
import numpy as np

from feature_extraction.acoustic import extract_acoustic_features
from feature_extraction.linguistic import extract_linguistic_features


def load_bundle(model_dir: str):
    md = Path(model_dir)
    model = joblib.load(md / "best_model.pkl")
    with open(md / "feature_names.json", "r", encoding="utf-8") as f:
        feature_names = json.load(f)
    with open(md / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return model, feature_names, metadata


def build_vector(audio_path: str, transcript: str, feature_names: list, spacy_model: str, bert_model: str):
    feats = {
        **extract_acoustic_features(audio_path),
        **extract_linguistic_features(transcript, language_model=spacy_model, bert_model=bert_model),
    }
    # align to expected order; missing values -> 0
    vec = [feats.get(name, 0.0) for name in feature_names]
    return np.array(vec, dtype=float).reshape(1, -1)


def get_feature_importance(model, feature_names):
    if hasattr(model, "coef_"):
        coefs = model.coef_.ravel()
    elif hasattr(model, "feature_importances_"):
        coefs = model.feature_importances_
    else:
        coefs = np.zeros(len(feature_names))
    return {name: float(val) for name, val in zip(feature_names, coefs)}


def main():
    parser = argparse.ArgumentParser(description="Predict MMSE using trained model.")
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--audio", type=str, required=True)
    parser.add_argument("--transcript", type=str, required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    model, feature_names, metadata = load_bundle(cfg["paths"]["model_dir"])
    vec = build_vector(args.audio, args.transcript, feature_names, cfg["nlp"]["spacy_model"], cfg["nlp"]["bert_model"])
    pred = float(model.predict(vec)[0])
    pred = max(0.0, min(30.0, pred))

    result = {
        "predicted_mmse": pred,
        "model_used": metadata.get("best_model", type(model).__name__),
        "rmse": metadata.get("metrics", {}).get(metadata.get("best_model", ""), {}).get("rmse_mean"),
        "feature_importance": get_feature_importance(model[-1] if hasattr(model, "__getitem__") else model, feature_names),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
