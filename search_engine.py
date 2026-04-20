import os
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

CSV_PATH = os.path.join(os.path.dirname(__file__), "games_25000.csv")

TEXT_COLUMNS = [
    "name",
    "summary",
    "storyline",
    "genres",
    "themes",
    "keywords",
    "game_modes",
    "player_perspectives",
    "platforms",
    "developers",
    "publishers",
]
#separate weighting of each field for TF-IDF calculations
FIELD_WEIGHTS = {
    "name": 4,
    "genres": 3,
    "themes": 2,
    "keywords": 2,
    "game_modes": 2,
    "platforms": 2,
    "developers": 1,
    "publishers": 1,
    "summary": 1,
    "storyline": 1,
}

# expansions of the short hand / abbreviation queries.
QUERY_EXPANSIONS = {
    "fps": "first person shooter",
    "rpg": "role playing game",
    "jrpg": "japanese role playing game",
    "coop": "co op cooperative multiplayer",
    "co-op": "co op cooperative multiplayer",
    "mmo": "massively multiplayer online",
}


def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_contains(series, value):
    return series.fillna("").str.lower().str.contains(value.lower(), na=False, regex=False)


def expand_query(query_text):
    """
    checks known abbreviations/short hand and expands each one
    and then joins the original query and expansions into one search
    """
    normalized_query = normalize_text(query_text)
    expanded_parts = [normalized_query]

    for term, expansion in QUERY_EXPANSIONS.items():
        if term in normalized_query.split():
            expanded_parts.append(expansion)

    return " ".join(part for part in expanded_parts if part).strip()


def build_weighted_search_text(df):
    """
    builds one synthetic search document per game row
    fields with larger weights are multiplied to appear more often in the
    final field text, which makes TF-IDF treat matches in those fields are more imporant
    """
    weighted_parts = []

    for column, weight in FIELD_WEIGHTS.items():
        weighted_parts.append((df[f"{column}_norm"] + " ") * weight)

    return pd.Series(weighted_parts).sum().str.strip()


class SearchEngine:
    def __init__(self, csv_path=CSV_PATH):
        self.csv_path = csv_path

        base_dir = os.path.dirname(__file__)
        cache_dir = os.path.join(base_dir, "cached")

        # Make sure cache folder exists
        os.makedirs(cache_dir, exist_ok=True)

        # Cache file paths
        self.df_path = os.path.join(cache_dir, "cached_df.pkl")
        self.vectorizer_path = os.path.join(cache_dir, "vectorizer.pkl")
        self.matrix_path = os.path.join(cache_dir, "tfidf_matrix.pkl")

        # --------------------------------------------------
        # Try loading cached data
        # --------------------------------------------------
        if (
            os.path.exists(self.df_path)
            and os.path.exists(self.vectorizer_path)
            and os.path.exists(self.matrix_path)
        ):
            print("Loading cached data...")

            self.df = pd.read_pickle(self.df_path)

            with open(self.vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)

            with open(self.matrix_path, "rb") as f:
                self.tfidf_matrix = pickle.load(f)

        else:
            print("First-time setup: processing data...")

            self.df = self._load_data()

            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )

            self.tfidf_matrix = self.vectorizer.fit_transform(self.df["search_text"])

            print("Saving cache...")

            self.df.to_pickle(self.df_path)

            with open(self.vectorizer_path, "wb") as f:
                pickle.dump(self.vectorizer, f)

            with open(self.matrix_path, "wb") as f:
                pickle.dump(self.tfidf_matrix, f)

            print("Cache saved! Future runs will be fast.")

    def _load_data(self):
        df = pd.read_csv(self.csv_path, dtype=str)

        if "rating" in df.columns:
            df["rating_num"] = pd.to_numeric(df["rating"], errors="coerce")
        else:
            df["rating"] = ""
            df["rating_num"] = pd.Series(dtype="float64")

        for col in TEXT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].fillna("").astype(str)
            df[f"{col}_norm"] = df[col].apply(normalize_text)

        df["search_text"] = build_weighted_search_text(df)

        return df

    def get_total_count(self):
        return len(self.df)

    def tokenize_filter(self, text):
        return [t.strip().lower() for t in str(text).split(',')]
    
    def token_match(self, series, query):
        query_tokens = self.tokenize_filter(query)
        def check(cell):
            cell_tokens = self.tokenize_filter(str(cell))
            return all(token in cell_tokens for token in query_tokens)
        return series.apply(check)
    
    def apply_filters(
        self,
        name="",
        genre="",
        theme="",
        platform="",
        developer="",
        publisher="",
        game_mode="",
        rating_min="",
        rating_max="",
    ):
        filtered = self.df.copy()
        mask = pd.Series(True, index=filtered.index)

        if name.strip():
            mask &= safe_contains(filtered["name"], name.strip())

        if genre.strip():
            mask &= self.token_match(filtered["genres"], genre.strip())

        if theme.strip():
            mask &= self.token_match(filtered["themes"], theme.strip())

        if platform.strip():
            mask &= self.token_match(filtered["platforms"], platform.strip())

        if developer.strip():
            mask &= safe_contains(filtered["developers"], developer.strip())

        if publisher.strip():
            mask &= safe_contains(filtered["publishers"], publisher.strip())

        if game_mode.strip():
            mask &= self.token_match(filtered["game_modes"], game_mode.strip())

        if rating_min.strip():
            try:
                mask &= filtered["rating_num"] >= float(rating_min)
            except ValueError:
                pass

        if rating_max.strip():
            try:
                mask &= filtered["rating_num"] <= float(rating_max)
            except ValueError:
                pass

        return filtered[mask].copy()

    def rank_by_query(self, data, query_text):
        query_text = expand_query(query_text)
        ranked = data.copy()

        if not query_text:
            ranked["score"] = 0.0
            return ranked.sort_values(
                by=["rating_num", "name"],
                ascending=[False, True],
                na_position="last"
            )

        # Transform query into TF-IDF vector
        query_vec = self.vectorizer.transform([query_text])

        # Use original indices from filtered dataframe to select rows
        filtered_indices = ranked.index.tolist()
        filtered_matrix = self.tfidf_matrix[filtered_indices]

        # Cosine similarity between query and filtered game set
        similarities = cosine_similarity(query_vec, filtered_matrix).flatten()

        ranked["score"] = similarities

        # Optional small boosts to improve perceived quality
        ranked["title_exact_boost"] = (
            ranked["name_norm"] == query_text
        ).astype(float) * 0.25

        ranked["title_contains_boost"] = (
            ranked["name_norm"].str.contains(query_text, na=False, regex=False)
        ).astype(float) * 0.10

        ranked["rating_boost"] = ranked["rating_num"].fillna(0) / 1000.0

        ranked["score"] = (
            ranked["score"] +
            ranked["title_exact_boost"] +
            ranked["title_contains_boost"] +
            ranked["rating_boost"]
        )

        ranked = ranked[ranked["score"] > 0]

        return ranked.sort_values(
            by=["score", "rating_num", "name"],
            ascending=[False, False, True],
            na_position="last"
        )

    def search(
        self,
        query_text="",
        name="",
        genre="",
        theme="",
        platform="",
        developer="",
        publisher="",
        game_mode="",
        rating_min="",
        rating_max="",
        limit=100,
    ):
        filtered = self.apply_filters(
            name=name,
            genre=genre,
            theme=theme,
            platform=platform,
            developer=developer,
            publisher=publisher,
            game_mode=game_mode,
            rating_min=rating_min,
            rating_max=rating_max,
        )

        ranked = self.rank_by_query(filtered, query_text)
        return ranked.head(limit).copy()
