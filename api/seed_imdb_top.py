"""
Populate the database with top IMDb movies via OMDB.

How it works:
  1. Downloads IMDb's public ratings dataset (datasets.imdbws.com, ~1 MB)
  2. Filters to highly rated, widely voted titles
  3. Fetches full details from OMDB for each IMDb ID
  4. Inserts movies into the local database until TARGET is reached

Requires OMDB_API_KEY in api/.env
Run from api/:
    python seed_imdb_top.py            # adds up to 250 movies
    python seed_imdb_top.py --clear    # wipes existing data first
    python seed_imdb_top.py --target 100   # stop after 100
"""

import asyncio
import gzip
import io
import csv
import sys
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

from database import get_conn, init_db

OMDB_URL    = "https://www.omdbapi.com/"
RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"

DEFAULT_TARGET  = 250
MIN_VOTES       = 100_000   # broad enough to cover all of IMDb's top 250
MIN_RATING      = 7.5
SUGGESTED_BY    = "imdb_top250"


async def fetch_by_imdb_id(imdb_id: str, api_key: str) -> dict | None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OMDB_URL, params={"i": imdb_id, "apikey": api_key})
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get("Response") == "False" or data.get("Type") != "movie":
        return None
    return {
        "title":       data.get("Title"),
        "year":        data.get("Year"),
        "genre":       data.get("Genre"),
        "plot":        data.get("Plot"),
        "poster_url":  data.get("Poster") if data.get("Poster") != "N/A" else None,
        "imdb_id":     data.get("imdbID"),
        "imdb_rating": data.get("imdbRating") if data.get("imdbRating") != "N/A" else None,
    }


async def seed(clear: bool = False, target: int = DEFAULT_TARGET):
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        print("ERROR: OMDB_API_KEY not set in api/.env")
        sys.exit(1)

    init_db()
    conn = get_conn()

    if clear:
        conn.execute("DELETE FROM ratings")
        conn.execute("DELETE FROM votes")
        conn.execute("DELETE FROM movies")
        conn.commit()
        print("Cleared existing data.\n")

    # ── Step 1: download IMDb public ratings dataset ───────────────────────────
    print("Downloading IMDb ratings dataset...", flush=True)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(RATINGS_URL)
    resp.raise_for_status()

    raw    = gzip.decompress(resp.content)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter="\t")

    candidates = [
        row for row in reader
        if float(row["averageRating"]) >= MIN_RATING
        and int(row["numVotes"]) >= MIN_VOTES
    ]
    # Sort by votes descending — most popular first
    candidates.sort(key=lambda r: int(r["numVotes"]), reverse=True)
    print(f"Found {len(candidates)} candidates. Fetching details from OMDB...\n")

    # ── Step 2: fetch full details from OMDB ──────────────────────────────────
    inserted = 0
    skipped  = 0

    for row in candidates:
        if inserted >= target:
            break

        imdb_id = row["tconst"]

        existing = conn.execute(
            "SELECT id FROM movies WHERE imdb_id = ?", (imdb_id,)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        meta = await fetch_by_imdb_id(imdb_id, api_key)
        if meta is None:
            # TV show, short, or not in OMDB — skip silently
            continue

        conn.execute(
            """INSERT OR IGNORE INTO movies
               (title, suggested_by, year, genre, plot, poster_url, imdb_id, imdb_rating)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                meta["title"], SUGGESTED_BY,
                meta["year"], meta["genre"], meta["plot"],
                meta["poster_url"], meta["imdb_id"], meta["imdb_rating"],
            ),
        )
        conn.commit()
        inserted += 1
        rating = meta.get("imdb_rating") or "?"
        print(f"  [{inserted:>3}/{target}] {meta['title']} ({meta.get('year', '?')}) — ⭐ {rating}")

    conn.close()
    print(f"\nDone — {inserted} inserted, {skipped} skipped (already in DB).")


if __name__ == "__main__":
    args   = sys.argv[1:]
    clear  = "--clear" in args
    target = DEFAULT_TARGET
    if "--target" in args:
        idx    = args.index("--target")
        target = int(args[idx + 1])
    asyncio.run(seed(clear=clear, target=target))
