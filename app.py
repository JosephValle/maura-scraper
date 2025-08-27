# server.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import SessionLocal, init_db, Article, Keyword
from scheduler import start_scheduler, job
from sqlalchemy import or_

# Initialize DB (no longer clears by default; set RESET_DB=1 to clear Articles)
init_db()

app = Flask(__name__)
CORS(app)

start_scheduler()

@app.route('/')
def index():
    return "Web Scraper API is running."

# ------------------ KEYWORDS CRUD ------------------

@app.route('/keywords', methods=['GET'])
def list_keywords():
    """Return all keywords (lowercased, DB canonical form)."""
    with SessionLocal() as s:
        rows = s.query(Keyword).order_by(Keyword.value.asc()).all()
        return jsonify([r.value for r in rows])

@app.route('/keywords', methods=['POST'])
def add_keywords():
    """
    Add one or more keywords.
    Accepts:
      - {"keyword": "Hypersonic"}
      - {"keywords": ["Hypersonic", "Nuclear microgrid", "..."]}
    """
    data = request.get_json(silent=True) or {}
    raw = []
    if "keyword" in data and isinstance(data["keyword"], str):
        raw = [data["keyword"]]
    elif "keywords" in data and isinstance(data["keywords"], list):
        raw = [x for x in data["keywords"] if isinstance(x, str)]
    else:
        return jsonify({"error": "Provide 'keyword' (string) or 'keywords' (list of strings)."}), 400

    # Normalize and dedupe
    incoming = []
    seen = set()
    for k in raw:
        v = k.strip().lower()
        if v and v not in seen:
            seen.add(v)
            incoming.append(v)

    if not incoming:
        return jsonify({"added": [], "skipped": [], "message": "No valid keywords."}), 200

    added, skipped = [], []
    with SessionLocal() as s:
        existing_set = {v for (v,) in s.query(Keyword.value).all()}
        for v in incoming:
            if v in existing_set:
                skipped.append(v)
                continue
            s.add(Keyword(value=v))
            added.append(v)
        s.commit()

    return jsonify({"added": added, "skipped": skipped}), 200

@app.route('/keywords', methods=['DELETE'])
def delete_keywords_bulk():
    """
    Remove keywords by JSON body:
      {"keywords": ["hypersonic", "nuclear microgrid"]}
    Case-insensitive (we store lowercased).
    """
    data = request.get_json(silent=True) or {}
    to_remove = [x.strip().lower() for x in data.get("keywords", []) if isinstance(x, str)]
    if not to_remove:
        return jsonify({"error": "Provide 'keywords' as a non-empty list of strings."}), 400

    removed, not_found = [], []
    with SessionLocal() as s:
        existing = {v: kid for (kid, v) in s.query(Keyword.id, Keyword.value).all()}
        for v in to_remove:
            kid = existing.get(v)
            if kid:
                s.query(Keyword).filter(Keyword.id == kid).delete()
                removed.append(v)
            else:
                not_found.append(v)
        s.commit()
    return jsonify({"removed": removed, "not_found": not_found}), 200

@app.route('/keywords/<path:value>', methods=['DELETE'])
def delete_keyword_single(value):
    """Remove a single keyword via URL path (percent-encode spaces)."""
    v = (value or "").strip().lower()
    if not v:
        return jsonify({"error": "Keyword cannot be empty."}), 400
    with SessionLocal() as s:
        row = s.query(Keyword).filter(Keyword.value == v).first()
        if not row:
            return jsonify({"removed": [], "not_found": [v]}), 200
        s.delete(row)
        s.commit()
        return jsonify({"removed": [v], "not_found": []}), 200

# ------------------ ARTICLES ------------------

@app.route('/articles', methods=['GET'])
def get_articles():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    tags_param = request.args.getlist('tags')
    if tags_param == [''] or not tags_param:
        tags_param = None

    with SessionLocal() as session:
        query = session.query(Article)

        if tags_param:
            conditions = []
            for tag in tags_param:
                conditions.append(Article.tags.like(f'%,{tag.lower()},%'))
            query = query.filter(or_(*conditions))

        query = query.order_by(Article.published_date.desc())
        total = query.count()
        articles = query.offset((page - 1) * page_size).limit(page_size).all()

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
    with SessionLocal() as session:
        articles = session.query(Article.tags).filter(Article.tags != None).all()
    tag_set = set()
    for (tags_str,) in articles:
        if tags_str:
            tags = tags_str.strip(',').split(',')
            tag_set.update(tags)
    return jsonify(sorted(tag_set))

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
