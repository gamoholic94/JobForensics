# JobForensics implementation plan

## Audit baseline

The repository is a split application:

- **Backend:** FastAPI in `api_server.py`, with a scikit-learn pipeline in
  `src/model.py` and shared preprocessing in `src/preprocessing.py`.
- **Analysis services:** URL normalization and SSRF checks in
  `src/url_analyzer.py` and `src/scraper.py`; company, application, salary,
  content-rule, and weighted-risk analyzers under `src/`.
- **Explainability:** LIME and SHAP adapters in `src/explain.py`.
- **Frontend:** Next.js 16/React 19 in `frontend/`, using same-origin API
  routes that proxy to the FastAPI service.
- **Data and artifacts:** EMSCAD CSV under `data/raw/`; the persisted model is
  expected at `models/model.pkl`. There is no application database.
- **Validation:** Backend tests cover preprocessing, URL safety, scraping,
  analysis, explainability, and mocked end-to-end behavior. The frontend has
  build dependencies but no automated UI test suite.

## Feature classification

| Area | Status | Evidence / limitation |
| --- | --- | --- |
| URL, text, PDF, and TXT input | IMPLEMENTED | `frontend/components/detection/job-scanner.tsx`, `api_server.py` |
| Bounded HTML and JSON-LD extraction | IMPLEMENTED | `src/scraper.py` |
| SSRF and unsafe redirect protection | IMPLEMENTED | `src/url_analyzer.py`, `src/scraper.py`; continue regression testing |
| ML fake-job prediction | IMPLEMENTED | Persisted scikit-learn pipeline in `models/model.pkl` when installed |
| Weighted, explainable risk rules | IMPLEMENTED | `src/risk_engine.py` and analyzers under `src/` |
| LIME/SHAP explanations | PARTIALLY IMPLEMENTED | Graceful unavailable responses exist; availability depends on installed packages and compatible artifacts |
| Structured result display | PARTIALLY IMPLEMENTED | Result screen previously used hardcoded risk values; source metadata was not displayed |
| Batch CSV analysis | IMPLEMENTED | Backend and frontend proxy exist; processing is synchronous and capped at 50 rows |
| Company identity verification | PARTIALLY IMPLEMENTED | Local domain/contact consistency checks only; no authoritative company registry or DNS/WHOIS provider |
| Public reviews and complaint analysis | PARTIALLY IMPLEMENTED | Reddit post analysis is available through the public JSON endpoint with bounded comments and source metadata; no review-provider or authenticity integration exists |
| Evidence correlation and evidence chain | PARTIALLY IMPLEMENTED | Analyzer outputs are returned as signals; complete analysis results can now be persisted as investigations, but there is not yet a user-scoped evidence timeline |
| Downloadable investigation reports | PARTIALLY IMPLEMENTED | Saved investigations can download self-contained HTML reports; PDF export is not yet implemented |
| Data-backed dashboard red flags | IMPLEMENTED | Dashboard indicators are aggregated from saved investigations through `GET /investigations/stats`, with an honest empty state |
| Authentication and user-specific history | PARTIALLY IMPLEMENTED | SQLite-backed save/list/get endpoints and an API-backed History page now exist; authentication and user scoping are still missing |
| Rate limiting and abuse controls | PARTIALLY IMPLEMENTED | Input and response bounds exist; production rate limiting and authentication are still required |
| External credentials/data sources | NEEDS EXTERNAL CREDENTIALS OR DATA SOURCE | Reddit public JSON works without credentials; review, registry, DNS/WHOIS, and domain reputation checks require selected providers and keys |
| Deployment | PARTIALLY IMPLEMENTED | Render/Vercel configuration and environment-variable proxying exist; model artifact delivery remains an operational prerequisite |

## Implementation order

1. Keep the current API contract stable while making result fields fully
   evidence-based and preserving source metadata.
2. Add a persistent investigation/case schema and replace static frontend
   dashboard/history data with API-backed records. The first SQLite-backed
   save/list/get slice is now implemented; user scoping remains.
3. Add report generation from stored evidence, including model version,
   unavailable integrations, timestamps, and source URLs.
4. Add optional, explicitly configured company/review/domain providers. Each
   provider must return provenance and an unavailable state instead of
   fabricated results.
5. Keep authentication out of scope unless the product requirements change;
   add request rate limiting, structured request IDs, and operational logging
   before public deployment.
6. Add frontend and API contract tests for loading, empty, partial, error, and
   unavailable-integration states.

## Acceptance criteria

- Every displayed score and explanation is derived from the API response; no
  production UI value is hardcoded as an analysis result.
- Unsafe schemes, private/local destinations, unsafe redirects, oversized
  responses, and unsupported content types are rejected with explicit errors.
- Missing fields and unavailable providers remain visible as unavailable rather
  than being inferred or replaced with synthetic data.
- A saved investigation can be reproduced from its source URL, timestamp,
  model metadata, structured fields, rule evidence, and provider provenance.
- Backend tests and the frontend production build pass without weakening
  existing API behavior.
