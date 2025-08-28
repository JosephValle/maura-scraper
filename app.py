# server.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import SessionLocal, init_db, Article, Keyword
from scheduler import start_scheduler, job
from sqlalchemy import or_

# ------------------ APP / BOOTSTRAP ------------------

# Initialize DB (no longer clears by default; set RESET_DB=1 to clear Articles)
init_db()

app = Flask(__name__)
CORS(app)

start_scheduler()

TAGS_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tags.json")

def _canon_token(t: str) -> str:
    # Canonical tag token for matching
    return (t or "").strip().lower()

def _canon_tags_expr():
    """
    SQL expression that normalizes Article.tags for robust LIKE matching:
    - lowercases the whole string
    - removes single spaces adjacent to commas: ', ' -> ',' and ' ,' -> ','
      (handles the common 'comma + optional space' formatting issue)
    """
    # func.replace is nested: first ', ' → ',', then ' ,' → ','
    no_space_adjacent_commas = func.replace(
        func.replace(Article.tags, ', ', ','), ' ,', ','
    )
    return func.lower(no_space_adjacent_commas)

def _parse_tags_query_args():
    """
    Accepts both:
      /articles?tags=alpha&tags=beta
    and
      /articles?tags=alpha,beta
    Returns a list of canonical tokens (trimmed, lowercased), deduped.
    """
    # getlist captures repeated ?tags=...
    items = request.args.getlist('tags')
    # If client sent a single comma-joined value, split it
    if len(items) == 1 and ',' in items[0]:
        items = [p for p in items[0].split(',')]

    out = []
    seen = set()
    for raw in items:
        tok = _canon_token(raw)
        if tok and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out

# --- has_articles enrichment ----------------------------------------------

def _tags_with_has_articles(session, base_tags):
    """
    base_tags: Iterable[str] tag names as displayed (not necessarily canonicalized).
    Robustly check existence regardless of whitespace/case artifacts in DB.
    """
    results = []
    canon_expr = _canon_tags_expr()
    for t in base_tags:
        if not t:
            continue
        tok = _canon_token(t)
        if not tok:
            results.append({"tag": t, "has_articles": False})
            continue
        pattern = f'%,{tok},%'
        exists = session.query(Article.id).filter(canon_expr.like(pattern)).first() is not None
        results.append({"tag": t, "has_articles": bool(exists)})
    return results

def _load_canonical_tags():
    """
    Load canonical tags from the JSON store.
    Returns a list or None if the store doesn't exist or is invalid.
    """
    if not os.path.exists(TAGS_STORE_PATH):
        return None
    try:
        with open(TAGS_STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("tags"), list):
            # Preserve order as stored
            return data["tags"]
    except Exception:
        pass
    return None


def _save_canonical_tags(tags_list):
    """
    Save canonical tags to the JSON store. Expects a list of strings.
    Does not alter order or content; caller guarantees shape.
    """
    tmp_path = TAGS_STORE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"tags": tags_list}, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, TAGS_STORE_PATH)


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
def _canon_token(t: str) -> str:
    # Canonical tag token for matching
    return (t or "").strip().lower()

def _canon_tags_expr():
    """
    SQL expression that normalizes Article.tags for robust LIKE matching:
    - lowercases the whole string
    - removes single spaces adjacent to commas: ', ' -> ',' and ' ,' -> ','
      (handles the common 'comma + optional space' formatting issue)
    """
    # func.replace is nested: first ', ' → ',', then ' ,' → ','
    no_space_adjacent_commas = func.replace(
        func.replace(Article.tags, ', ', ','), ' ,', ','
    )
    return func.lower(no_space_adjacent_commas)

def _parse_tags_query_args():
    """
    Accepts both:
      /articles?tags=alpha&tags=beta
    and
      /articles?tags=alpha,beta
    Returns a list of canonical tokens (trimmed, lowercased), deduped.
    """
    # getlist captures repeated ?tags=...
    items = request.args.getlist('tags')
    # If client sent a single comma-joined value, split it
    if len(items) == 1 and ',' in items[0]:
        items = [p for p in items[0].split(',')]

    out = []
    seen = set()
    for raw in items:
        tok = _canon_token(raw)
        if tok and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out

# --- has_articles enrichment ----------------------------------------------

