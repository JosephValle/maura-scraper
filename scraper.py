# scraper.py
import feedparser
from datetime import datetime, timedelta
import time
import ssl
from sqlalchemy.exc import SQLAlchemyError

from config import RSS_FEEDS, DAYS_LIMIT
from database import SessionLocal, Article, Keyword

def load_keywords(session):
    """Return a list of lowercased keywords from DB; empty list if none."""
    rows = session.query(Keyword.value).all()
    return [v for (v,) in rows]

def get_matched_tags(entry, keywords_lower):
    """
    Returns list of *original* matched keywords (as in DB, lowercased).
    We’ll return them lowercased (DB format) and display/serialize as-is later.
    """
    text = ((entry.get("title") or "") + " " + (entry.get("summary") or "")).lower()
    return [kw for kw in keywords_lower if kw in text]

def get_published_date(entry):
    published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published_struct:
        return None
    return datetime.fromtimestamp(time.mktime(published_struct))

def is_within_time_limit(published_dt):
    if published_dt is None:
        return False
    return datetime.now() - published_dt < timedelta(days=DAYS_LIMIT)

def scrape_articles():
    print("Starting article scraping...")
    session = SessionLocal()
    new_articles = 0
    added_urls = set()

    try:
        keywords = load_keywords(session)  # lowercased, unique
        if not keywords:
            print("No keywords configured; skipping scrape.")
            return

        for feed_url in RSS_FEEDS:
            print(f"Parsing feed: {feed_url}")
            ssl._create_default_https_context = ssl._create_unverified_context
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                print(f" - Error parsing feed {feed_url}: possibly invalid RSS. Details: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                published_dt = get_published_date(entry)
                if not is_within_time_limit(published_dt):
                    continue

                matched_tags = get_matched_tags(entry, keywords)
                if not matched_tags:
                    continue

                article_url = entry.get("link") or ""
                if not article_url:
                    continue

                if session.query(Article).filter(Article.url == article_url).first() or article_url in added_urls:
                    print(f"Skipping duplicate article: {article_url}")
                    continue

                summary = entry.get("summary") or ""

                # Store tags as ",tag1,tag2," for consistent filtering
                unique_tags = sorted(set(matched_tags))
                tags_str = "," + ",".join(unique_tags) + "," if unique_tags else ""

                article = Article(
                    title=entry.get("title", "No Title"),
                    url=article_url,
                    published_date=published_dt,
                    summary=summary,
                    source=feed_url,
                    tags=tags_str,
                    content=""
                )
                session.add(article)
                added_urls.add(article_url)
                new_articles += 1

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during scraping: {e}")
    finally:
        session.close()

    print(f"Article scraping finished. {new_articles} new articles added.")
