"""
Schroders Macro-Economic NLP Processing Engine (V2)
====================================================
Upgraded pipeline with:
  • Single LLM call via OpenAI Structured Outputs
  • 15-theme macro taxonomy
  • Probabilistic event forecasting
  • Portfolio relevance tagging (tickers, FX pairs, commodities)
  • FinBERT sentiment & intensity (unchanged)

Modules:
    1. Text Preprocessing
    2. LLM Structured Extraction  (theme + summary + future_odds)
    3. Financial NER + Portfolio Relevance Tags
    4. Sentiment & Intensity Analysis (FinBERT)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import numpy as np
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError

from pydantic_models import (
    MacroTheme,
    FutureOdd,
    NLPInsights,
    NamedEntities,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

INTENSITY_KEYWORDS: list[str] = [
    "surge", "surged", "plunge", "plunged", "crash", "crashed",
    "soar", "soared", "collapse", "collapsed", "spike", "spiked",
    "tumble", "tumbled", "skyrocket", "skyrocketed", "plummet",
    "plummeted", "unprecedented", "historic", "crisis", "catastrophe",
    "panic", "meltdown", "freefall", "extreme", "severe", "dramatic",
    "aggressive", "massive", "sharply", "steeply", "abruptly",
]

# Common commodities for portfolio tag extraction
COMMODITIES: set[str] = {
    "gold", "silver", "platinum", "palladium", "copper", "iron ore",
    "crude oil", "brent", "wti", "natural gas", "lng",
    "wheat", "corn", "soybeans", "coffee", "sugar", "cocoa", "cotton",
    "lithium", "nickel", "zinc", "aluminium", "aluminum", "tin", "uranium",
}

# Regex: stock tickers like $AAPL, $TSLA, $MSFT
_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")

# Regex: currency pairs like EUR/USD, GBP/JPY, USD/CNY
_FX_PAIR_RE = re.compile(
    r"\b([A-Z]{3})/([A-Z]{3})\b"
)

LLM_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))


# ──────────────────────────────────────────────
# Model Manager (lazy singleton)
# ──────────────────────────────────────────────

class ModelManager:
    """Lazily loads heavy ML models once and caches them."""

    _instance: ModelManager | None = None

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._spacy_model = None
            cls._instance._finbert_pipeline = None
            cls._instance._openai_client = None
        return cls._instance

    # ── spaCy ─────────────────────────────────

    @property
    def spacy_nlp(self):
        """Load spaCy en_core_web_sm on first access."""
        if self._spacy_model is None:
            import spacy
            logger.info("Loading spaCy en_core_web_sm …")
            try:
                self._spacy_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning(
                    "spaCy model not found – downloading en_core_web_sm …"
                )
                from spacy.cli import download
                download("en_core_web_sm")
                self._spacy_model = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded.")
        return self._spacy_model

    # ── FinBERT ───────────────────────────────

    @property
    def finbert(self):
        """Load ProsusAI/finbert sentiment pipeline on first access."""
        if self._finbert_pipeline is None:
            from transformers import pipeline as hf_pipeline
            logger.info("Loading ProsusAI/finbert …")
            self._finbert_pipeline = hf_pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT model loaded.")
        return self._finbert_pipeline

    # ── OpenAI ────────────────────────────────

    @property
    def openai(self) -> OpenAI:
        """Return a configured OpenAI client."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise EnvironmentError(
                    "OPENAI_API_KEY is not set. "
                    "Add it to your .env file or environment variables."
                )
            self._openai_client = OpenAI(
                api_key=api_key,
                timeout=LLM_TIMEOUT,
            )
        return self._openai_client


models = ModelManager()


# ══════════════════════════════════════════════
# MODULE 1 — Text Preprocessing
# ══════════════════════════════════════════════