def _tags_with_has_articles(session, base_tags):
    """
    base_tags: Iterable[str] tag names as displayed (not necessarily canonicalized).
    Robustly check existence regardless of whitespace/case artifacts in DB.
    """
    results = []
    canon_expr = _canon_tags_expr()
    for t in base_tags:
        if not t:
            continue
        tok = _canon_token(t)
        if not tok:
            results.append({"tag": t, "has_articles": False})
            continue
        pattern = f'%,{tok},%'
        exists = session.query(Article.id).filter(canon_expr.like(pattern)).first() is not None
        results.append({"tag": t, "has_articles": bool(exists)})
    return results

# --- /articles filter fix --------------------------------------------------

@app.route('/articles', methods=['GET'])
def get_articles():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    # Parse robustly: repeated & comma-joined
    tokens = _parse_tags_query_args()
    if not tokens:
        tokens = None

    with SessionLocal() as session:
        query = session.query(Article)

        if tokens:
            canon_expr = _canon_tags_expr()
            conditions = [canon_expr.like(f'%,{tok},%') for tok in tokens]
            query = query.filter(or_(*conditions))

        query = query.order_by(Article.published_date.desc())
        total = query.count()
        articles = query.offset((page - 1) * page_size).limit(page_size).all()

        articles_data = []
        for article in articles:
            tags_list = article.tags.strip(',').split(',') if article.tags else []
            # Optional: trim displayed tags
            tags_list = [t.strip() for t in tags_list if t]
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


# ------------------ TAGS (GET / SET ALL) ------------------

def _tags_with_has_articles(session, base_tags):
    """
    base_tags: Iterable[str] of tag names (already deduped/sorted)
    Returns: [{"tag": str, "has_articles": bool}, ...]
    """
    results = []
    for t in base_tags:
        if not t:
            continue
        # Articles.tags stored like ",tag1,tag2,"; match whole tokens reliably
        pattern = f'%,{t},%'
        exists = session.query(Article.id).filter(Article.tags.like(pattern)).first() is not None
        results.append({"tag": t, "has_articles": bool(exists)})
    return results

@app.route('/tags', methods=['GET'])
def get_tags():
    """
    Returns:
      - Default (legacy): array of strings (canonical or aggregated)
      - If include_has_articles=1: array of objects [{tag, has_articles}]
    """
    include_has = request.args.get('include_has_articles') == '1'

    canonical = _load_canonical_tags()
    if canonical is not None:
        if not include_has:
            return jsonify(canonical)
        with SessionLocal() as session:
            enriched = _tags_with_has_articles(session, canonical)
            return jsonify(enriched)

    # Fallback: aggregate from Article.tags (legacy behavior)
    with SessionLocal() as session:
        rows = session.query(Article.tags).filter(Article.tags != None).all()
        tag_set = set()
        for (tags_str,) in rows:
            if tags_str:
                # stored as ",a,b,c," → split safely
                parts = tags_str.strip(',').split(',')
                for p in parts:
                    p = p.strip()
                    if p:
                        tag_set.add(p)

        base_tags = sorted(tag_set)
        if not include_has:
            return jsonify(base_tags)

        enriched = _tags_with_has_articles(session, base_tags)
        return jsonify(enriched)

@app.route('/tags', methods=['PUT', 'POST'])
def set_tags():
    """
    Replace the canonical tag list with EXACTLY the list provided.
    Body (required): {"tags": ["Tag A", "Tag B", ...]}
    Behavior:
      - Always stores the sanitized list (order preserved; double quotes removed).
      - Default response: {"tags": [ ...sanitized... ]}
      - If query param include_has_articles=1 is present, respond with
        a JSON array of objects: [{"tag": "...","has_articles": bool}, ...]
    """
    include_has = request.args.get('include_has_articles') == '1'

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "tags" not in data:
        return jsonify({"error": "Body must be an object with a 'tags' field."}), 400

    tags = data["tags"]
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return jsonify({"error": "'tags' must be a list of strings."}), 400

    # Sanitize: strip double quotes; keep order/content otherwise
    tags = [t.replace('"', '') for t in tags]

    _save_canonical_tags(tags)

    if not include_has:
        return jsonify({"tags": tags}), 200

    # Enriched response path
    with SessionLocal() as session:
        enriched = _tags_with_has_articles(session, tags)
    return jsonify(enriched), 200


# ------------------ MAINTENANCE ------------------

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
