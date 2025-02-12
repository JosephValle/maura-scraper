import os
from flask import Flask, request, jsonify
from database import SessionLocal, init_db, Article
from scheduler import start_scheduler, job

# Initialize the database (creates tables if they don't exist)
init_db()

app = Flask(__name__)

# Start the scheduler when the app starts
start_scheduler()

@app.route('/')
def index():
    return "Web Scraper API is running."

@app.route('/articles', methods=['GET'])
def get_articles():
    """
    Returns a paginated list of articles.
    Query parameters:
      - page (default: 1)
      - page_size (default: 10)
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    session = SessionLocal()
    query = session.query(Article).order_by(Article.published_date.desc())
    total = query.count()
    articles = query.offset((page - 1) * page_size).limit(page_size).all()
    session.close()

    articles_data = []
    for article in articles:
        articles_data.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "summary": article.summary,
            "source": article.source,
        })

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "articles": articles_data
    })

@app.route('/restart', methods=['POST'])
def restart():
    try:
        job()
        return jsonify({"message": "Restarted successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

if __name__ == '__main__':
    # For deployment, use the PORT environment variable if available
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
