from flask import Flask, render_template, request, url_for
import pandas as pd

from search_engine import SearchEngine


RESULTS_PER_PAGE = 50

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


def create_app():
    app = Flask(__name__)

    # Load the search engine once so each request can reuse the cached data.
    engine = SearchEngine()

    @app.get("/")
    def index():
        # Keep all form values in one dict so the template can refill the fields
        # after a search without repeating request parsing logic.
        filters = {field: request.args.get(field, "").strip() for field in FILTER_FIELDS}
        searched = any(filters.values())
        page = current_page()
        pagination = None
        results = []

        # Avoid running a broad search on the first page load.
        if searched:
            matches = engine.search(**filters, limit=engine.get_total_count())
            page_count = max(1, (len(matches) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
            page = min(page, page_count)
            start = (page - 1) * RESULTS_PER_PAGE
            end = start + RESULTS_PER_PAGE
            page_matches = matches.iloc[start:end]

            results = [serialize_game(row) for _, row in page_matches.iterrows()]
            pagination = build_pagination(filters, page, page_count, len(matches), start)

        return render_template(
            "index.html",
            filters=filters,
            results=results,
            searched=searched,
            pagination=pagination,
            total_count=engine.get_total_count(),
        )

    return app


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


def serialize_game(game):
    # Convert a pandas row into plain display values before sending it to Jinja.
    # This keeps missing value handling and numeric formatting out of the HTML.
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


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)