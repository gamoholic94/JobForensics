"""
Training, saving, loading, and prediction utilities for the
Fake Job Posting Detection model.

Run directly to train and save a model:
    python -m src.model
"""
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (average_precision_score, classification_report,
                             brier_score_loss, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FunctionTransformer, Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.calibration import CalibratedClassifierCV

try:
    from src.preprocessing import (
        TARGET_COLUMN,
        BINARY_COLUMNS,
        CATEGORICAL_COLUMNS,
        load_raw_dataset,
        make_inference_frame,
        preprocess_dataframe,
    )
except ImportError:  # allow running as a standalone script
    from preprocessing import (
        TARGET_COLUMN,
        BINARY_COLUMNS,
        CATEGORICAL_COLUMNS,
        load_raw_dataset,
        make_inference_frame,
        preprocess_dataframe,
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "fake_job_postings.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "model.pkl"
MODEL_METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"


def build_pipeline(model_type: str = "logistic_regression", use_structured_features: bool = True,
                   calibrate: bool = True) -> Pipeline:
    """Build a leakage-safe pipeline with optional internal probability calibration."""
    if model_type == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=300, max_depth=None, class_weight="balanced", random_state=42
        )
    elif model_type == "xgboost":
        from xgboost import XGBClassifier

        classifier = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            eval_metric="logloss",
            random_state=42,
        )
    else:  # default: logistic regression (fast, highly explainable)
        classifier = LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42
        )

    text_transformer = TfidfVectorizer(
        max_features=20000, ngram_range=(1, 2), stop_words="english"
    )
    if use_structured_features:
        feature_transformer = ColumnTransformer(
            transformers=[
                ("text", text_transformer, "text"),
                ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
                ("numeric", StandardScaler(with_mean=False), BINARY_COLUMNS + [
                    "text_length", "has_salary_range", "salary_min", "salary_max", "salary_midpoint"
                ]),
            ],
            remainder="drop",
        )
    else:
        feature_transformer = ColumnTransformer(
            transformers=[("text", text_transformer, "text")], remainder="drop"
        )
    if calibrate:
        classifier = CalibratedClassifierCV(classifier, cv=3, method="sigmoid")
    pipeline = Pipeline(
        steps=[
            ("preprocess", FunctionTransformer(preprocess_dataframe, validate=False)),
            ("features", feature_transformer),
            ("classifier", classifier),
        ]
    )
    return pipeline


def train(model_type: str = "logistic_regression", data_path: str = RAW_DATA_PATH):
    """Train the model on the raw dataset and save it to disk."""
    if not Path(data_path).exists():
        raise FileNotFoundError(
            f"Dataset not found at '{data_path}'. Download the Kaggle "
            "'Real or Fake Job Posting Prediction' dataset and place the CSV "
            "there (see README.md)."
        )

    df = load_raw_dataset(data_path)
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline(model_type, use_structured_features=True)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float((y_pred == y_test).mean()),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "average_precision": float(average_precision_score(y_test, y_proba)),
        "brier_score": float(brier_score_loss(y_test, y_proba)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    print(classification_report(y_test, y_pred, target_names=["Real", "Fake"], zero_division=0))
    print(metrics)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return pipeline, metrics


def load_model(model_path: str = MODEL_PATH) -> Pipeline:
    """Load a previously trained model pipeline from disk."""
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"No trained model found at '{model_path}'. Run `python -m src.model` "
            "to train and save one first."
        )
    return joblib.load(model_path)


def load_model_metadata(metadata_path: str = MODEL_METADATA_PATH) -> dict:
    """Load optional artifact metadata, returning an empty mapping if absent."""
    path = Path(metadata_path)
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return metadata if isinstance(metadata, dict) else {}


def predict_text(pipeline: Pipeline, raw_text: str, fields: dict | None = None):
    """
    Predict whether a single raw job description is Fake or Real.
    Returns (label, model_fake_probability, cleaned_text).
    """
    inference_frame = make_inference_frame(raw_text, **(fields or {}))
    proba = pipeline.predict_proba(inference_frame)[0]
    classes = list(getattr(pipeline, "classes_", []))
    try:
        fake_index = classes.index(1)
    except ValueError as exc:
        raise ValueError("Model must expose class 1 for fake postings") from exc
    fake_probability = float(proba[fake_index])
    label = "Fake" if fake_probability >= 0.5 else "Real"
    cleaned = preprocess_dataframe(inference_frame).iloc[0]["text"]
    return label, fake_probability, cleaned


if __name__ == "__main__":
    train(model_type="logistic_regression")
