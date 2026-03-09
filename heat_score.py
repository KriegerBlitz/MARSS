import json
import os
import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from feeds import fetch_articles
from scorer import score_article, compute_theme_strength, compute_confidence

# -----------------------------
# STEP 1 — RECENCY SCORE
# -----------------------------

def compute_recency(published_str):
    # Convert RSS date string to datetime object
    try:
        dt = parsedate_to_datetime(published_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except:
        return 0.6  # default if date parsing fails

    now = datetime.now(timezone.utc)
    hours_ago = (now - dt).total_seconds() / 3600

    # Stepped recency — simpler and more interpretable than decay
    if hours_ago < 6:   return 1.0   # breaking news
    if hours_ago < 24:  return 0.8   # today
    if hours_ago < 72:  return 0.6   # last 3 days
    if hours_ago < 168: return 0.4   # last week
    return 0.2                        # older


# -----------------------------
# STEP 2 — HEAT SCORE PER ARTICLE
# -----------------------------

def compute_article_heat(match_scores, text, published_str, article_count=1):

    # How strongly are themes present in this article?
    theme_strength = compute_theme_strength(match_scores)

    # How emotionally intense is the language?
    from scorer import compute_sentiment
    sentiment = compute_sentiment(text)

    # How recent is this article?
    recency = compute_recency(published_str)

    # How many articles cover this today? (normalized, cap at 1)
    volume_score = min(article_count / 10, 1)

    # Weighted formula:
    # 40% theme strength + 30% sentiment + 20% recency + 10% volume
    heat = (
        0.4 * theme_strength +
        0.3 * sentiment +
        0.2 * recency +
        0.1 * volume_score
    )

    return round(min(max(heat, 0), 1), 4)  # clamp between 0 and 1


# -----------------------------
# STEP 3 — AGGREGATE HEAT PER THEME
# -----------------------------

def calculate_heat(articles):
    # Count how many articles mention each theme
    theme_article_counts = {}
    for article in articles:
        scores = score_article(article["text"])
        for theme in scores:
            theme_article_counts[theme] = theme_article_counts.get(theme, 0) + 1

    # Now calculate heat for each article and accumulate per theme
    theme_heat = {}

    for article in articles:
        from scorer import compute_theme_matches
        match_scores = compute_theme_matches(article["text"])

        if not match_scores:
            continue

        for theme, matches in match_scores.items():
            article_count = theme_article_counts.get(theme, 1)

            heat = compute_article_heat(
                {theme: matches},        # just this theme's matches
                article["text"],         # full article text
                article["published"],    # publish date
                article_count            # how many articles cover this theme
            )

            if theme not in theme_heat:
                theme_heat[theme] = 0

            # Accumulate heat across all articles
            theme_heat[theme] += heat

    # Sort hottest first
    sorted_heat = dict(sorted(theme_heat.items(), key=lambda x: x[1], reverse=True))
    return sorted_heat


# -----------------------------
# STEP 4 — DISPLAY
# -----------------------------

def display_heatmap(heat):
    print("\n🌡️  MACRO THEME HEATMAP")
    print("=" * 60)
    for theme, score in heat.items():
        if score > 5:    bar = "🔴 HOT  "
        elif score > 2:  bar = "🟡 WARM "
        else:            bar = "🟢 COOL "
        print(f"{bar}  {theme:<30} {round(score, 4)}")


if __name__ == "__main__":
    articles = fetch_articles()
    heat = calculate_heat(articles)
    display_heatmap(heat)