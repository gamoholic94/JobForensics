# Fake Job Posting Detection using Explainable AI

A research project that detects fraudulent job postings using machine learning
and explains the learned signals with SHAP and LIME. The backend also provides
safe URL normalization, structured job-page extraction, contact-domain checks,
salary indicators, and a transparent non-probabilistic risk score.

## 🎯 Project Goals
- Build classical ML models (Logistic Regression, Random Forest, XGBoost) to
  classify job postings as **Real** or **Fake**.
- Use **Explainable AI (XAI)** techniques (SHAP, LIME) to interpret predictions
  at both the global (model-level) and local (single prediction) level.
- Provide an interactive app where a user can:
  - Paste a job description (JD) text,
  - Upload a text file, or
  - Paste a job posting URL (auto-scraped),
  and get back a prediction + confidence score + highlighted explanation of
  which words/phrases drove the decision.

## 📁 Project Structure
```
fake-job-detection-xai/
├── data/
│   ├── raw/               # original dataset (place fake_job_postings.csv here)
│   └── processed/         # cleaned/processed data
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_modeling.ipynb
│   └── 04_explainability.ipynb
├── src/
│   ├── preprocessing.py   # shared cleaning and feature engineering
│   ├── scraper.py         # bounded URL fetch and JSON-LD/page extraction
│   ├── url_analyzer.py    # URL validation and local domain indicators
│   ├── company_analyzer.py# contact/company-domain consistency checks
│   ├── salary_analyzer.py # conservative salary signals
│   ├── risk_engine.py     # explainable risk rules and aggregation
│   ├── model.py           # training / loading / prediction utilities
│   └── explain.py         # model-specific SHAP and LIME wrappers
├── models/                # saved trained model artifacts (.pkl)
├── api_server.py           # HTTP API for the deployed model service
├── reports/
│   └── figures/           # plots & results for the research write-up
├── requirements.txt
├── tests/
│   └── test_backend.py
└── README.md
```

## 📊 Dataset
This project is designed around the Kaggle **"Real or Fake Job Posting
Prediction"** dataset (EMSCAD), ~18,000 labeled job postings.

1. Download it from Kaggle:
   https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction
2. Place the CSV file at:
   `data/raw/fake_job_postings.csv`

(Alternatively, use the Kaggle API: `kaggle datasets download -d shivamb/real-or-fake-fake-jobposting-prediction`)

## ⚙️ Setup
```bash
cd fake-job-detection-xai
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## 🚀 Usage

### 1. Train the model
The source pipeline is the reproducible implementation. Run the training
script directly:
```bash
python -m src.model
```
This fits preprocessing, TF-IDF, categorical encoding, numeric scaling, and
the classifier using only the training split, then saves the complete pipeline
to `models/model.pkl`. Metrics include fraud precision, recall, F1, ROC-AUC,
average precision, and a confusion matrix. The test split is not used for
fitting, model selection, or calibration. The default classifier is balanced
logistic regression; the other supported choices are `random_forest` and
`xgboost`.

Calibration uses `CalibratedClassifierCV` with three internal training folds.
Training also reports Brier score as a calibration diagnostic. The unified
backend entry point `src.predict.analyze_posting()` returns model probability,
domain/company/salary/application/content analyses, the overall 0-100 risk
score, and evidence-based recommendations in one schema.

The available `models/model.pkl` artifact was trained with scikit-learn 1.7.1;
this version is pinned in `requirements.txt` so loading the serialized
pipeline is deterministic. The artifact tests load the real file and exercise
both normal and short inputs. Because model binaries are deployment artifacts,
a clean checkout must receive this file through artifact storage or a training
run before launching the app.

An optional `models/model_metadata.json` file can describe an artifact without
being required at runtime. Training prints evaluation metrics, but this
repository does not claim fixed metric values unless a training run produces
and records them.

The dataset is not included in this repository. Place it at
`data/raw/fake_job_postings.csv` before training. No metrics or trained model
are claimed until that file is available.

### 2. Launch the Python prediction API

The production frontend is the Next.js app in `jobguard-frontend-boilerplate`.
Vercel hosts that frontend, while this Python API hosts the model and analysis
pipeline. The model artifact is required at `models/model.pkl`.

```bash
uvicorn api_server:app --reload --port 8000
```

The API exposes `GET /health` and `POST /predict`. The frontend forwards its
same-origin `/api/predict` route to this service using the server-only
`BACKEND_API_URL` environment variable.

The backend returns a **model fake probability**, not a calibrated confidence
claim. A separate overall risk score combines documented starting weights for
model, domain, company, salary, application, and content indicators; it is not
a probability of fraud.

### Test the backend
```bash
pytest -q
```

## 🧪 Explainability and limitations
- **LIME** explains local text contributions using the same persisted pipeline.
- **SHAP** selects a linear explainer for logistic regression and a tree
  explainer for random forests; transformed feature names are retained and
  mapped to non-empty local contributors when the model has signal. If SHAP or
  LIME is unavailable or cannot produce a safe explanation, the main analysis
  still succeeds with a structured unavailable result.
- URL scraping uses requests, semantic HTML, and JSON-LD. JavaScript-only
  pages may return no description because browser automation is optional.
- Domain age, registrar, DNS, and trust scores are returned as unavailable
  unless a reliable external data source is added.
- Rules are risk indicators, not proof. A model prediction and external rules
  can disagree and should be interpreted separately.
- **Model Fake Probability** comes from the calibrated model's
  `predict_proba()` output. **Overall Risk Score** is a separate bounded 0-100
  weighted evidence score and is not a probability.
- Run `pytest -q` to execute the backend, artifact, XAI, and mocked end-to-end
  tests. Domain age, external company verification, and salary benchmarks may
  be unavailable; JavaScript-only pages may also fail to produce job text.

## 📄 License
For academic/research use.
