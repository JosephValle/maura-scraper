import os

# Expanded keywords focusing on success metrics in nuclear & defense tech:
KEYWORDS = [
    "capacity factor",
    "unit capability factor",
    "safety system performance",
    "fuel performance",
    "artificial intelligence",
    "AI",
    "hypersonic",
    "hypersonics",
    "quantum computing",
    "quantum science",
    "rapid prototyping",
    "critical technology",
    "biotechnology",
    "advanced materials",
    "zero trust",
    "5G",
    "nuclear energy",
    "defense tech",
    "Musk",
    "nuclear-enabled",
]

# Add relevant RSS feeds for nuclear, defense, and aerospace news:
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.sciencedaily.com/rss/all.xml",
    "https://www.defensenews.com/rss/news/",
    "https://breakingdefense.com/feed/",
    "https://www.defense.gov/News/Press-Releases/rss/",
    "https://world-nuclear-news.org/RSS",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss"
]

# Database configuration (using a local SQLite file)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "articles.db")

# Only consider articles from the past X days (e.g., 30 days)
DAYS_LIMIT = 30

# Scheduler or scraping time (placeholder):
SCRAPE_TIME = "12:00"  # Daily at 12:00 local time (could be used with cron or APScheduler)
