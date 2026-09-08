import os

import pytest

from src.explain import explain_with_lime, explain_with_shap, top_shap_features_for_instance
from src.model import MODEL_PATH, load_model


@pytest.fixture
def saved_model():
    if not os.path.exists(MODEL_PATH):
        pytest.skip("Model artifact not found")
    return load_model(MODEL_PATH)


def test_shap_returns_real_mapped_features(saved_model):
    result = explain_with_shap(saved_model, ["contact email"])
    assert result["available"] is True
    features = top_shap_features_for_instance(result, top_n=5)
    assert features
    assert all(isinstance(name, str) and isinstance(value, float) for name, value in features)
    assert all("__" not in name for name, _ in features)


def test_lime_is_structured_when_available_or_missing(saved_model):
    features, explanation = explain_with_lime(saved_model, "contact email")
    assert isinstance(features, list)
    assert explanation is None or features


def test_shap_availability_matches_usable_contributions(saved_model):
    result = explain_with_shap(saved_model, ["contact email"])
    features = top_shap_features_for_instance(result, top_n=5)
    assert result["available"] is bool(features)
