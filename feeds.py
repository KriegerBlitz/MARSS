import requests
from bs4 import BeautifulSoup

FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.investing.com/rss/news.rss",
    "https://feeds.skynews.com/feeds/rss/business.xml",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://finance.yahoo.com/rss/topfinstories",
    
]
def fetch_articles():
    articles = []
    for url in FEEDS:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "xml")
            # xml refers to extendible markup language, which is used for RSS feeds
            items = soup.find_all("item")
            for item in items:
                title = item.find("title").get_text(strip=True) if item.find("title") else ""
                summary = item.find("description").get_text(strip=True) if item.find("description") else ""
                published = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
                link = item.find("link").get_text(strip=True) if item.find("link") else ""
                articles.append({
                    "title": title,
                    "text": title + " " + summary,
                    "published": published,
                    "link": link,
                    "source": url
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return articles


if __name__ == "__main__":
    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles")
    for a in articles[:3]:
        print(f"\n  Source: {a['source']}")
        print(f"  Title: {a['title']}")
        print(f"  Published: {a['published']}")