# GameSense
This is a Github Repo for a project in CSCE 470, where we will create a tool, which allows users to search currently or formerly commercially available video games based on certain attributes such as genre, age rating, developer, etc. We call the IGDB API to access their database which has tens of thousands of games and apply TF-IDF vectorization and cosine similarity to rank games. 


# Search Algorithm
Our search algorithm ranks games using a TF-IDF based search model combined with cosine similarity. Each game is turned into a searchable text document by combining normalized fields such as the name, genres, themes, keywords, platforms, developers, publishers, summary, and storyline. Certain fields like name and genre are weighted heavier so they have a stronger impact on the final ranking.

When the user enters the query the text is normalized and expanded, with short hand terms to improve matching. The query is then compared against filtered game dataset using TF-IDF vectors and cosine similarity. The final results are adjusted with large boosts for exact title matches, partial title matches, and higher rated games, which helps the most relevant results to appear first. 