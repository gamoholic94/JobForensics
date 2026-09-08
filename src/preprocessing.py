"""
Text cleaning and feature engineering utilities for the
Fake Job Posting Detection project.
"""
import re
import string
import pandas as pd

TEXT_COLUMNS = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
]

CATEGORICAL_COLUMNS = [
    "employment_type",
    "required_experience",
    "required_education",
    "industry",
    "function",
]

BINARY_COLUMNS = [
    "telecommuting",
    "has_company_logo",
    "has_questions",
]

TARGET_COLUMN = "fraudulent"


def clean_text(text: str) -> str:
    """Normalize job text while preserving useful fraud-related words."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML tags
    text = re.sub(r"https?://\S+|www\.\S+", " url ", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", " email ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def combine_text_fields(df: pd.DataFrame, columns=None) -> pd.Series:
    """Concatenate the relevant text columns into a single text field."""
    columns = columns or TEXT_COLUMNS
    available = [c for c in columns if c in df.columns]
    if not available:
        return pd.Series("", index=df.index, dtype="string")
    combined = df[available].fillna("").astype(str).agg(" ".join, axis=1)
    return combined.apply(clean_text)


def load_raw_dataset(path: str) -> pd.DataFrame:
    """Load the raw EMSCAD fake job postings CSV."""
    df = pd.read_csv(path)
    return df


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Full preprocessing pipeline: clean text, fill NAs, engineer features."""
    df = df.copy()

    # Keep the original columns so this function can be the first pipeline step.
    for col in TEXT_COLUMNS:
        if col not in df:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    for col in CATEGORICAL_COLUMNS:
        if col not in df:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown").astype(str)
    for col in BINARY_COLUMNS:
        if col not in df:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(0, 1).astype(int)

    # Combined, cleaned text field used for TF-IDF / model input
    df["text"] = combine_text_fields(df)

    # Simple engineered signal features often useful for fake-job detection
    df["text_length"] = df["text"].str.len().astype(float)
    salary = df.get("salary_range", pd.Series("", index=df.index)).fillna("").astype(str)
    df["has_salary_range"] = salary.str.strip().ne("").astype(int)
    salary_numbers = salary.str.findall(r"\d+(?:[,.]\d+)?").apply(
        lambda values: [float(value.replace(",", "")) for value in values]
    )
    df["salary_min"] = salary_numbers.apply(lambda values: min(values) if values else 0.0)
    df["salary_max"] = salary_numbers.apply(lambda values: max(values) if values else 0.0)
    df["salary_midpoint"] = ((df["salary_min"] + df["salary_max"]) / 2).where(
        df["has_salary_range"].eq(1), 0.0
    )

    return df


def prepare_features_and_target(df: pd.DataFrame):
    """Return raw rows and the target for a leakage-safe sklearn pipeline."""
    X = df.drop(columns=[TARGET_COLUMN], errors="ignore")
    y = df[TARGET_COLUMN] if TARGET_COLUMN in df.columns else None
    return X, y


def preprocess_single_text(raw_text: str) -> str:
    """Return the normalized text for callers that only need text cleaning."""
    return clean_text(raw_text)


def make_inference_frame(raw_text: str, **fields) -> pd.DataFrame:
    """Build one raw posting row for the persisted model pipeline."""
    row = {column: "" for column in TEXT_COLUMNS}
    row["description"] = raw_text or ""
    row.update(fields)
    if not str(row.get("salary_range", "") or "").strip():
        row["salary_range"] = raw_text or ""
    return pd.DataFrame([row])
