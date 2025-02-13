import feedparser
from datetime import datetime, timedelta
import time
from config import RSS_FEEDS, KEYWORDS, DAYS_LIMIT
from database import SessionLocal, Article
from sqlalchemy.exc import SQLAlchemyError
import ssl

def get_matched_tags(entry):
    """
    Returns a list of keywords (tags) that are found in the entry’s title or summary.
    """
    matched_tags = []
    text = ((entry.get("title") or "") + " " + (entry.get("summary") or "")).lower()
    for keyword in KEYWORDS:
        if keyword.lower() in text:
            matched_tags.append(keyword)
    return matched_tags

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
    print("Starting article scraping...")
    session = SessionLocal()
    new_articles = 0
    added_urls = set()  # Track URLs added in this run

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

            matched_tags = get_matched_tags(entry)
            if not matched_tags:
                continue

            article_url = entry.get("link") or ""
            # Check both the DB and our in-memory set.
            if session.query(Article).filter(Article.url == article_url).first() or article_url in added_urls:
                print(f"Skipping duplicate article: {article_url}")
                continue

            # Print a message if more than one tag is being added.
            # if len(matched_tags) > 1:
            #     print(f"Multiple tags detected for article {article_url}: {matched_tags}")

            summary = entry.get("summary") or ""
            # Fix: Join tags correctly without extra commas.
            tags_str = ",".join(matched_tags)

            article = Article(
                title=entry.get("title", "No Title"),
                url=article_url,
                published_date=published_dt,
                summary=summary,
                source=feed_url,
                tags=tags_str,
                content=""  # Content scraping not implemented in this example
            )
            session.add(article)
            added_urls.add(article_url)  # Remember this URL for the current run
            new_articles += 1

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error committing new articles to the database: {e}")
    finally:
        session.close()

    print(f"Article scraping finished. {new_articles} new articles added.")