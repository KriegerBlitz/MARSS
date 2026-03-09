from themes import THEMES
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# Financial keywords for stronger sentiment detection
FINANCIAL_KEYWORDS = [
    "surge", "spike", "crisis", "shock", "collapse", "war",
    "inflation", "recession", "panic", "selloff", "tightening",
    "rate hike", "contagion", "default", "crash", "plunge"
]

def compute_sentiment(text):
    # VADER gives compound score between -1 and +1
    vader_score = analyzer.polarity_scores(text)["compound"]
    vader_intensity = abs(vader_score)  # we care about strength not direction

    # Count how many financial keywords appear
    keyword_count = sum(1 for k in FINANCIAL_KEYWORDS if k in text.lower())
    financial_intensity = min(keyword_count / 5, 1)  # cap at 1

    # Combine both: 60% VADER + 40% financial keywords
    sentiment = 0.6 * vader_intensity + 0.4 * financial_intensity

    return round(sentiment, 4)


def compute_theme_matches(text):
    text_lower = text.lower()
    scores = {}

    for theme, keywords in THEMES.items():
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        if matches > 0:
            scores[theme] = matches

    return scores  # returns {theme: keyword_match_count}


def compute_theme_strength(match_scores):
    if not match_scores:
        return 0

    values = list(match_scores.values())
    avg = sum(values) / len(values)
    maximum = max(values)

    # 60% average strength + 40% peak strength
    # divide by 3 to normalize (assuming max ~3 keyword matches normally)
    strength = 0.6 * (avg / 3) + 0.4 * (maximum / 3)

    return round(min(strength, 1), 4)  # cap at 1


def compute_confidence(match_scores):
    if not match_scores:
        return 0.5

    values = list(match_scores.values())
    avg = sum(values) / len(values)
    maximum = max(values)

    # How confident are we in the theme detection?
    # High max + high avg = high confidence
    confidence = 0.7 * (maximum / 3) + 0.3 * (avg / 3)

    return round(min(max(confidence, 0), 1), 4)


def score_article(text):
    # Step 1: count keyword matches per theme
    match_scores = compute_theme_matches(text)

    if not match_scores:
        return {}

    # Step 2: compute sentiment intensity
    sentiment = compute_sentiment(text)

    # Step 3: final score = matches * sentiment
    final_scores = {}
    for theme, matches in match_scores.items():
        final_scores[theme] = round(matches * sentiment, 4)

    # Step 4: sort highest first
    sorted_scores = dict(sorted(final_scores.items(), key=lambda x: x[1], reverse=True))

    return sorted_scores


if __name__ == "__main__":
    tests = [
        "The Federal Reserve raised interest rates again as CPI inflation hit 6.5%",
        "Oil prices surged after OPEC announced supply cuts",
        "Bank run fears spread after SVB collapse triggers panic selling"
    ]

    for text in tests:
        print(f"\nArticle: {text}")
        matches = compute_theme_matches(text)
        sentiment = compute_sentiment(text)
        strength = compute_theme_strength(matches)
        confidence = compute_confidence(matches)
        scores = score_article(text)

        print(f"  Sentiment:  {sentiment}")
        print(f"  Strength:   {strength}")
        print(f"  Confidence: {confidence}")
        print(f"  Themes:     {scores}")