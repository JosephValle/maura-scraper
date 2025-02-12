from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_articles

def job():
    print("Scheduled scraping job started.")
    scrape_articles()
    # scrape_linkedin_posts()
    print("Scheduled scraping job finished.")

from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_articles

def job():
    print("Scheduled scraping job started.")
    scrape_articles()
    # scrape_linkedin_posts()
    print("Scheduled scraping job finished.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run the scraping job immediately on startup
    print("Running initial scraping job on startup...")
    job()

    # Schedule the job to run daily at 12:00 PM
    scheduler.add_job(func=job, trigger="cron", hour=12, minute=0)
    scheduler.start()
    print("Scheduler started.")

