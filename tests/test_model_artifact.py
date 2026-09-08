import warnings

import pytest

from src.model import MODEL_PATH, load_model, predict_text


def test_saved_model_artifact_predicts_normal_and_short_text():
    if not MODEL_PATH or not __import__("os").path.exists(MODEL_PATH):
        pytest.skip("Model artifact not found")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        model = load_model(MODEL_PATH)
    assert list(model.named_steps) == ["preprocess", "features", "classifier"]
    assert not any("InconsistentVersionWarning" in warning.category.__name__ for warning in captured)
    assert set(model.classes_) == {0, 1}
    for text in ("Experienced software engineer role", "x"):
        label, probability, cleaned = predict_text(model, text)
        assert label in {"Real", "Fake"}
        assert 0 <= probability <= 1
        assert isinstance(cleaned, str)


def test_saved_model_exposes_predict_proba():
    if not __import__("os").path.exists(MODEL_PATH):
        pytest.skip("Model artifact not found")
    model = load_model(MODEL_PATH)
    assert model.predict_proba(model.named_steps["preprocess"].transform(
        __import__("src.preprocessing", fromlist=["make_inference_frame"]).make_inference_frame("job")
    )).shape[1] == 2
