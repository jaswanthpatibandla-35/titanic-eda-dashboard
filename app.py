"""
app.py - FastAPI application entry point for the Titanic EDA API.

Endpoints:
    GET  /                  → HTML dashboard
    GET  /api/health        → Health check
    GET  /api/summary       → Dataset overview statistics
    GET  /api/missing       → Missing value report
    GET  /api/correlation   → Correlation matrix
    GET  /api/survival      → Survival rate breakdowns
    GET  /api/charts        → List of generated chart URLs
    POST /api/run-eda       → Trigger (re)generation of all EDA artefacts
    GET  /charts/{name}     → Serve individual chart PNG
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Project imports ────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    APP_ENV,
    APP_HOST,
    APP_PORT,
    CACHE_MAX_SIZE,
    CACHE_TTL_SECONDS,
    CHARTS_DIR,
    DEBUG,
    LOG_LEVEL,
    REPORTS_DIR,
    STATIC_DIR,
    TEMPLATES_DIR,
)
from src.data_loader import get_data_dictionary, load_titanic
from src.eda_analysis import (
    correlation_matrix,
    full_quality_report,
    missing_value_report,
    survival_rates,
)
from src.utils import get_logger, save_json
from src.visualizations import generate_all_charts

# ── Logging ────────────────────────────────────────────────────────────────────
logger = get_logger("app", LOG_LEVEL)

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Titanic EDA API",
    description="Production-ready Exploratory Data Analysis API for the Titanic dataset.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────────────────
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# ── In-process cache ───────────────────────────────────────────────────────────
_cache: dict[str, dict[str, Any]] = {}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"] < CACHE_TTL_SECONDS):
        logger.debug("Cache HIT: %s", key)
        return entry["data"]
    return None


def _cache_set(key: str, data: Any) -> None:
    if len(_cache) >= CACHE_MAX_SIZE:
        oldest = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest]
    _cache[key] = {"data": data, "ts": time.time()}
    logger.debug("Cache SET: %s", key)


# ── Shared state (loaded once on startup) ─────────────────────────────────────
_df = None
_charts: dict[str, str] = {}


@app.on_event("startup")
async def startup_event() -> None:
    """Load dataset and generate charts on application startup."""
    global _df, _charts
    logger.info("=== Titanic EDA API starting up (%s) ===", APP_ENV)
    try:
        _df = load_titanic()
        logger.info("Dataset loaded: %d rows", len(_df))
        _charts = generate_all_charts(_df)
        logger.info("Charts generated: %d files", len(_charts))

        # Persist full quality report to disk
        report = full_quality_report(_df)
        save_json(report, REPORTS_DIR / "quality_report.json")
        logger.info("Quality report saved.")
    except Exception as exc:
        logger.error("Startup error: %s", exc, exc_info=True)


# ── Middleware: request timing ─────────────────────────────────────────────────

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-ms"] = f"{elapsed:.1f}"
    return response


# ── Helpers ────────────────────────────────────────────────────────────────────

def _require_df():
    """Raise 503 if the dataset has not been loaded yet."""
    if _df is None:
        raise HTTPException(status_code=503, detail="Dataset not yet loaded. Try again in a moment.")
    return _df


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
def health_check() -> dict:
    """
    Liveness / readiness probe.

    Returns:
        JSON with status, dataset row count, and chart count.
    """
    return {
        "status": "ok",
        "environment": APP_ENV,
        "dataset_rows": len(_df) if _df is not None else 0,
        "charts_generated": len(_charts),
    }


@app.get("/api/summary", tags=["EDA"])
def dataset_summary() -> JSONResponse:
    """Return high-level dataset statistics and data dictionary."""
    cached = _cache_get("summary")
    if cached:
        return JSONResponse(cached)

    df = _require_df()
    data = {
        "shape": {"rows": int(len(df)), "columns": int(len(df.columns))},
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "data_dictionary": get_data_dictionary(),
        "numeric_describe": df.describe().round(4).to_dict(),
    }
    _cache_set("summary", data)
    return JSONResponse(data)


@app.get("/api/missing", tags=["EDA"])
def missing_values() -> JSONResponse:
    """Return a per-column missing value report with recommendations."""
    cached = _cache_get("missing")
    if cached:
        return JSONResponse(cached)

    df = _require_df()
    report = missing_value_report(df)
    data = report.reset_index().rename(columns={"index": "column"}).to_dict(orient="records")
    _cache_set("missing", data)
    return JSONResponse(data)


@app.get("/api/correlation", tags=["EDA"])
def feature_correlation(method: str = "pearson") -> JSONResponse:
    """
    Return the feature correlation matrix.

    Query params:
        method: 'pearson' (default), 'spearman', or 'kendall'.
    """
    if method not in ("pearson", "spearman", "kendall"):
        raise HTTPException(status_code=422, detail="method must be one of: pearson, spearman, kendall")

    cache_key = f"correlation_{method}"
    cached = _cache_get(cache_key)
    if cached:
        return JSONResponse(cached)

    df = _require_df()
    corr = correlation_matrix(df, method=method)
    data = corr.to_dict()
    _cache_set(cache_key, data)
    return JSONResponse(data)


@app.get("/api/survival", tags=["EDA"])
def survival_breakdown() -> JSONResponse:
    """Return survival rate breakdowns by Sex, Pclass, Embarked, and Sex×Pclass."""
    cached = _cache_get("survival")
    if cached:
        return JSONResponse(cached)

    df = _require_df()
    rates = survival_rates(df)
    # Convert DataFrames to lists for JSON serialisation
    data = {k: v.to_dict(orient="records") for k, v in rates.items()}
    _cache_set("survival", data)
    return JSONResponse(data)


@app.get("/api/charts", tags=["Visualizations"])
def list_charts(request: Request) -> JSONResponse:
    """Return a list of generated charts with their URLs."""
    base = str(request.base_url).rstrip("/")
    chart_urls = {
        name: f"{base}/charts/{Path(path).name}"
        for name, path in _charts.items()
    }
    return JSONResponse({"count": len(chart_urls), "charts": chart_urls})


@app.post("/api/run-eda", tags=["EDA"])
def run_eda(force_download: bool = False) -> JSONResponse:
    """
    Trigger (re)generation of all EDA outputs.

    Query params:
        force_download: Re-download the dataset even if cached locally.
    """
    global _df, _charts
    try:
        _df = load_titanic(force_download=force_download)
        _charts = generate_all_charts(_df)
        report = full_quality_report(_df)
        save_json(report, REPORTS_DIR / "quality_report.json")
        _cache.clear()  # Invalidate stale cache entries
        return JSONResponse({
            "status": "success",
            "rows": len(_df),
            "charts_generated": len(_charts),
        })
    except Exception as exc:
        logger.error("EDA run failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard(request: Request) -> HTMLResponse:
    """Serve the interactive HTML dashboard."""
    template_path = TEMPLATES_DIR / "dashboard.html"
    if template_path.exists():
        return HTMLResponse(template_path.read_text(encoding="utf-8"))

    # Fallback minimal page when template is absent
    base = str(request.base_url).rstrip("/")
    chart_list = "".join(
        f'<img src="{base}/charts/{Path(p).name}" style="max-width:100%;margin:8px 0;border-radius:8px;">'
        for p in _charts.values()
    )
    return HTMLResponse(f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Titanic EDA</title>
    <style>body{{font-family:sans-serif;max-width:900px;margin:0 auto;padding:24px}}</style>
    </head><body><h1>🚢 Titanic EDA Dashboard</h1>
    <p><a href="/api/docs">API Docs →</a></p>
    {chart_list}</body></html>
    """)


# ── Dev server ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=DEBUG,
        log_level=LOG_LEVEL.lower(),
        workers=1,
    )
