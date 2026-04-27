"""
Seed the CineMatrix SQLite database with sample data.
Run from the api/ directory: python seed_db_updatecheck.py
"""
from database import get_conn, init_db

MOVIES = [
    # (title, suggested_by, watched, watched_at, year, genre, imdb_rating)
    ("The Thing",          "Daniel#1234",  1, "2024-10-15", "1982", "Horror, Mystery, Sci-Fi", "8.2"),
    ("Blade Runner 2049",  "Braeden#5678", 1, "2024-11-02", "2017", "Drama, Mystery, Sci-Fi",  "8.0"),
    ("Annihilation",       "Hope#9012",    1, "2024-11-22", "2018", "Adventure, Drama, Horror","6.8"),
    ("Dune: Part Two",     "Daniel#1234",  0, None,         "2024", "Action, Adventure, Drama", "8.8"),
    ("Hereditary",         "Braeden#5678", 0, None,         "2018", "Drama, Horror, Mystery",  "7.3"),
    ("The Green Mile",     "Hope#9012",    0, None,         "1999", "Crime, Drama, Fantasy",   "8.6"),
    ("Mandy",              "Daniel#1234",  0, None,         "2018", "Action, Fantasy, Horror", "6.5"),
)

VOTES = [
    # (movie_title, user_id)
    ("Dune: Part Two",  "111111111111111111"),
    ("Dune: Part Two",  "222222222222222222"),
    ("Dune: Part Two",  "333333333333333333"),
    ("Hereditary",      "111111111111111111"),
    ("Hereditary",      "444444444444444444"),
    ("The Green Mile",  "222222222222222222"),
    ("Mandy",           "333333333333333333"),
]

RATINGS = [
    # (movie_title, user_id, score)
    ("The Thing",         "111111111111111111", 5),
    ("The Thing",         "222222222222222222", 5),
    ("The Thing",         "333333333333333333", 4),
    ("Blade Runner 2049", "111111111111111111", 4),
    ("Blade Runner 2049", "444444444444444444", 5),
    ("Annihilation",      "222222222222222222", 3),
    ("Annihilation",      "333333333333333333", 4),
]


def seed():
    init_db()
    conn = get_conn()

    conn.execute("DELETE FROM ratings")
    conn.execute("DELETE FROM votes")
    conn.execute("DELETE FROM movies")
    conn.commit()
    print("Cleared existing data.")

    title_to_id = {}
    for title, suggested_by, watched, watched_at, year, genre, imdb_rating in MOVIES:
        cur = conn.execute(
            """INSERT INTO movies
               (title, suggested_by, watched, watched_at, year, genre, imdb_rating)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, suggested_by, watched, watched_at, year, genre, imdb_rating),
        )
        title_to_id[title] = cur.lastrowid
    conn.commit()
    print(f"Inserted {len(MOVIES)} movies.")

    for title, user_id in VOTES:
        conn.execute(
            "INSERT INTO votes (movie_id, user_id) VALUES (?, ?)",
            (title_to_id[title], user_id),
        )
    conn.commit()
    print(f"Inserted {len(VOTES)} votes.")

    for title, user_id, score in RATINGS:
        conn.execute(
            "INSERT INTO ratings (movie_id, user_id, score) VALUES (?, ?, ?)",
            (title_to_id[title], user_id, score),
        )
    conn.commit()
    print(f"Inserted {len(RATINGS)} ratings.")

    conn.close()
    print("\nSeed complete. Run the API and bot to test.")


if __name__ == "__main__":
    seed()
