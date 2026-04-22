import os
import requests
import time
import json
import pandas as pd

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_URL = "https://api.igdb.com/v4/games"


def get_access_token(client_id, client_secret):
    response = requests.post(
        TOKEN_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


def fetch_games(client_id, access_token, total_games=30000, batch_size=500):
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }

    all_games = []
    offset = 0

    while len(all_games) < total_games:
        remaining = total_games - len(all_games)
        limit = min(batch_size, remaining)

        query = f"""
fields
    id,
    name,
    summary,
    storyline,
    rating,
    genres.name,
    themes.name,
    keywords.name,
    game_modes.name,
    player_perspectives.name,
    platforms.name,
    similar_games,
    involved_companies.company.name,
    involved_companies.developer,
    involved_companies.publisher;
sort id asc;
limit {limit};
offset {offset};
"""

        response = requests.post(
            IGDB_URL,
            headers=headers,
            data=query,
            timeout=60
        )

        print(f"Status code: {response.status_code}")

        response.raise_for_status()
        batch = response.json()

        if not batch:
            print("No more games returned by IGDB.")
            break

        all_games.extend(batch)
        print(f"Fetched {len(all_games)} games so far...")

        offset += limit
        time.sleep(0.4)

    return all_games


def extract_names(items):
    if not items:
        return ""
    names = []
    for item in items:
        if isinstance(item, dict) and "name" in item:
            names.append(item["name"])
    return ", ".join(names)


def extract_company_roles(companies):
    developers = []
    publishers = []

    if not companies:
        return "", ""

    for item in companies:
        company_name = ""
        if isinstance(item, dict):
            company = item.get("company")
            if isinstance(company, dict):
                company_name = company.get("name", "")

            if item.get("developer") and company_name:
                developers.append(company_name)

            if item.get("publisher") and company_name:
                publishers.append(company_name)

    return ", ".join(developers), ", ".join(publishers)


def save_json(games, filename="games_25000.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(games)} games to {filename}")


def save_csv(games, filename="games_25000.csv"):
    rows = []

    for g in games:
        developers, publishers = extract_company_roles(g.get("involved_companies"))

        rows.append({
            "id": g.get("id"),
            "name": g.get("name"),
            "summary": g.get("summary"),
            "storyline": g.get("storyline"),
            "rating": g.get("rating"),
            "genres": extract_names(g.get("genres")),
            "themes": extract_names(g.get("themes")),
            "keywords": extract_names(g.get("keywords")),
            "game_modes": extract_names(g.get("game_modes")),
            "player_perspectives": extract_names(g.get("player_perspectives")),
            "platforms": extract_names(g.get("platforms")),
            "developers": developers,
            "publishers": publishers,
            "similar_games": ", ".join(str(x) for x in g.get("similar_games", [])) if g.get("similar_games") else "",
        })

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"Saved {len(df)} games to {filename}")


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET as environment variables first.")

    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    print("Access token retrieved successfully.")

    games = fetch_games(CLIENT_ID, access_token, total_games=25000, batch_size=500)

    save_json(games, "games_25000.json")
    save_csv(games, "games_25000.csv")


if __name__ == "__main__":
    main()