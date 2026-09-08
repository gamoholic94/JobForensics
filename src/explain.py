"""
Explainable AI (XAI) utilities: SHAP and LIME wrappers for explaining
individual fake-job-posting predictions made by the trained pipeline.

All functions return structured results with error handling to ensure
that XAI failures do not crash the entire analysis pipeline.
"""
import logging
import numpy as np
logger = logging.getLogger(__name__)
try:
    import shap
except ImportError:
    shap = None
try:
    from lime.lime_text import LimeTextExplainer
except ImportError:
    LimeTextExplainer = None
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
CLASS_NAMES = ["Real", "Fake"]
def _underlying_estimator(classifier):
    """Return the fitted estimator used by a calibrated classifier."""
    if isinstance(classifier, CalibratedClassifierCV):
        calibrated = getattr(classifier, "calibrated_classifiers_", [])
        if not calibrated:
            raise ValueError("Calibrated classifier has no fitted estimators")
        return calibrated[0].estimator
    return classifier
def _display_feature_name(name: str) -> str:
    """Remove transformer prefixes while retaining the actual feature name."""
    return name.split("__", 1)[1] if "__" in name else name
def explain_with_lime(pipeline, cleaned_text: str, num_features: int = 10):
    """
    Explain a single prediction using LIME.
    
    Returns a tuple of (explanation_list, explanation_object) where:
    - explanation_list is a list of (word, weight) tuples
    - explanation_object is the raw LIME explanation for HTML rendering
    
    On error, returns ({}, None) to allow graceful degradation.
    """
    if LimeTextExplainer is None:
        logger.warning("LIME not available: lime package not installed")
        return [], None
    
    try:
        explainer = LimeTextExplainer(class_names=CLASS_NAMES)

        def predict_proba_fn(texts):
            """Wrapper to handle both raw text and preprocessed dataframes."""
            if "preprocess" in pipeline.named_steps:
                import pandas as pd
                from src.preprocessing import make_inference_frame
                rows = pd.concat([make_inference_frame(text) for text in texts], ignore_index=True)
                return pipeline.predict_proba(rows)
            return pipeline.predict_proba(texts)

        explanation = explainer.explain_instance(
            cleaned_text,
            predict_proba_fn,
            num_features=min(num_features, 20),
            labels=(1,),
        )
        return explanation.as_list(label=1), explanation
    
    except Exception as exc:
        logger.warning("LIME explanation failed: %s", exc)
        return [], None


def explain_with_shap(pipeline, cleaned_texts, sample_background=None):
    """
    Build a SHAP explainer for the TF-IDF + classifier pipeline.
    
    `cleaned_texts` should be a list/Series of cleaned text documents
    (e.g. a sample of the training set) used as the background/explain set.
    
    Returns a dict with keys: available, method, values, feature_names, error
    - available: bool indicating if explanation succeeded
    - method: "SHAP"
    - values: SHAP values or None
    - feature_names: feature names or None
    - error: error message if explanation failed
    """
    if shap is None:
        logger.warning("SHAP not available: shap package not installed")
        return {
            "available": False,
            "method": "SHAP",
            "values": None,
            "feature_names": None,
            "error": "SHAP package not installed",
        }
    
    try:
        feature_step = pipeline.named_steps.get("features")
        classifier = pipeline.named_steps["classifier"]
        shap_classifier = _underlying_estimator(classifier)

        if "preprocess" in pipeline.named_steps:
            import pandas as pd
            from src.preprocessing import make_inference_frame
            rows = pd.concat([make_inference_frame(text) for text in cleaned_texts], ignore_index=True)
            transformed = pipeline.named_steps["preprocess"].transform(rows)
        else:
            transformed = cleaned_texts
        
        X_vec = feature_step.transform(transformed) if feature_step is not None else transformed
        feature_names = feature_step.get_feature_names_out() if feature_step is not None else []
        if X_vec.shape[1] != len(feature_names):
            raise ValueError("Transformed feature matrix does not match feature names")

        if isinstance(shap_classifier, LogisticRegression):
            # Dense input avoids SHAP returning a zero vector for sparse
            # matrices produced by the ColumnTransformer.
            shap_input = X_vec.toarray() if hasattr(X_vec, "toarray") else np.asarray(X_vec)
            background = np.zeros((1, shap_input.shape[1]), dtype=shap_input.dtype)
            explainer = shap.LinearExplainer(shap_classifier, background)
            shap_values = explainer(shap_input)
        elif isinstance(shap_classifier, RandomForestClassifier):
            explainer = shap.TreeExplainer(shap_classifier)
            shap_values = explainer(X_vec)
        else:
            explainer = shap.Explainer(shap_classifier, X_vec, feature_names=feature_names)
            shap_values = explainer(X_vec)
        result = {
            "available": True,
            "method": "SHAP",
            "values": shap_values,
            "feature_names": list(feature_names) if hasattr(feature_names, '__iter__') else [],
            "error": None,
        }
        if not top_shap_features_for_instance(result, top_n=1):
            result["available"] = False
            result["error"] = "SHAP returned no usable feature contributions"
        return result
    
    except Exception as exc:
        logger.warning("SHAP explanation failed: %s", exc)
        return {
            "available": False,
            "method": "SHAP",
            "values": None,
            "feature_names": None,
            "error": str(exc),
        }


def top_shap_features_for_instance(shap_result, instance_index=0, top_n=10):
    """
    Return the top contributing (feature, shap_value) pairs for one instance.
    
    Safe wrapper that returns empty list if explanation is unavailable.
    """
    if not shap_result.get("available") or shap_result.get("values") is None:
        return []
    
    try:
        shap_values = shap_result["values"]
        feature_names = shap_result.get("feature_names", [])
        
        if not hasattr(shap_values, 'values') or len(shap_values.values) <= instance_index:
            return []
        
        values = np.asarray(shap_values.values)[instance_index]
        if values.ndim == 2:
            values = values[:, 1] if values.shape[1] > 1 else values[:, 0]
        order = np.argsort(np.abs(values))[::-1][:top_n]
        return [(_display_feature_name(feature_names[i]), float(values[i]))
            for i in order
            if i < len(feature_names) and np.isfinite(values[i]) and not np.isclose(values[i], 0)]
    
    except Exception as exc:
        logger.warning("Failed to extract SHAP features: %s", exc)
        return []
