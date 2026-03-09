"""
Kaggle Batch Processor
=======================
Loads a large CSV file in chunks, runs each row through the local
NLP modules (preprocessing, NER, FinBERT sentiment), and exports
an enriched dataset.

Usage:
    python kaggle_batch_processor.py --input data.csv --output enriched --format both
    python kaggle_batch_processor.py --input data.csv --chunksize 1000

Notes:
    • Only local models are used (no LLM API calls) to keep batch
      processing free and fast.
    • The script auto-detects text columns by looking for common
      names: body_text, text, content, article, headline, title.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

# Pipeline imports (local-only modules)
from nlp_pipeline import (
    preprocess_text,
    extract_entities,
    analyze_sentiment,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# Columns we look for automatically when --text-col is not provided
_AUTO_DETECT_COLS: list[str] = [
    "body_text", "text", "content", "article", "body",
    "headline", "title", "summary", "description",
]


def detect_text_column(columns: list[str]) -> str | None:
    """Try to find a text column by matching common names."""
    lower_map = {c.lower(): c for c in columns}
    for candidate in _AUTO_DETECT_COLS:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def process_row(text: str) -> dict[str, Any]:
    """Run local NLP modules on a single row of text."""
    cleaned = preprocess_text(text)
    entities = extract_entities(cleaned)
    sentiment = analyze_sentiment(cleaned)

    return {
        "cleaned_text": cleaned,
        "geographies": "; ".join(entities["geographies"]),
        "organisations": "; ".join(entities["organisations"]),
        "sentiment_score": sentiment["sentiment_score"],
        "intensity_score": sentiment["intensity_score"],
    }


def run_batch(
    input_path: str,
    output_path: str,
    text_col: str | None,
    chunksize: int,
    output_format: str,
) -> None:
    """
    Main batch processing loop.

    Parameters
    ----------
    input_path : str
        Path to the input CSV file.
    output_path : str
        Base name for output files (extension added automatically).
    text_col : str | None
        Name of the column containing body text.  Auto-detected if None.
    chunksize : int
        Number of rows per chunk.
    output_format : str
        One of "csv", "json", or "both".
    """
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error("Input file not found: %s", input_file)
        sys.exit(1)

    # Peek at headers to find the text column
    sample = pd.read_csv(input_file, nrows=0)
    columns = list(sample.columns)

    if text_col is None:
        text_col = detect_text_column(columns)
        if text_col is None:
            logger.error(
                "Could not auto-detect a text column from: %s. "
                "Please specify --text-col.",
                columns,
            )
            sys.exit(1)
        logger.info("Auto-detected text column: '%s'", text_col)
    elif text_col not in columns:
        logger.error("Column '%s' not found in CSV.", text_col)
        sys.exit(1)

    # Count total rows for the progress bar
    total_rows = sum(1 for _ in open(input_file, encoding="utf-8")) - 1
    logger.info("Processing %d rows in chunks of %d …", total_rows, chunksize)

    all_results: list[pd.DataFrame] = []
    start = time.perf_counter()

    reader = pd.read_csv(input_file, chunksize=chunksize, encoding="utf-8")

    with tqdm(total=total_rows, desc="Processing", unit="row") as pbar:
        for chunk in reader:
            enriched_rows: list[dict[str, Any]] = []

            for idx, row in chunk.iterrows():
                raw_text = str(row.get(text_col, ""))
                if not raw_text.strip():
                    enriched_rows.append({
                        "cleaned_text": "",
                        "geographies": "",
                        "organisations": "",
                        "sentiment_score": 0.0,
                        "intensity_score": 0.0,
                    })
                else:
                    enriched_rows.append(process_row(raw_text))
                pbar.update(1)

            enriched_df = pd.DataFrame(enriched_rows, index=chunk.index)
            combined = pd.concat([chunk, enriched_df], axis=1)
            all_results.append(combined)

    final_df = pd.concat(all_results, ignore_index=True)
    elapsed = round(time.perf_counter() - start, 2)
    logger.info("Processing complete in %.2fs", elapsed)

    # ── Export ───────────────────────────────
    output_base = Path(output_path)

    if output_format in ("csv", "both"):
        csv_path = output_base.with_suffix(".csv")
        final_df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("CSV saved → %s (%d rows)", csv_path, len(final_df))

    if output_format in ("json", "both"):
        json_path = output_base.with_suffix(".json")
        final_df.to_json(json_path, orient="records", indent=2, force_ascii=False)
        logger.info("JSON saved → %s (%d rows)", json_path, len(final_df))


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-process a CSV of financial articles through "
                    "local NLP models (spaCy NER + FinBERT sentiment).",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output", "-o",
        default="output_enriched",
        help="Base name for output files (default: output_enriched).",
    )
    parser.add_argument(
        "--text-col",
        default=None,
        help="Name of the CSV column containing body text. "
             "Auto-detected if not provided.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=500,
        help="Rows per chunk (default: 500).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "json", "both"],
        default="both",
        help="Output format (default: both).",
    )

    args = parser.parse_args()

    run_batch(
        input_path=args.input,
        output_path=args.output,
        text_col=args.text_col,
        chunksize=args.chunksize,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
