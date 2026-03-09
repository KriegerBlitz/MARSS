import json
import os
from datetime import datetime
from heat_score import calculate_heat
from feeds import fetch_articles

TIMELINE_FILE = "timeline.json"

def load_timeline():
    if os.path.exists(TIMELINE_FILE):
        with open(TIMELINE_FILE, "r") as f:
            return json.load(f)
    return []


def save_snapshot(heat_scores):
    timeline = load_timeline()
    snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scores": heat_scores
    }
    timeline.append(snapshot)
    with open(TIMELINE_FILE, "w") as f:
        json.dump(timeline, f, indent=2)
    print(f"✅ Snapshot saved at {snapshot['timestamp']}")


def display_timeline():
    timeline = load_timeline()
    if not timeline:
        print("No timeline data yet.")
        return

    print("\n📈 MACRO THEME TIMELINE")
    print("=" * 60)
    for snapshot in timeline:
        print(f"\n🕐 {snapshot['timestamp']}")
        for theme, score in snapshot["scores"].items():
            if score > 5:    bar = "🔴 HOT  "
            elif score > 2:  bar = "🟡 WARM "
            else:            bar = "🟢 COOL "
            print(f"   {bar}  {theme:<30} {round(score, 4)}")
        print("-" * 60)


def theme_history(theme_name):
    timeline = load_timeline()
    if not timeline:
        print("No timeline data yet.")
        return

    print(f"\n📊 History for: {theme_name}")
    print("=" * 60)
    for snapshot in timeline:
        score = snapshot["scores"].get(theme_name, 0)
        if score > 5:    bar = "🔴"
        elif score > 2:  bar = "🟡"
        else:            bar = "🟢"
        print(f"  {snapshot['timestamp']}  {bar}  {round(score, 4)}")


if __name__ == "__main__":
    articles = fetch_articles()
    heat = calculate_heat(articles)
    save_snapshot(heat)
    display_timeline()
    theme_history("Geopolitical_Escalation")