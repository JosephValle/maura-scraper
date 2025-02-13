import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import SessionLocal, init_db, Article
from scheduler import start_scheduler, job

# Initialize the database (this now clears the db on every start)
init_db()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Start the scheduler when the app starts
start_scheduler()

@app.route('/')
def index():
    return "Web Scraper API is running."


@app.route('/articles', methods=['GET'])
def get_articles():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # Retrieve tags from the query parameters.
    # This supports multiple values, e.g. /articles?tags=tag1&tags=tag2.
    tags_param = request.args.getlist('tags')
    # If tags_param is an empty list or contains an empty string, treat it as no filter.
    if tags_param == [''] or not tags_param:
        tags_param = None

    session = SessionLocal()
    query = session.query(Article)

    # If tags_param is provided, filter articles that contain at least one of the tags.
    if tags_param:
        from sqlalchemy import or_
        conditions = []
        for tag in tags_param:
            # Since our tags are stored as a comma-delimited string like ",tag1,tag2,"
            # this will match only if the tag exists as a whole word.
            conditions.append(Article.tags.like(f'%,{tag},%'))
        query = query.filter(or_(*conditions))
    
    query = query.order_by(Article.published_date.desc())
    total = query.count()
    articles = query.offset((page - 1) * page_size).limit(page_size).all()

    print(f"Query fetched {len(articles)} articles.")  # Debug print
    session.close()

    articles_data = []
    for article in articles:
        tags_list = article.tags.strip(',').split(',') if article.tags else []
        articles_data.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "summary": article.summary,
            "source": article.source,
            "tags": tags_list,
        })

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "articles": articles_data
    })



@app.route('/tags', methods=['GET'])
def get_tags():
    """
    Returns a unique list of tags found across all stored articles.
    """
    session = SessionLocal()
    # Only select the 'tags' field from each article.
    articles = session.query(Article.tags).filter(Article.tags != None).all()
    session.close()
    
    tag_set = set()
    for (tags_str,) in articles:
        if tags_str:
            # Our tags are stored as ",tag1,tag2," so we remove the extra commas and split.
            tags = tags_str.strip(',').split(',')
            tag_set.update(tags)
    
    return jsonify(list(tag_set))

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