def preprocess_text(raw_text: str) -> str:
    """
    Clean raw article text:
      • Strip HTML tags
      • Normalise financial symbols & abbreviations
      • Collapse whitespace
    """
    text = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ")

    text = re.sub(r"\bbps?\b", "basis points", text, flags=re.IGNORECASE)
    text = re.sub(r"\bbn\b", "billion", text, flags=re.IGNORECASE)
    text = re.sub(r"\btrn\b", "trillion", text, flags=re.IGNORECASE)
    text = re.sub(r"\bmn\b", "million", text, flags=re.IGNORECASE)
    text = re.sub(r"\bQoQ\b", "quarter-over-quarter", text)
    text = re.sub(r"\bYoY\b", "year-over-year", text)
    text = re.sub(r"\bMoM\b", "month-over-month", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text


# ══════════════════════════════════════════════
# MODULE 2 — LLM Structured Extraction
#             (replaces old classify + summarize)
# ══════════════════════════════════════════════

_THEME_LIST = ", ".join(t.value for t in MacroTheme)

_STRUCTURED_SYSTEM_PROMPT = f"""\
You are a senior macro-economic research analyst at Schroders.

Analyze the provided financial article and return a JSON object matching the \
required schema exactly.

INSTRUCTIONS:
1. **primary_macro_theme**: Classify the article into exactly ONE theme from \
this list: [{_THEME_LIST}]. Pick the single best match.
2. **summary**: Write a dense, 2-paragraph macro-economic briefing. \
Paragraph 1 covers what happened and the immediate drivers. \
Paragraph 2 covers forward-looking implications for global markets and portfolios.
3. **future_odds**: Predict the 3 most likely future related macro events \
with percentage probabilities based on historical market behaviour. \
Each entry needs an 'event' (concise description) and a 'probability' \
(e.g. "72%").\
"""

# Build the JSON schema dict for OpenAI's response_format
_NLP_INSIGHTS_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "NLPInsights",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "primary_macro_theme": {
                    "type": "string",
                    "enum": [t.value for t in MacroTheme],
                    "description": "The single best-matching macro theme.",
                },
                "summary": {
                    "type": "string",
                    "description": "A dense 2-paragraph macro-economic briefing.",
                },
                "future_odds": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event": {
                                "type": "string",
                                "description": "Concise description of a likely future event.",
                            },
                            "probability": {
                                "type": "string",
                                "description": "Estimated probability, e.g. '72%'.",
                            },
                        },
                        "required": ["event", "probability"],
                        "additionalProperties": False,
                    },
                    "description": "3 most likely future related events.",
                },
            },
            "required": ["primary_macro_theme", "summary", "future_odds"],
            "additionalProperties": False,
        },
    },
}


def extract_structured_insights(text: str) -> NLPInsights:
    """
    Single OpenAI call using Structured Outputs (response_format)
    to extract theme classification, 2-paragraph briefing, and
    3 probabilistic event forecasts.

    Returns an NLPInsights model, or a fallback on failure.
    """
    try:
        response = models.openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _STRUCTURED_SYSTEM_PROMPT},
                {"role": "user", "content": text[:6000]},
            ],
            response_format=_NLP_INSIGHTS_SCHEMA,
            temperature=0.2,
            max_tokens=1000,
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return NLPInsights(**parsed)

    except (APITimeoutError, APIConnectionError) as exc:
        logger.error("LLM timeout/connection error: %s", exc)
    except RateLimitError as exc:
        logger.error("LLM rate-limit hit: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error in extract_structured_insights: %s", exc)

    # Fallback
    return NLPInsights(
        primary_macro_theme=MacroTheme.Risk_Off,
        summary="Analysis unavailable due to an API error.",
        future_odds=[
            FutureOdd(event="Unable to generate forecast", probability="N/A"),
        ],
    )


# ══════════════════════════════════════════════
# MODULE 3 — Financial NER + Portfolio Relevance
# ══════════════════════════════════════════════

def extract_entities(text: str) -> NamedEntities:
    """
    spaCy NER: extract deduplicated geographies (GPE) and
    organisations (ORG).
    """
    doc = models.spacy_nlp(text[:100_000])

    geographies: set[str] = set()
    organisations: set[str] = set()

    for ent in doc.ents:
        cleaned = ent.text.strip()
        if not cleaned:
            continue
        if ent.label_ == "GPE":
            geographies.add(cleaned)
        elif ent.label_ == "ORG":
            organisations.add(cleaned)

    return NamedEntities(
        geographies=sorted(geographies),
        organisations=sorted(organisations),
    )


