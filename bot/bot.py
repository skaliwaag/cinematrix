import os
import discord
from discord import app_commands
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
QUEUE_CHANNEL = os.getenv("QUEUE_CHANNEL_NAME", "movie-queue")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
guild = discord.Object(id=GUILD_ID)


# ── Helper ─────────────────────────────────────────────────────────────────────

def find_movie_id(title: str):
    # TODO: GET /movies, find match by title (case-insensitive), return id or None
    pass


# ── Commands ───────────────────────────────────────────────────────────────────

@tree.command(guild=guild, name="suggest", description="Add a movie to the watchlist")
@app_commands.describe(title="The movie title to suggest")
async def suggest(interaction: discord.Interaction, title: str):
    # TODO: POST /movies
    # TODO: handle 409 (already exists)
    # TODO: announce to #movie-queue channel if it exists
    pass


@tree.command(guild=guild, name="vote", description="Vote for a movie on the watchlist")
@app_commands.describe(title="The movie title to vote for")
async def vote(interaction: discord.Interaction, title: str):
    # TODO: find movie id, POST /movies/{id}/votes
    # TODO: handle 404 (not found) and 409 (already voted)
    pass


@tree.command(guild=guild, name="whats-next", description="Show the top-voted unwatched movie")
async def whats_next(interaction: discord.Interaction):
    # TODO: GET /whats-next, handle 404
    pass


@tree.command(guild=guild, name="watched", description="Mark a movie as watched")
@app_commands.describe(title="The movie you just watched")
async def watched(interaction: discord.Interaction, title: str):
    # TODO: find movie id, PATCH /movies/{id}/watched
    # TODO: prompt user to rate it after
    pass


@tree.command(guild=guild, name="rate", description="Rate a watched movie from 1 to 5")
@app_commands.describe(title="The movie to rate", score="Your score from 1 to 5")
async def rate(interaction: discord.Interaction, title: str, score: int):
    # TODO: validate score 1-5
    # TODO: find movie id, POST /movies/{id}/ratings
    # TODO: handle 400 (not watched) and 409 (already rated)
    pass


@tree.command(guild=guild, name="top-rated", description="Show the highest rated movies")
async def top_rated(interaction: discord.Interaction):
    # TODO: GET /top-rated, format and display results
    pass


@tree.command(guild=guild, name="history", description="Show everything the server has watched")
async def history(interaction: discord.Interaction):
    # TODO: GET /history, format and display results
    pass

@tree.command(guild=guild, name="poll top", description="Run a poll of the top 5 highest-voted movies"
async def poll_top(interaction: discord.Interaction):
    # Implement polling and database retrieval


@tree.command(guild=guild, name="poll random", description="Run a poll 5 random movies"
async def poll_top(interaction: discord.Interaction):
    # Implement polling and database retrieval

# ── Startup ────────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    await tree.sync(guild=guild)
    print(f"Logged in as {client.user} — commands synced")


client.run(TOKEN)
