"""
Schroders Macro-Economic NLP Processing Engine — FastAPI Server (V2)
====================================================================
Exposes a POST endpoint that runs the V2 NLP pipeline on a financial
news article and returns structured macroeconomic insights with
15-theme taxonomy, probabilistic forecasts, and portfolio relevance tags.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from pydantic_models import (
    ArticleInput,
    ArticleOutput,
    PipelineResult,
    NamedEntities,
    FutureOdd,
    MacroTheme,
    HealthResponse,
)
from nlp_pipeline import ModelManager, run_full_pipeline

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Application Lifespan (model pre-loading)
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load heavy ML models at startup."""
    logger.info("🚀  Starting model pre-load …")
    manager = ModelManager()

    try:
        _ = manager.spacy_nlp
        logger.info("✅  spaCy model ready.")
    except Exception as exc:
        logger.error("❌  Failed to load spaCy model: %s", exc)

    try:
        _ = manager.finbert
        logger.info("✅  FinBERT model ready.")
    except Exception as exc:
        logger.error("❌  Failed to load FinBERT model: %s", exc)

    logger.info("🟢  Server is ready to accept requests.")
    yield
    logger.info("🔴  Shutting down …")


# ──────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────

app = FastAPI(
    title="Schroders Macro-Economic NLP Engine (V2)",
    description=(
        "Ingests raw financial news articles and returns structured "
        "macroeconomic insights via a 15-theme taxonomy, probabilistic "
        "event forecasting, portfolio relevance tagging, and FinBERT "
        "sentiment analysis — all powered by OpenAI Structured Outputs."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return server health and model-load status."""
    manager = ModelManager()
    return HealthResponse(
        timestamp=datetime.utcnow().isoformat() + "Z",
        models_loaded={
            "spacy_en_core_web_sm": manager._spacy_model is not None,
            "finbert": manager._finbert_pipeline is not None,
        },
    )


@app.post(
    "/api/v1/process_article",
    response_model=ArticleOutput,
    status_code=status.HTTP_200_OK,
    tags=["Pipeline"],
    summary="Process a financial news article (V2)",
    description=(
        "Runs the V2 pipeline: preprocessing → LLM structured extraction "
        "(theme + summary + forecasts) → NER + portfolio tags → FinBERT "
        "sentiment. Returns a single merged JSON payload."
    ),
)
async def process_article(article: ArticleInput) -> ArticleOutput:
    """
    Accept a raw financial news article and run the V2 pipeline:
        1. Text Preprocessing
        2. LLM Structured Extraction (theme, summary, future_odds)
        3. Financial NER + Portfolio Relevance Tags
        4. Sentiment & Intensity Analysis (FinBERT)
    """
    logger.info(
        "Processing article: '%s' from %s",
        article.headline[:80],
        article.source_name,
    )
    start = time.perf_counter()

    try:
        result = run_full_pipeline(
            headline=article.headline,
            body_text=article.body_text,
        )
    except Exception as exc:
        logger.exception("Pipeline failed for article: %s", article.headline)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing error: {exc}",
        )

    elapsed = round(time.perf_counter() - start, 3)
    logger.info("Pipeline completed in %.3fs", elapsed)

    return ArticleOutput(
        processing_time_seconds=elapsed,
        input_metadata=article,
        pipeline_result=PipelineResult(
            cleaned_text=result["cleaned_text"],
            primary_macro_theme=result["primary_macro_theme"],
            summary=result["summary"],
            future_odds=[FutureOdd(**fo) for fo in result["future_odds"]],
            portfolio_relevance_tags=result["portfolio_relevance_tags"],
            named_entities=NamedEntities(**result["named_entities"]),
            sentiment_score=result["sentiment_score"],
            intensity_score=result["intensity_score"],
        ),
    )


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
