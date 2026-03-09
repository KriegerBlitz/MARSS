<p align="center">
  <h1 align="center">Schroders Macro-Economic NLP Processing Engine (V2)</h1>
  <p align="center">
    <strong>Team MARSS — FinTech Hackathon</strong><br/>
    Advanced portfolio tracking with a 15-theme macro taxonomy, probabilistic event forecasting,<br/>
    and portfolio relevance tagging — powered by OpenAI Structured Outputs + FinBERT + spaCy.
  </p>
</p>

---

## Table of Contents

- [Overview](#overview)
- [What Changed in V2](#what-changed-in-v2)
- [Tech Stack](#tech-stack)
- [Architecture & Pipeline](#architecture--pipeline)
  - [Module 1 — Text Preprocessing](#module-1--text-preprocessing)
  - [Module 2 — LLM Structured Extraction](#module-2--llm-structured-extraction)
  - [Module 3 — Financial NER + Portfolio Relevance](#module-3--financial-ner--portfolio-relevance)
  - [Module 4 — Sentiment & Intensity (FinBERT)](#module-4--sentiment--intensity-finbert)
- [Project Structure](#project-structure)
- [15-Theme Macro Taxonomy](#15-theme-macro-taxonomy)
- [Input / Output Schemas](#input--output-schemas)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Example Usage](#example-usage)

---

## Overview

The **Schroders Macro-Economic NLP Engine** is a FastAPI-powered backend that ingests raw financial news articles and returns deeply structured macroeconomic insights. V2 introduces:

- **15-theme macro taxonomy** with strict enum enforcement
- **Probabilistic event forecasting** — 3 predicted future events with percentage odds
- **Portfolio relevance tagging** — extracts stock tickers, FX pairs, and commodities
- **OpenAI Structured Outputs** — single LLM call with guaranteed JSON schema matching
- **FinBERT sentiment** — financial-domain sentiment and intensity scoring

---

## What Changed in V2

| Feature | V1 | V2 |
|---------|-----|-----|
| Macro themes | 7 free-text themes | 15-value strict `MacroTheme` enum |
| LLM calls | 2 separate (classify + summarize) | 1 single call via `response_format` |
| Output guarantee | Manual JSON parsing | OpenAI Structured Outputs (schema-enforced) |
| Forecasting | None | `future_odds` — 3 events with probabilities |
| Portfolio tags | None | Tickers, FX pairs, commodities extraction |
| NER | GPE + ORG | GPE + ORG + MONEY + PRODUCT |
| Schemas | Inline in main.py | Dedicated `pydantic_models.py` |
| FinBERT | ✅ | ✅ (unchanged) |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | FastAPI + Uvicorn | Async HTTP server with OpenAPI docs |
| **Schema Enforcement** | Pydantic v2 | Strict I/O validation + OpenAI response_format |
| **Sentiment Analysis** | HuggingFace Transformers (`ProsusAI/finbert`) | Financial sentiment classification |
| **Named Entity Recognition** | spaCy (`en_core_web_sm`) | Geographies, organisations, money, products |
| **LLM Reasoning** | OpenAI API (`gpt-4o-mini`) | Structured extraction with JSON schema |
| **Data Processing** | pandas, NumPy | Batch processing, numerical ops |
| **Text Cleaning** | BeautifulSoup4, regex | HTML stripping, abbreviation normalization |
| **Runtime** | Python 3.12 + torch 2.5.1 (CPU) | ML-compatible runtime |

---

## Architecture & Pipeline

```
                         POST /api/v1/process_article
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────┐
    │                   V2 NLP PIPELINE                     │
    │                                                       │
    │  ┌─────────────┐    ┌────────────────────────────┐    │
    │  │  Module 1    │    │       Module 2              │    │
    │  │  Preprocess  │──▶│  LLM Structured Extraction  │    │
    │  │  (local)     │    │  (OpenAI response_format)   │    │
    │  └──────┬───────┘    │                            │    │
    │         │            │  → primary_macro_theme     │    │
    │         │            │  → summary (2 paragraphs)  │    │
    │         │            │  → future_odds (3 events)  │    │
    │         │            └────────────────────────────┘    │
    │         │                                             │
    │         ▼                                             │
    │  ┌─────────────────────┐  ┌───────────────────┐      │
    │  │     Module 3         │  │     Module 4       │      │
    │  │  NER + Portfolio     │  │  FinBERT Sentiment │      │
    │  │  Tags (spaCy+regex)  │  │  & Intensity       │      │
    │  │                     │  │                     │      │
    │  │  → named_entities   │  │  → sentiment_score  │      │
    │  │  → portfolio_tags   │  │  → intensity_score  │      │
    │  └─────────────────────┘  └───────────────────┘      │
    └──────────────────────┬────────────────────────────────┘
                           │
                           ▼
                  Merged JSON Response
```

### Module 1 — Text Preprocessing

**Function:** `preprocess_text()` | **Local, no API**

| Operation | Example |
|-----------|---------|
| HTML stripping | `<p>Fed hikes</p>` → `Fed hikes` |
| Financial abbreviations | `25bps` → `25 basis points`, `$5bn` → `$5 billion` |
| Period shorthands | `QoQ` → `quarter-over-quarter`, `YoY` → `year-over-year` |

### Module 2 — LLM Structured Extraction

**Function:** `extract_structured_insights()` | **OpenAI API (single call)**

Replaces V1's separate `classify_theme()` + `summarize_text()` with one optimised call using OpenAI's `response_format` parameter for **guaranteed JSON schema matching**.

The LLM returns an `NLPInsights` object:
- **`primary_macro_theme`**: one of 15 enum values (schema-enforced)
- **`summary`**: 2-paragraph macro briefing (drivers + implications)
- **`future_odds`**: 3 predicted events with percentage probabilities

### Module 3 — Financial NER + Portfolio Relevance

**Functions:** `extract_entities()` + `extract_portfolio_tags()` | **Local, no API**

| Source | What it catches | Examples |
|--------|----------------|----------|
| Regex | Stock tickers | `$AAPL`, `$TSLA`, `$MSFT` |
| Regex | Currency pairs | `EUR/USD`, `GBP/JPY` |
| Keyword match | Commodities | Gold, Crude Oil, Natural Gas |
| spaCy NER | Geographies (GPE) | United States, Euro Area |
| spaCy NER | Organisations (ORG) | Federal Reserve, OPEC |
| spaCy NER | Money (MONEY) | $95 a barrel |
| spaCy NER | Products (PRODUCT) | Brent crude |

### Module 4 — Sentiment & Intensity (FinBERT)

**Function:** `analyze_sentiment()` | **Local, no API**

- **Sentiment Score** (−1.0 to +1.0): FinBERT label × confidence
- **Intensity Score** (0.0 to 1.0): confidence + keyword boost (max +0.30)

---

## Project Structure

```
[FinTech Hackathon] Team MARSS/
├── .env.example              # Environment variable template
├── README.md                 # This documentation
├── requirements.txt          # Python dependencies
├── pydantic_models.py        # All schemas (MacroTheme enum, NLPInsights, I/O models)
├── main.py                   # FastAPI server
├── nlp_pipeline.py           # V2 pipeline modules + ModelManager
└── kaggle_batch_processor.py # CLI batch CSV enrichment (local models only)
```

---

## 15-Theme Macro Taxonomy

| # | Theme | Description |
|---|-------|-------------|
| 1 | `Inflation_Shock` | Unexpected inflation surge |
| 2 | `Disinflation` | Inflation declining / cooling |
| 3 | `Energy_Shock` | Oil/gas supply disruption or price spike |
| 4 | `Growth_Slowdown` | Decelerating GDP / economic activity |
| 5 | `Recession_Risk` | Elevated probability of economic contraction |
| 6 | `Growth_Reacceleration` | Recovery / re-acceleration signals |
| 7 | `Monetary_Tightening` | Rate hikes / hawkish central bank policy |
| 8 | `Monetary_Easing` | Rate cuts / dovish central bank policy |
| 9 | `Banking_Stress` | Bank failures, liquidity concerns |
| 10 | `Credit_Crunch` | Tightening lending standards, rising defaults |
| 11 | `Geopolitical_Escalation` | War, sanctions, trade conflicts |
| 12 | `Dollar_Strength` | USD appreciation / DXY surge |
| 13 | `Risk_Off` | Flight to safety, de-risking |
| 14 | `Risk_On` | Appetite for risk assets returning |
| 15 | `Volatility_Shock` | VIX spike, market turbulence |

---

## Input / Output Schemas

### Input — `ArticleInput`

```json
{
  "timestamp": "2026-03-06T12:00:00Z",
  "source_name": "Reuters",
  "source_type": "wire",
  "author": "Jane Doe",
  "headline": "Fed raises rates by 25bps amid persistent inflation",
  "body_text": "The Federal Reserve raised interest rates...",
  "url_reference": "https://reuters.com/article/fed-2026"
}
```

### Output — `ArticleOutput`

```json
{
  "status": "success",
  "processing_time_seconds": 2.847,
  "input_metadata": { "..." },
  "pipeline_result": {
    "cleaned_text": "Fed raises rates by 25 basis points...",
    "primary_macro_theme": "Monetary_Tightening",
    "summary": "The Federal Reserve raised interest rates by 25 basis points, driven by persistent inflationary pressures across the US economy. Chair Powell emphasized that the labor market remains tight and core services inflation has not yet shown convincing signs of moderation.\n\nThis hawkish move is expected to tighten financial conditions further, putting downward pressure on equity valuations and widening credit spreads. Emerging market currencies face heightened depreciation risk as the rate differential with the US widens.",
    "future_odds": [
      { "event": "Fed delivers another 25bp hike within 3 months", "probability": "62%" },
      { "event": "US 10Y yield breaches 5.0%", "probability": "45%" },
      { "event": "S&P 500 correction of 10%+ within 6 months", "probability": "38%" }
    ],
    "portfolio_relevance_tags": ["$SPY", "EUR/USD", "Gold"],
    "named_entities": {
      "geographies": ["US"],
      "organisations": ["Federal Reserve"]
    },
    "sentiment_score": -0.4521,
    "intensity_score": 0.8734
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `primary_macro_theme` | `MacroTheme` enum | One of 15 themes |
| `summary` | `string` | 2-paragraph macro briefing |
| `future_odds` | `FutureOdd[]` | 3 predicted events with probabilities |
| `portfolio_relevance_tags` | `string[]` | Tickers, FX pairs, commodities |
| `named_entities` | `NamedEntities` | Geographies + organisations |
| `sentiment_score` | `float [-1, 1]` | FinBERT directional sentiment |
| `intensity_score` | `float [0, 1]` | Signal strength / urgency |

---

## Getting Started

### Prerequisites

- **Python 3.12** (torch has DLL issues on 3.14)
- **OpenAI API key** (for the structured LLM extraction)

### Installation

```bash
# Install dependencies
py -3.12 -m pip install -r requirements.txt

# Download spaCy model
py -3.12 -m spacy download en_core_web_sm

# Copy env template and set your API key
copy .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-...
```

### Running the Server

```bash
py -3.12 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/health`

### Running the Batch Processor

```bash
# Enrich a CSV with local models (NER + FinBERT, no API costs)
py -3.12 kaggle_batch_processor.py --input data.csv --output enriched --format both
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health + model-load status |
| `POST` | `/api/v1/process_article` | Full V2 pipeline (returns `ArticleOutput`) |

---

## Example Usage

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/process_article \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-03-06T12:00:00Z",
    "source_name": "Bloomberg",
    "source_type": "wire",
    "author": "Markets Desk",
    "headline": "Oil surges past $95 on OPEC+ supply cuts",
    "body_text": "Brent crude surged past $95 a barrel after OPEC+ announced deeper-than-expected production cuts, raising fears of an energy-driven inflation shock across developed economies. The EUR/USD pair fell sharply as traders priced in prolonged ECB hawkishness. $XLE and $USO rallied while $SPY dropped 1.2%.",
    "url_reference": "https://bloomberg.com/oil-2026"
  }'
```

### Python

```python
import requests

resp = requests.post(
    "http://localhost:8000/api/v1/process_article",
    json={
        "timestamp": "2026-03-06T12:00:00Z",
        "source_name": "FT",
        "source_type": "research",
        "author": "Markets Desk",
        "headline": "Oil surges past $95 on OPEC+ supply cuts",
        "body_text": "Brent crude surged past $95 a barrel...",
        "url_reference": "https://ft.com/oil-2026",
    },
)

data = resp.json()["pipeline_result"]
print(f"Theme:     {data['primary_macro_theme']}")
print(f"Tags:      {data['portfolio_relevance_tags']}")
print(f"Sentiment: {data['sentiment_score']}")
print(f"Forecasts: {data['future_odds']}")
```

---

<p align="center"><em>Built for the FinTech Hackathon by Team MARSS</em></p>
