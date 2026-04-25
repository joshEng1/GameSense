import os

from flask import Flask, render_template, request, url_for
import pandas as pd

from search_engine import SearchEngine


RESULTS_PER_PAGE = 50
MAX_SEARCH_RESULTS = 100
engine = None

FILTER_FIELDS = [
    "query_text",
    "name",
    "genre",
    "theme",
    "platform",
    "developer",
    "publisher",
    "game_mode",
    "rating_min",
    "rating_max",
]

# MULTI_FIELDS = ["genre", "theme", "platform", "developer", "publisher", "game_mode"]

def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        # Keep all form values in one dict so the template can refill the fields
        # after a search without repeating request parsing logic.
        filters = {field: request.args.get(field, "").strip() for field in FILTER_FIELDS}
        # filters = {field: request.args.get(field, "").strip() for field in FILTER_FIELDS if field not in MULTI_FIELDS}
        # filters.update({field: request.args.getlist(field) for field in MULTI_FIELDS})
        searched = any(filters.values())
        page = current_page()
        pagination = None
        results = []
        total_count = None

        engine = get_engine()
        filter_options = engine.get_filter_options()

        # Avoid running a broad search on the first page load.
        if searched:
            matches = engine.search(**filters, limit=MAX_SEARCH_RESULTS)
            '''
            matches = engine.search(
                **{k: v for k, v in filters.items() if k not in MULTI_FIELDS},
                **{k: ",".join(v) for k, v in filters.items() if k in MULTI_FIELDS},
                limit=MAX_SEARCH_RESULTS,
            )
            '''
            page_count = max(1, (len(matches) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
            page = min(page, page_count)
            start = (page - 1) * RESULTS_PER_PAGE
            end = start + RESULTS_PER_PAGE
            page_matches = matches.iloc[start:end]

            scores = pd.to_numeric(matches["score"], errors="coerce").dropna()
            max_score = scores.max() if not scores.empty else None
            results = [serialize_game(row, max_score) for _, row in page_matches.iterrows()]
            pagination = build_pagination(filters, page, page_count, len(matches), start)
            total_count = engine.get_total_count()

        

        return render_template(
            "index.html",
            filters=filters,
            results=results,
            searched=searched,
            pagination=pagination,
            total_count=total_count,
            filter_options=filter_options
        )

    return app


def get_engine():
    global engine

    # Load TF IDF after the web server starts so hosted platforms can bind first.
    if engine is None:
        engine = SearchEngine()

    return engine


def current_page():
    try:
        return max(1, int(request.args.get("page", "1")))
    except ValueError:
        return 1


def build_pagination(filters, page, page_count, total_results, start):
    return {
        "page": page,
        "page_count": page_count,
        "total_results": total_results,
        "start_result": start + 1 if total_results else 0,
        "end_result": min(start + RESULTS_PER_PAGE, total_results),
        "prev_url": page_url(filters, page - 1) if page > 1 else "",
        "next_url": page_url(filters, page + 1) if page < page_count else "",
    }


def page_url(filters, page):
    args = {field: value for field, value in filters.items() if value}
    args["page"] = page
    return url_for("index", **args)


def serialize_game(game, max_score=None):
    # Convert a pandas row into plain display values before sending it to Jinja.
    # This keeps missing value handling and numeric formatting out of the HTML.
    normalized = normalize_score(game.get("score"), max_score)
    match_percent = int(round(normalized * 100))
    return {
        "name": text_value(game, "name"),
        "genres": text_value(game, "genres"),
        "themes": text_value(game, "themes"),
        "platforms": text_value(game, "platforms"),
        "developers": text_value(game, "developers"),
        "publishers": text_value(game, "publishers"),
        "game_modes": text_value(game, "game_modes"),
        "keywords": text_value(game, "keywords"),
        "summary": text_value(game, "summary"),
        "storyline": text_value(game, "storyline"),
        "rating": rating_value(game),
        "score": score_value(game),
        "match_label": relevance_label(normalized),
        "match_bar": score_bar(normalized),
        "match_percent": match_percent,
        "match_width": f"{match_percent}%",
        "match_tag": match_tag(normalized),
    }


def text_value(game, key):
    value = game.get(key, "")
    if pd.isna(value) or str(value).strip() == "":
        return "N/A"
    return str(value).strip()


def rating_value(game):
    value = game.get("rating", "")
    if pd.isna(value) or str(value).strip() == "":
        return "N/A"

    try:
        return f"{float(value):.1f}"
    except ValueError:
        return str(value)


def score_value(game):
    value = game.get("score", "")
    if pd.isna(value) or str(value).strip() == "":
        return "N/A"

    try:
        return f"{float(value):.3f}"
    except ValueError:
        return str(value)


def normalize_score(score, max_score):
    try:
        score = float(score) * 2.3
    except (ValueError, TypeError):
        return 0.0
    return max(0.0, min(score, 1.0))


def score_bar(normalized_score, length=10):
    try:
        normalized_score = float(normalized_score)
    except (ValueError, TypeError):
        normalized_score = 0.0
    normalized_score = max(0.0, min(normalized_score, 1.0))
    filled = round(normalized_score * length)
    return "█" * filled


def relevance_label(normalized_score):
    try:
        normalized_score = float(normalized_score)
    except (ValueError, TypeError):
        return "N/A"
    if normalized_score >= 0.8:
        return "Top Result"
    elif normalized_score >= 0.60:
        return "High Relevance"
    elif normalized_score >= 0.35:
        return "Moderate Relevance"
    else:
        return "Low Relevance"


def match_tag(normalized_score):
    try:
        normalized_score = float(normalized_score)
    except (ValueError, TypeError):
        return "low"
    if normalized_score >= 0.8:
        return "high"
    elif normalized_score >= 0.60:
        return "good"
    elif normalized_score >= 0.35:
        return "mid"
    else:
        return "low"


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
