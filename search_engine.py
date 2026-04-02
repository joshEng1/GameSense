import os
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_contains(series, value):
    return series.fillna("").str.lower().str.contains(value.lower(), na=False, regex=False)


class SearchEngine:
    def __init__(self, csv_path=CSV_PATH):
        self.csv_path = csv_path
        self.df = self._load_data()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["search_text"])

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

        # Build a combined text field for TF-IDF search
        # Title is repeated to make it matter more in ranking
        df["search_text"] = (
            df["name_norm"] + " " +
            df["name_norm"] + " " +
            df["genres_norm"] + " " +
            df["themes_norm"] + " " +
            df["keywords_norm"] + " " +
            df["game_modes_norm"] + " " +
            df["platforms_norm"] + " " +
            df["developers_norm"] + " " +
            df["publishers_norm"] + " " +
            df["summary_norm"] + " " +
            df["storyline_norm"]
        ).str.strip()

        return df

    def get_total_count(self):
        return len(self.df)

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
            mask &= safe_contains(filtered["genres"], genre.strip())

        if theme.strip():
            mask &= safe_contains(filtered["themes"], theme.strip())

        if platform.strip():
            mask &= safe_contains(filtered["platforms"], platform.strip())

        if developer.strip():
            mask &= safe_contains(filtered["developers"], developer.strip())

        if publisher.strip():
            mask &= safe_contains(filtered["publishers"], publisher.strip())

        if game_mode.strip():
            mask &= safe_contains(filtered["game_modes"], game_mode.strip())

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
        query_text = normalize_text(query_text)
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