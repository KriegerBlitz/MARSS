"""
Schroders Macro-Economic NLP Engine — Pydantic Models (V2)
==========================================================
Strictly-typed schemas for the 15-theme taxonomy, OpenAI Structured
Outputs, portfolio relevance tagging, and API request/response.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 15-Theme Macro Taxonomy
# ──────────────────────────────────────────────

class MacroTheme(str, Enum):
    """Exhaustive list of macro-economic themes the engine can classify."""

    Inflation_Shock = "Inflation_Shock"
    Disinflation = "Disinflation"
    Energy_Shock = "Energy_Shock"
    Growth_Slowdown = "Growth_Slowdown"
    Recession_Risk = "Recession_Risk"
    Growth_Reacceleration = "Growth_Reacceleration"
    Monetary_Tightening = "Monetary_Tightening"
    Monetary_Easing = "Monetary_Easing"
    Banking_Stress = "Banking_Stress"
    Credit_Crunch = "Credit_Crunch"
    Geopolitical_Escalation = "Geopolitical_Escalation"
    Dollar_Strength = "Dollar_Strength"
    Risk_Off = "Risk_Off"
    Risk_On = "Risk_On"
    Volatility_Shock = "Volatility_Shock"


# ──────────────────────────────────────────────
# LLM Structured Output Schema
# ──────────────────────────────────────────────

class FutureOdd(BaseModel):
    """A single probabilistic event forecast."""

    event: str = Field(
        ...,
        description="A concise description of a likely future macro event.",
    )
    probability: str = Field(
        ...,
        description="Estimated probability as a percentage string, e.g. '72%'.",
    )


class NLPInsights(BaseModel):
    """
    Schema passed to OpenAI's response_format for guaranteed JSON
    matching.  Contains the LLM-generated classification, briefing,
    and probabilistic forecasts.
    """

    primary_macro_theme: MacroTheme = Field(
        ...,
        description="The single best-matching macro theme from the 15-value taxonomy.",
    )
    summary: str = Field(
        ...,
        description="A dense, 2-paragraph macro-economic briefing on the article's impact.",
    )
    future_odds: list[FutureOdd] = Field(
        ...,
        description="The 3 most likely future related events with percentage probabilities.",
    )


# ──────────────────────────────────────────────
# Named Entities
# ──────────────────────────────────────────────

class NamedEntities(BaseModel):
    """Extracted named entities grouped by spaCy label."""

    geographies: list[str] = Field(default_factory=list)
    organisations: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# API Request
# ──────────────────────────────────────────────

class ArticleInput(BaseModel):
    """Incoming raw article payload."""

    timestamp: str = Field(
        ...,
        description="ISO-8601 timestamp of the article publication.",
        examples=["2026-03-06T12:00:00Z"],
    )
    source_name: str = Field(
        ...,
        description="Name of the news source.",
        examples=["Reuters"],
    )
    source_type: str = Field(
        ...,
        description="Type of source (e.g. wire, blog, research).",
        examples=["wire"],
    )
    author: str = Field(
        ...,
        description="Article author name.",
        examples=["Jane Doe"],
    )
    headline: str = Field(
        ...,
        description="Article headline.",
        examples=["Fed raises rates by 25bps"],
    )
    body_text: str = Field(
        ...,
        description="Full article body text (may contain HTML).",
    )
    url_reference: str = Field(
        ...,
        description="URL to the original article.",
        examples=["https://example.com/article/123"],
    )


# ──────────────────────────────────────────────
# API Response
# ──────────────────────────────────────────────

class PipelineResult(BaseModel):
    """
    Merged output from all pipeline stages:
      • LLM structured insights (theme, summary, future_odds)
      • spaCy NER (named_entities, portfolio_relevance_tags)
      • FinBERT (sentiment_score, intensity_score)
    """

    cleaned_text: str
    primary_macro_theme: MacroTheme
    summary: str
    future_odds: list[FutureOdd]
    portfolio_relevance_tags: list[str] = Field(
        default_factory=list,
        description="Stock tickers, currency pairs, and commodities extracted for portfolio relevance.",
    )
    named_entities: NamedEntities
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    intensity_score: float = Field(..., ge=0.0, le=1.0)


class ArticleOutput(BaseModel):
    """Full API response wrapping metadata + pipeline results."""

    status: str = "success"
    processing_time_seconds: float
    input_metadata: ArticleInput
    pipeline_result: PipelineResult


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = "healthy"
    timestamp: str
    models_loaded: dict[str, bool]
