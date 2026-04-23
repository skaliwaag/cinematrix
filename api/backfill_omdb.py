import asyncio
from dotenv import load_dotenv
load_dotenv()

from database import get_conn
from omdb import fetch_movie_meta


async def backfill():
    conn = get_conn()
    movies = conn.execute(
        "SELECT id, title FROM movies WHERE year IS NULL"
    ).fetchall()

    if not movies:
        print("Nothing to backfill.")
        conn.close()
        return

    print(f"Backfilling {len(movies)} movie(s)...\n")

    for movie in movies:
        meta = await fetch_movie_meta(movie["title"])
        if meta:
            conn.execute("""
                UPDATE movies
                SET year=?, genre=?, plot=?, poster_url=?, imdb_id=?, imdb_rating=?
                WHERE id=?
            """, (
                meta.get("year"), meta.get("genre"), meta.get("plot"),
                meta.get("poster_url"), meta.get("imdb_id"), meta.get("imdb_rating"),
                movie["id"],
            ))
            print(f"  OK  {movie['title']} ({meta.get('year', '?')}) — ⭐ {meta.get('imdb_rating', '?')}")
        else:
            print(f"  --  {movie['title']} — not found on OMDB")

    conn.commit()
    conn.close()
    print("\nDone.")


asyncio.run(backfill())
