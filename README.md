# CineMatrix

A Discord bot for movie-night groups. Manage a shared watchlist, vote on what to watch next, and track what the server has seen.

OMDB integration automatically pulls year, genre, plot, poster, and IMDB rating when a movie is suggested.

## Prerequisites

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Discord server with a `#movie-queue` channel
- (Optional) An OMDB API key for automatic movie metadata — free at https://www.omdbapi.com/

## Quick Setup

Run the setup script to copy `.env` files and install all dependencies in one step:

```bash
python setup.py
```

It will also offer to seed the database with sample movies. Then proceed to steps 3 and 4 below.

## Manual Setup

### 1. Create environment files

Copy `misc/.env.example` to both `api/.env` and `bot/.env`, then fill in your values:

```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
API_BASE=http://localhost:8000
QUEUE_CHANNEL_NAME=movie-queue
OMDB_API_KEY=your_omdb_api_key_here   # optional — enables movie metadata on /suggest
```

To get your `GUILD_ID`: open Discord, go to Settings > Advanced > enable Developer Mode, then right-click your server and select Copy Server ID.

### 2. Install dependencies

```bash
cd api && pip install -r requirements.txt
cd ../bot && pip install -r requirements.txt
```

### 3. Start the API

Open a terminal and run:

```bash
cd api
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Visit `/docs` for the interactive endpoint browser.

### 4. Start the bot

Open a second terminal and run:

```bash
cd bot
python bot.py
```

Slash commands sync to your server on startup. Allow a few seconds, then try `/suggest Dune` in Discord.

### 5. (Optional) Seed sample data

```bash
cd api
python seed_db_updatecheck.py
```

## Commands

| Command | Description |
|---|---|
| `/suggest [title]` | Add a movie to the watchlist. Fetches year, genre, IMDB rating, and poster automatically. Announces to `#movie-queue`. |
| `/vote [title]` | Upvote a movie. One vote per user; rejects duplicates. |
| `/whats-next` | Show the top-voted unwatched movie. |
| `/watched [title]` | Mark a movie as watched. Resets its vote count. |
| `/rate [title] [1-5]` | Rate a watched movie 1-5. One rating per user. |
| `/top-rated` | Watched movies ranked by average rating (rated movies only). |
| `/history` | All watched movies with dates and average scores. |
| `/poll-top` | 24-hour Discord poll on the 5 most-voted unwatched picks. |
| `/poll-random` | 24-hour Discord poll on 5 random unwatched picks. |
| `/queue` | Full unwatched watchlist sorted by votes, with IMDB ratings. |
| `/info [title]` | Rich embed with plot, genre, IMDB rating, poster, and vote count. |
| `/remove [title]` | Remove a movie you suggested (suggester only). |

## Architecture

```
api/    FastAPI + SQLite — all CRUD operations; bot never touches the DB directly
bot/    discord.py — slash commands that call the API
misc/   .env.example and reference docs
```

The API and bot run as separate processes. The bot is a pure HTTP client — it calls API endpoints for every operation and holds no state of its own. The SQLite database is created automatically on first run.
