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


class VoteIn(BaseModel):
    user_id: str


class RatingIn(BaseModel):
    user_id: str
    score: int


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
def vote(movie_id: int, data: VoteIn):
    conn = get_conn()
    row = conn.execute("SELECT id FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")
    try:
        conn.execute(
            "INSERT INTO votes (movie_id, user_id) VALUES (?, ?)",
            (movie_id, data.user_id)
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=409, detail="Already voted for this movie")
    conn.close()
    return {"movie_id": movie_id, "user_id": data.user_id}


# ── Ratings ────────────────────────────────────────────────────────────────────

@app.post("/movies/{movie_id}/ratings", status_code=201)
def rate_movie(movie_id: int, data: RatingIn):
    if data.score < 1 or data.score > 5:
        raise HTTPException(status_code=422, detail="Score must be between 1 and 5")
    conn = get_conn()
    row = conn.execute("SELECT id, watched FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")
    if not row["watched"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Movie has not been watched yet")
    try:
        conn.execute(
            "INSERT INTO ratings (movie_id, user_id, score) VALUES (?, ?, ?)",
            (movie_id, data.user_id, data.score)
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=409, detail="Already rated this movie")
    conn.close()
    return {"movie_id": movie_id, "user_id": data.user_id, "score": data.score}


# ── Special queries ────────────────────────────────────────────────────────────

@app.get("/whats-next")
def whats_next():
    conn = get_conn()
    row = conn.execute("""
        SELECT m.*, COUNT(v.id) AS vote_count
        FROM movies m
        LEFT JOIN votes v ON v.movie_id = m.id
        WHERE m.watched = 0
        GROUP BY m.id
        ORDER BY vote_count DESC, m.id ASC
        LIMIT 1
    """).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No unwatched movies on the list")
    return dict(row)


@app.get("/top-rated")
def top_rated():
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*, ROUND(AVG(r.score), 2) AS avg_score, COUNT(r.id) AS rating_count
        FROM movies m
        JOIN ratings r ON r.movie_id = m.id
        WHERE m.watched = 1
        GROUP BY m.id
        ORDER BY avg_score DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/history")
def history():
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*, ROUND(AVG(r.score), 2) AS avg_score, COUNT(r.id) AS rating_count
        FROM movies m
        LEFT JOIN ratings r ON r.movie_id = m.id
        WHERE m.watched = 1
        GROUP BY m.id
        ORDER BY m.watched_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]