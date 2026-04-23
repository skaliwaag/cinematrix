import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cinematrix.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS movies (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL UNIQUE,
            suggested_by TEXT NOT NULL,
            watched      INTEGER NOT NULL DEFAULT 0,
            watched_at   TEXT,
            year         TEXT,
            genre        TEXT,
            plot         TEXT,
            poster_url   TEXT,
            imdb_id      TEXT,
            imdb_rating  TEXT
        );

        CREATE TABLE IF NOT EXISTS votes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL REFERENCES movies(id),
            user_id  TEXT NOT NULL,
            UNIQUE(movie_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS ratings (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL REFERENCES movies(id),
            user_id  TEXT NOT NULL,
            score    INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
            UNIQUE(movie_id, user_id)
        );
    """)

    # Migrate existing DB — silently skip columns that already exist
    new_columns = ["year TEXT", "genre TEXT", "plot TEXT",
                   "poster_url TEXT", "imdb_id TEXT", "imdb_rating TEXT"]
    for col in new_columns:
        try:
            conn.execute(f"ALTER TABLE movies ADD COLUMN {col}")
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("Database ready.")