def extract_portfolio_tags(text: str) -> list[str]:
    """
    Extract portfolio-relevant tags from the text:
      • Stock tickers  ($AAPL, $TSLA, etc.)
      • Currency pairs  (EUR/USD, GBP/JPY, etc.)
      • Commodities     (crude oil, gold, etc.)
      • spaCy MONEY / PRODUCT entities
    """
    tags: set[str] = set()

    # 1. Regex — stock tickers
    for match in _TICKER_RE.finditer(text):
        tags.add(f"${match.group(1)}")

    # 2. Regex — currency pairs
    for match in _FX_PAIR_RE.finditer(text):
        pair = f"{match.group(1)}/{match.group(2)}"
        tags.add(pair)

    # 3. Keyword — commodities
    text_lower = text.lower()
    for commodity in COMMODITIES:
        if commodity in text_lower:
            tags.add(commodity.title())

    # 4. spaCy — MONEY and PRODUCT entities
    doc = models.spacy_nlp(text[:100_000])
    for ent in doc.ents:
        if ent.label_ in ("MONEY", "PRODUCT"):
            cleaned = ent.text.strip()
            if cleaned and len(cleaned) > 1:
                tags.add(cleaned)

    return sorted(tags)


# ══════════════════════════════════════════════
# MODULE 4 — Sentiment & Intensity (FinBERT)
# ══════════════════════════════════════════════

_LABEL_MAP: dict[str, float] = {
    "positive": 1.0,
    "negative": -1.0,
    "neutral": 0.0,
}


def analyze_sentiment(text: str) -> dict[str, float]:
    """
    Run FinBERT on the text and compute:
      • sentiment_score  (-1.0 … 1.0)
      • intensity_score  ( 0.0 … 1.0)
    """
    truncated = text[:1500]
    result = models.finbert(truncated)[0]

    label: str = result["label"].lower()
    confidence: float = float(result["score"])

    sentiment_score = _LABEL_MAP.get(label, 0.0) * confidence

    lower_text = text.lower()
    keyword_hits = sum(1 for kw in INTENSITY_KEYWORDS if kw in lower_text)
    keyword_boost = min(keyword_hits * 0.05, 0.3)
    intensity_score = float(np.clip(confidence + keyword_boost, 0.0, 1.0))

    return {
        "sentiment_score": round(sentiment_score, 4),
        "intensity_score": round(intensity_score, 4),
    }


# ══════════════════════════════════════════════
# Full Pipeline Orchestrator
# ══════════════════════════════════════════════

def run_full_pipeline(headline: str, body_text: str) -> dict[str, Any]:
    """
    Execute all V2 modules sequentially:
        1. Text Preprocessing
        2. LLM Structured Extraction (theme + summary + forecasts)
        3. Financial NER + Portfolio Relevance Tags
        4. Sentiment & Intensity (FinBERT)

    Returns a merged dict ready for PipelineResult.
    """
    combined_raw = f"{headline}. {body_text}"

    # 1 — Preprocessing
    cleaned = preprocess_text(combined_raw)

    # 2 — LLM Structured Extraction (single call)
    insights = extract_structured_insights(cleaned)

    # 3 — NER + Portfolio Tags
    entities = extract_entities(cleaned)
    portfolio_tags = extract_portfolio_tags(cleaned)

    # 4 — Sentiment & Intensity
    sentiment = analyze_sentiment(cleaned)

    return {
        "cleaned_text": cleaned,
        "primary_macro_theme": insights.primary_macro_theme,
        "summary": insights.summary,
        "future_odds": [fo.model_dump() for fo in insights.future_odds],
        "portfolio_relevance_tags": portfolio_tags,
        "named_entities": entities.model_dump(),
        "sentiment_score": sentiment["sentiment_score"],
        "intensity_score": sentiment["intensity_score"],
    }


def run_local_pipeline(headline: str, body_text: str) -> dict[str, Any]:
    """
    Run only local modules (no LLM) — for batch processing.
    Modules: Preprocessing → NER + Portfolio Tags → FinBERT.
    """
    combined_raw = f"{headline}. {body_text}"

    cleaned = preprocess_text(combined_raw)
    entities = extract_entities(cleaned)
    portfolio_tags = extract_portfolio_tags(cleaned)
    sentiment = analyze_sentiment(cleaned)

    return {
        "cleaned_text": cleaned,
        "named_entities": entities.model_dump(),
        "portfolio_relevance_tags": portfolio_tags,
        "sentiment_score": sentiment["sentiment_score"],
        "intensity_score": sentiment["intensity_score"],
    }
