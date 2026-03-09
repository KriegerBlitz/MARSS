ALERT_TRIGGERS = {
    "Geopolitical": [
        "declares war", "military strike", "invasion begins",
        "nuclear launch", "missile attack", "coup", "assassination",
        "war declared", "troops deployed", "airstrike"
    ],
    "Monetary": [
        "emergency rate cut", "surprise rate hike", "Fed intervenes",
        "emergency meeting", "unscheduled Fed", "central bank emergency"
    ],
    "Banking": [
        "bank failure", "bank collapse", "bank run",
        "FDIC seizure", "emergency bailout", "bank nationalized"
    ],
    "Market": [
        "circuit breaker", "trading halted", "market crash",
        "flash crash", "market suspended", "black monday"
    ],
    "Energy": [
        "oil embargo", "pipeline explosion", "Strait of Hormuz closed",
        "OPEC emergency", "energy emergency", "nuclear plant"
    ]
}

def check_alerts(article):
    text_lower = article["text"].lower()
    triggered = []

    for category, triggers in ALERT_TRIGGERS.items():
        for phrase in triggers:
            if phrase.lower() in text_lower:
                triggered.append({
                    "category": category,
                    "trigger": phrase,
                    "title": article["title"],
                    "source": article["source"],
                    "published": article["published"]
                })

    return triggered


def run_alerts(articles):
    all_alerts = []
    for article in articles:
        alerts = check_alerts(article)
        all_alerts.extend(alerts)
    return all_alerts


if __name__ == "__main__":
    from CODE.MARSS.feeds import fetch_articles
    articles = fetch_articles()
    alerts = run_alerts(articles)

    if alerts:
        print(f"\n🚨 {len(alerts)} ALERTS TRIGGERED\n")
        print("=" * 60)
        for alert in alerts:
            print(f"⚠️  [{alert['category']}] Trigger: '{alert['trigger']}'")
            print(f"   Title: {alert['title']}")
            print(f"   Source: {alert['source']}")
            print(f"   Published: {alert['published']}")
            print("-" * 60)
    else:
        print("No alerts triggered.")