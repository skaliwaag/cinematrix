# CineMatrix

A Discord bot for movie-night groups. Manage a shared watchlist, vote on what to watch next, and track what the server has seen.

## Prerequisites

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- (Optional) An OMDB API key for automatic movie metadata — free at https://www.omdbapi.com/

## Setup

### 1. Create environment files

Copy `misc/.env.example` to both `api/.env` and `bot/.env`, then fill in your values:

```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
API_BASE=http://localhost:8000
QUEUE_CHANNEL_NAME=movie-queue
OMDB_API_KEY=your_omdb_api_key_here   # optional — enables movie metadata on /suggest
```

### 2. Install dependencies

```bash
cd api && pip install -r requirements.txt
cd ../bot && pip install -r requirements.txt
```

### 3. Start the API

```bash
cd api
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Visit `/docs` for the interactive endpoint browser.

### 4. (Optional) Seed sample data

```bash
cd api
python seed_db_updatecheck.py
```

### 5. Start the bot

```bash
cd bot
python bot.py
```

Slash commands sync to your server on startup. Allow a few seconds, then try `/suggest Dune` in Discord.

## Commands

| Command | Description |
|---|---|
| `/suggest [title]` | Add a movie to the watchlist |
| `/vote [title]` | Upvote a movie (one vote per user) |
| `/whats-next` | Show the top-voted unwatched movie |
| `/watched [title]` | Mark a movie as watched |
| `/rate [title] [1-5]` | Rate a watched movie |
| `/top-rated` | Watched movies ranked by average rating |
| `/history` | All watched movies with dates and scores |
| `/poll-top` | Discord poll — top 5 most-voted picks |
| `/poll-random` | Discord poll — 5 random picks |
| `/queue` | Full unwatched watchlist sorted by votes |
| `/info [title]` | Detailed movie embed with IMDB info |
| `/remove [title]` | Remove a movie you suggested |

## Architecture

```
api/    FastAPI + SQLite — all CRUD operations; bot never touches the DB directly
bot/    discord.py — slash commands that call the API
misc/   .env.example and reference docs
```
