from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os

from feeds import fetch_articles
from scorer import score_article, compute_confidence, compute_theme_strength, compute_theme_matches, compute_sentiment
from heat_score import calculate_heat, compute_article_heat, compute_recency
from alerts import run_alerts
from timeline import save_snapshot, load_timeline

app = FastAPI()

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------
# CORE PIPELINE
# -----------------------------

def run_pipeline():
    print("🔄 Running NLP pipeline...")
    articles = fetch_articles()

    sst_payload = []

    for article in articles:
        match_scores = compute_theme_matches(article["text"])
        scores = score_article(article["text"])

        if not scores:
            continue

        strength = compute_theme_strength(match_scores)
        confidence = compute_confidence(match_scores)
        sentiment = compute_sentiment(article["text"])
        recency = compute_recency(article["published"])
        heat = compute_article_heat(
            match_scores,
            article["text"],
            article["published"],
            len(articles)
        )

        sst_payload.append({
            "title":        article["title"],
            "published":    article["published"],
            "source":       article["source"],
            "theme_scores": scores,
            "heat":         heat,
            "confidence":   confidence,
            "sentiment":    sentiment,
            "recency":      recency,
            "strength":     strength
        })

    heat = calculate_heat(articles)
    alerts = run_alerts(articles)
    save_snapshot(heat)

    # Save for SST engine
    with open("sst_input.json", "w") as f:
        json.dump({
            "heatmap":  heat,
            "articles": sst_payload,
            "alerts":   alerts
        }, f, indent=2)

    print("✅ Pipeline complete, sst_input.json updated")
    return heat, sst_payload, alerts


# -----------------------------
# AUTO REFRESH EVERY 30 MINS
# -----------------------------

scheduler = BackgroundScheduler()
scheduler.add_job(run_pipeline, "interval", minutes=30)
scheduler.start()


# -----------------------------
# ENDPOINTS
# -----------------------------

@app.get("/")
def root():
    return {"status": "Macro NLP Engine Running"}


@app.get("/heatmap")
def heatmap():
    articles = fetch_articles()
    heat = calculate_heat(articles)
    return {"heatmap": heat}


@app.get("/alerts")
def alerts():
    articles = fetch_articles()
    triggered = run_alerts(articles)
    return {"alerts": triggered}


@app.get("/articles")
def articles():
    articles = fetch_articles()
    results = []
    for article in articles:
        match_scores = compute_theme_matches(article["text"])
        scores = score_article(article["text"])
        if not scores:
            continue
        results.append({
            "title":      article["title"],
            "published":  article["published"],
            "source":     article["source"],
            "themes":     scores,
            "strength":   compute_theme_strength(match_scores),
            "confidence": compute_confidence(match_scores)
        })
    results.sort(key=lambda x: list(x["themes"].values())[0], reverse=True)
    return {"articles": results}


@app.get("/timeline")
def timeline():
    return {"timeline": load_timeline()}


@app.get("/snapshot")
def snapshot():
    articles = fetch_articles()
    heat = calculate_heat(articles)
    save_snapshot(heat)
    return {"status": "Snapshot saved", "scores": heat}


@app.get("/sst")
def sst():
    # SST engine writes its output here
    if os.path.exists("sst_output.json"):
        with open("sst_output.json") as f:
            return json.load(f)
    return {"status": "SST output not available yet"}


@app.get("/dashboard")
def dashboard():
    # Single endpoint that returns everything for the dashboard
    articles_data = fetch_articles()
    heat = calculate_heat(articles_data)
    alerts = run_alerts(articles_data)
    timeline = load_timeline()

    sst = {}
    if os.path.exists("sst_output.json"):
        with open("sst_output.json") as f:
            sst = json.load(f)

    return {
        "heatmap":  heat,
        "alerts":   alerts,
        "timeline": timeline[-5:],  # last 5 snapshots
        "sst":      sst
    }