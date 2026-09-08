"""HTTP adapter for hosting the existing JobForensics pipeline outside Vercel."""

import base64
import binascii
import csv
import os
from io import BytesIO
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from pydantic import BaseModel

from src.model import MODEL_PATH, load_model
from src.predict import analyze_posting
from src.scraper import fetch_html, scrape_job

app = FastAPI(title="JobForensics Prediction API")

allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type"],
    )


class PredictionRequest(BaseModel):
    url: str = ""
    title: str = ""
    company_name: str = ""
    company: str = ""
    description: str = ""
    location: str = ""
    employment_type: str = ""
    application_url: str = ""
    file_name: str = ""
    file_content_base64: str = ""


class BatchPredictionRequest(BaseModel):
    file_name: str = ""
    file_content_base64: str = ""


@lru_cache(maxsize=1)
def get_model():
    return load_model(MODEL_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def extract_uploaded_text(request: PredictionRequest) -> str:
    if not request.file_content_base64:
        return ""
    try:
        content = base64.b64decode(request.file_content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="The uploaded file could not be read.") from exc

    if len(content) > 10_000_000:
        raise HTTPException(status_code=413, detail="Please upload a file smaller than 10 MB.")
    suffix = os.path.splitext(request.file_name.lower())[1]
    if suffix == ".txt":
        return content.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="The PDF could not be read. Try exporting it as TXT.") from exc
    raise HTTPException(status_code=415, detail="Please upload a PDF or TXT file.")


def is_google_form(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    return (
        hostname.endswith("forms.gle")
        or hostname.endswith("forms.google.com")
        or hostname.endswith("docs.google.com")
    )


def is_linkedin_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname == "linkedin.com" or hostname.endswith(".linkedin.com")


def scrape_google_form(url: str) -> str:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def predict_one(request: PredictionRequest) -> dict[str, Any]:
    job: dict[str, Any] = {
        "title": request.title,
        "company_name": request.company_name or request.company,
        "location": request.location,
        "employment_type": request.employment_type,
        "application_url": request.application_url,
    }
    text = request.description or extract_uploaded_text(request)
    source_warning = ""

    if request.url:
        try:
            if is_google_form(request.url):
                text = scrape_google_form(request.url)
            else:
                scraped = scrape_job(request.url)
                if not scraped.get("success"):
                    portal_name = "LinkedIn" if is_linkedin_url(request.url) else "the job portal"
                    text = (
                        f"{portal_name} job posting URL. The page content was unavailable to automated scraping. "
                        "Assess the source as limited evidence and recommend independent verification."
                    )
                    job["title"] = job.get("title") or f"{portal_name} job posting"
                    source_warning = (
                        f"{portal_name} limited access to the page, so this result is based on the URL and available source signals only. "
                        "Paste the job description or upload a PDF/TXT file for a fuller analysis."
                    )
                else:
                    text = scraped.get("description", "")
                    job.update({key: value for key, value in scraped.items() if value is not None})
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Unable to read the Google Forms link.") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="A job description or readable URL is required.")

    try:
        result = analyze_posting(get_model(), text, url=request.url, job=job, generate_xai=True)
        if source_warning:
            result["source_warning"] = source_warning
            result["recommendations"] = [source_warning, *result.get("recommendations", [])]
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="The model artifact is not installed on the prediction service.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job analysis failed.") from exc


@app.post("/predict")
def predict(request: PredictionRequest) -> dict[str, Any]:
    return predict_one(request)


@app.post("/predict/batch")
def predict_batch(request: BatchPredictionRequest) -> dict[str, Any]:
    if not request.file_content_base64:
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    try:
        content = base64.b64decode(request.file_content_base64, validate=True)
        rows = list(csv.DictReader(content.decode("utf-8-sig").splitlines()))
    except (binascii.Error, UnicodeDecodeError, csv.Error) as exc:
        raise HTTPException(status_code=400, detail="The CSV file could not be read.") from exc

    if len(content) > 3_000_000:
        raise HTTPException(status_code=413, detail="Please upload a CSV smaller than 3 MB.")
    if not rows:
        raise HTTPException(status_code=400, detail="The CSV file does not contain any job links.")
    if len(rows) > 50:
        raise HTTPException(status_code=400, detail="Please upload no more than 50 job links at once.")

    results: list[dict[str, Any]] = []
    url_names = {"url", "link", "job_url", "job link", "job_link"}
    for index, row in enumerate(rows, start=1):
        normalized = {str(key).strip().lower(): (value or "").strip() for key, value in row.items() if key}
        url = next((normalized[name] for name in url_names if normalized.get(name)), "")
        if not url and normalized:
            url = next(iter(normalized.values()), "")
        item = {
            "url": url,
            "title": normalized.get("title", ""),
            "company_name": normalized.get("company", normalized.get("company_name", "")),
            "location": normalized.get("location", ""),
            "employment_type": normalized.get("employment_type", ""),
        }
        try:
            if not url:
                raise HTTPException(status_code=400, detail="No job link found in this row.")
            results.append({"row": index, "url": url, "result": predict_one(PredictionRequest(**item))})
        except HTTPException as exc:
            results.append({"row": index, "url": url, "error": exc.detail})
        except Exception:
            results.append({"row": index, "url": url, "error": "Job analysis failed."})

    return {
        "success": True,
        "total": len(results),
        "completed": sum("result" in item for item in results),
        "failed": sum("error" in item for item in results),
        "results": results,
    }