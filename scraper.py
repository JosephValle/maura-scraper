import feedparser
from datetime import datetime, timedelta
import time
from config import RSS_FEEDS, KEYWORDS, DAYS_LIMIT
from database import SessionLocal, Article
from sqlalchemy.exc import SQLAlchemyError
import ssl


def article_matches_keywords(article):
    """
    Check if an article's title or summary contains any of the specified keywords.
    Uses a simple substring check; consider using NLP for more robust matching.
    """
    text = (
        (article.get("title") or "") + " " + (article.get("summary") or "")
    ).lower()
    for keyword in KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


def get_published_date(entry):
    """
    Try to extract a datetime from entry. If 'published_parsed' is missing,
    fall back to 'updated_parsed'. Return None if both are unavailable.
    """
    published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published_struct:
        return None
    return datetime.fromtimestamp(time.mktime(published_struct))


def is_within_time_limit(published_dt):
    """
    Check if the article was published within the last DAYS_LIMIT days.
    """
    if published_dt is None:
        return False
    return datetime.now() - published_dt < timedelta(days=DAYS_LIMIT)


def scrape_articles():
    """
    Scrape RSS feeds for articles containing any of the KEYWORDS, published within DAYS_LIMIT.
    Store new matching articles in the database.
    """
    print("Starting article scraping...")
    session = SessionLocal()
    new_articles = 0

    for feed_url in RSS_FEEDS:

        print(f"Parsing feed: {feed_url}")
        ssl._create_default_https_context = ssl._create_unverified_context
        feed = feedparser.parse(feed_url)
        # If 'feed' is malformed, skip
        if feed.bozo:
            print(f" - Error parsing feed {feed_url}: possibly invalid RSS. Details: {feed.bozo_exception}")
            continue

        for entry in feed.entries:
            published_dt = get_published_date(entry)

            # Skip articles outside the time window
            if not is_within_time_limit(published_dt):
                continue

            # Skip articles that do not match keywords
            if not article_matches_keywords(entry):
                continue

            # Check if the article already exists in the database (by URL)
            article_url = entry.get("link") or ""
            existing = session.query(Article).filter(Article.url == article_url).first()
            if existing:
                continue  # Article is already stored

            # Parse summary if available
            summary = entry.get("summary") or ""

            # Create a new Article record
            article = Article(
                title=entry.get("title", "No Title"),
                url=article_url,
                published_date=published_dt,
                summary=summary,
                source=feed_url,
                content=""  # Content scraping not implemented in this example
            )
            session.add(article)
            new_articles += 1

    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error committing new articles to the database: {e}")
    finally:
        session.close()

    print(f"Article scraping finished. {new_articles} new articles added.")


# def scrape_linkedin_posts():
    """
    Placeholder for LinkedIn scraping.
    - Scraping LinkedIn posts reliably requires authentication and is subject to strict anti-scraping measures.
    - Consider using the LinkedIn API or an authorized 3rd-party platform for robust coverage.
    """
    # print("LinkedIn scraping is not implemented due to authentication/anti-scraping constraints.")


# -------------------------------------
# Placeholders for advanced monitoring
# -------------------------------------

def track_brand24_mentions():
    """
    Placeholder for integrating with Brand24's API.
    - Brand24 is a subscription-based service that allows you to track brand mentions across social media and the web.
    - For more info: https://brand24.com/api
    """
    pass


def track_meltwater_mentions():
    """
    Placeholder for integrating with Meltwater's API.
    - Meltwater provides media monitoring and PR analytics.
    - For more info, check: https://help.meltwater.com/en/
    """
    pass


def track_cision_press_releases():
    """
    Placeholder for Cision integration (PR Newswire).
    - Cision has a wide database of press releases and a media distribution network.
    - Typically requires subscription or API credentials.
    """
    pass


def track_google_alerts():
    """
    Placeholder for scraping or automating Google Alerts.
    - Google Alerts sends email alerts for new articles containing specified keywords.
    - Scripting direct scraping is against Google's ToS; consider using their email alerts or API-based solutions.
    """
    pass
