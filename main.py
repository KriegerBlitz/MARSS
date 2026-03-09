import json
from feeds import fetch_articles
from scorer import score_article, compute_confidence, compute_theme_strength, compute_theme_matches, compute_sentiment
from heat_score import calculate_heat, display_heatmap, compute_article_heat, compute_recency
from alerts import run_alerts
from timeline import save_snapshot

def run():
    print("🔄 Fetching articles...\n")
    articles = fetch_articles()
    print(f"✅ Fetched {len(articles)} articles\n")

    # -----------------------------
    # SCORED ARTICLES
    # -----------------------------
    print("=" * 60)
    print("📰 TOP ARTICLES BY THEME SCORE")
    print("=" * 60)

    results = []
    sst_payload = []  # this goes to SST engine

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

        results.append({
            "title":      article["title"],
            "published":  article["published"],
            "source":     article["source"],
            "themes":     scores,
            "strength":   strength,
            "confidence": confidence
        })

        # Clean JSON for SST engine
        sst_payload.append({
            "title":        article["title"],
            "published":    article["published"],
            "source":       article["source"],
            "theme scores": scores,
            "heat":         heat,
            "confidence":   confidence,
            "sentiment":    sentiment,
            "recency":      recency,
            "strength":     strength
        })

    # Sort by top theme score
    results.sort(key=lambda x: list(x["themes"].values())[0], reverse=True)

    for r in results[:10]:
        print(f"\n📌 {r['title']}")
        print(f"   Published:  {r['published']}")
        print(f"   Strength:   {r['strength']}")
        print(f"   Confidence: {r['confidence']}")
        top_themes = list(r["themes"].items())[:3]
        print(f"   Themes:     {top_themes}")

    # -----------------------------
    # HEATMAP
    # -----------------------------
    print("\n")
    heat = calculate_heat(articles)
    display_heatmap(heat)

    # -----------------------------
    # SAVE SNAPSHOT
    # -----------------------------
    save_snapshot(heat)
    print("\n✅ Snapshot saved to timeline\n")

    # -----------------------------
    # ALERTS
    # -----------------------------
    print("=" * 60)
    print("🚨 ALERT CHECK")
    print("=" * 60)
    alerts = run_alerts(articles)
    if alerts:
        print(f"\n⚠️  {len(alerts)} ALERTS TRIGGERED\n")
        for alert in alerts:
            print(f"  [{alert['category']}] Trigger: '{alert['trigger']}'")
            print(f"  Title: {alert['title']}")
            print(f"  Published: {alert['published']}\n")
    else:
        print("No alerts triggered.")

    # -----------------------------
    # EXPORT JSON FOR SST ENGINE
    # -----------------------------
    with open("sst_input.json", "w") as f:
        json.dump({
            "heatmap":  heat,
            "articles": sst_payload,
            "alerts":   alerts
        }, f, indent=2)

    print("\n✅ SST input saved to sst_input.json\n")


if __name__ == "__main__":
    run()