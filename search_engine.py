import os
import re
import pandas as pd

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

DISPLAY_COLUMNS = [
    "name",
    "genres",
    "themes",
    "platforms",
    "developers",
    "publishers",
    "rating",
    "game_modes",
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
            df[col] = df[col].fillna("")
            df[f"{col}_norm"] = df[col].apply(normalize_text)

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

        tokens = [token for token in query_text.split() if len(token) > 1]

        if not tokens:
            ranked["score"] = 0.0
            return ranked.sort_values(
                by=["rating_num", "name"],
                ascending=[False, True],
                na_position="last"
            )

        score = pd.Series(0.0, index=data.index)
        matched_tokens = pd.Series(0, index=data.index)

        name_norm = data["name_norm"]
        genres_norm = data["genres_norm"]
        themes_norm = data["themes_norm"]
        keywords_norm = data["keywords_norm"]
        platforms_norm = data["platforms_norm"]
        game_modes_norm = data["game_modes_norm"]
        developers_norm = data["developers_norm"]
        publishers_norm = data["publishers_norm"]
        summary_norm = data["summary_norm"]
        storyline_norm = data["storyline_norm"]

        # Strong full-query boosts
        score += (name_norm == query_text).astype(float) * 100
        score += name_norm.str.startswith(query_text, na=False).astype(float) * 40
        score += name_norm.str.contains(query_text, na=False, regex=False).astype(float) * 25

        score += genres_norm.str.contains(query_text, na=False, regex=False).astype(float) * 15
        score += themes_norm.str.contains(query_text, na=False, regex=False).astype(float) * 12
        score += keywords_norm.str.contains(query_text, na=False, regex=False).astype(float) * 12
        score += summary_norm.str.contains(query_text, na=False, regex=False).astype(float) * 8
        score += storyline_norm.str.contains(query_text, na=False, regex=False).astype(float) * 5

        for token in tokens:
            token_match = pd.Series(False, index=data.index)

            in_name = name_norm.str.contains(token, na=False, regex=False)
            in_genres = genres_norm.str.contains(token, na=False, regex=False)
            in_themes = themes_norm.str.contains(token, na=False, regex=False)
            in_keywords = keywords_norm.str.contains(token, na=False, regex=False)
            in_platforms = platforms_norm.str.contains(token, na=False, regex=False)
            in_modes = game_modes_norm.str.contains(token, na=False, regex=False)
            in_devs = developers_norm.str.contains(token, na=False, regex=False)
            in_pubs = publishers_norm.str.contains(token, na=False, regex=False)
            in_summary = summary_norm.str.contains(token, na=False, regex=False)
            in_storyline = storyline_norm.str.contains(token, na=False, regex=False)

            # Title gets strongest weight
            score += in_name.astype(float) * 10
            score += name_norm.str.startswith(token, na=False).astype(float) * 6

            score += in_genres.astype(float) * 6
            score += in_themes.astype(float) * 5
            score += in_keywords.astype(float) * 5
            score += in_platforms.astype(float) * 3
            score += in_modes.astype(float) * 3
            score += in_devs.astype(float) * 2
            score += in_pubs.astype(float) * 2
            score += in_summary.astype(float) * 2
            score += in_storyline.astype(float) * 1

            token_match |= (
                in_name | in_genres | in_themes | in_keywords |
                in_platforms | in_modes | in_devs | in_pubs |
                in_summary | in_storyline
            )

            matched_tokens += token_match.astype(int)

        # Reward games that match more of the query words
        score += matched_tokens.astype(float) * 8

        # Extra bonus if ALL tokens matched somewhere
        score += (matched_tokens == len(tokens)).astype(float) * 20

        # Small rating bonus so stronger games win ties
        if "rating_num" in data.columns:
            rating_bonus = data["rating_num"].fillna(0) / 10.0
            score += rating_bonus

        ranked["score"] = score
        ranked["matched_tokens"] = matched_tokens

        ranked = ranked[ranked["score"] > 0]

        return ranked.sort_values(
            by=["score", "matched_tokens", "rating_num", "name"],
            ascending=[False, False, False, True],
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