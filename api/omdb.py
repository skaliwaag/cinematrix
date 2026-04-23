import os
import httpx

OMDB_URL = "https://www.omdbapi.com/"


async def fetch_movie_meta(title: str) -> dict | None:
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        return None

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(OMDB_URL, params={"t": title, "apikey": api_key})

    if resp.status_code != 200:
        return None

    data = resp.json()
    if data.get("Response") == "False":
        return None

    return {
        "year":        data.get("Year"),
        "genre":       data.get("Genre"),
        "plot":        data.get("Plot"),
        "poster_url":  data.get("Poster") if data.get("Poster") != "N/A" else None,
        "imdb_id":     data.get("imdbID"),
        "imdb_rating": data.get("imdbRating") if data.get("imdbRating") != "N/A" else None,
    }
