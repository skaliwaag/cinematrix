from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_conn, init_db

app = FastAPI(title="CineMatrix API")


@app.on_event("startup")
def startup():
    init_db()


# ── Pydantic models ────────────────────────────────────────────────────────────

class MovieIn(BaseModel):
    title: str
    suggested_by: str


# ── Movies ─────────────────────────────────────────────────────────────────────

@app.get("/movies")
def list_movies():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM movies ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/movies", status_code=201)
def add_movie(data: MovieIn):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO movies (title, suggested_by) VALUES (?, ?)",
            (data.title, data.suggested_by)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM movies WHERE id = ?", (cur.lastrowid,)).fetchone()
    except Exception:
        conn.close()
        raise HTTPException(status_code=409, detail="Movie already on the list")
    conn.close()
    return dict(row)


@app.patch("/movies/{movie_id}/watched")
def mark_watched(movie_id: int):
    from datetime import date
    conn = get_conn()
    row = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")
    conn.execute(
        "UPDATE movies SET watched = 1, watched_at = ? WHERE id = ?",
        (date.today().isoformat(), movie_id)
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    conn.close()
    return dict(updated)


@app.delete("/movies/{movie_id}", status_code=204)
def delete_movie(movie_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()


# ── Votes ──────────────────────────────────────────────────────────────────────

@app.post("/movies/{movie_id}/votes", status_code=201)
def vote(movie_id: int):
    # TODO: insert a vote; reject duplicates
    pass


# ── Ratings ────────────────────────────────────────────────────────────────────

@app.post("/movies/{movie_id}/ratings", status_code=201)
def rate_movie(movie_id: int):
    # TODO: insert a rating 1-5; reject if movie not watched yet
    pass


# ── Special queries ────────────────────────────────────────────────────────────

@app.get("/whats-next")
def whats_next():
    # TODO: return unwatched movie with most votes
    pass

@app.get("/top-rated")
def top_rated():
    # TODO: return watched movies ranked by avg rating
    pass

@app.get("/history")
def history():
    # TODO: return all watched movies with avg ratings
    pass