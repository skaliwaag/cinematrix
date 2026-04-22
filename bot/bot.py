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

async def find_movie_id(title: str):
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/movies")
    title_lower = title.lower()
    for m in r.json():
        if m["title"].lower() == title_lower:
            return m["id"]
    return None


# ── Commands ───────────────────────────────────────────────────────────────────

@tree.command(guild=guild, name="suggest", description="Add a movie to the watchlist")
@app_commands.describe(title="The movie title to suggest")
async def suggest(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.post(
            f"{API_BASE}/movies",
            json={"title": title, "suggested_by": str(interaction.user)}
        )
    if r.status_code == 409:
        await interaction.followup.send(f"**{title}** is already on the watchlist.")
        return
    await interaction.followup.send(f"Added **{title}** to the watchlist!")
    channel = discord.utils.get(interaction.guild.text_channels, name=QUEUE_CHANNEL)
    if channel and channel.id != interaction.channel_id:
        await channel.send(
            f"**{interaction.user.display_name}** suggested **{title}** for movie night!"
        )


@tree.command(guild=guild, name="vote", description="Vote for a movie on the watchlist")
@app_commands.describe(title="The movie title to vote for")
async def vote(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    movie_id = await find_movie_id(title)
    if movie_id is None:
        await interaction.followup.send(f"**{title}** was not found on the watchlist.")
        return
    async with httpx.AsyncClient() as http:
        r = await http.post(
            f"{API_BASE}/movies/{movie_id}/votes",
            json={"user_id": str(interaction.user.id)}
        )
    if r.status_code == 409:
        await interaction.followup.send(f"You already voted for **{title}**.")
        return
    await interaction.followup.send(f"Voted for **{title}**!")


@tree.command(guild=guild, name="whats-next", description="Show the top-voted unwatched movie")
async def whats_next(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/whats-next")
    if r.status_code == 404:
        await interaction.followup.send(
            "No unwatched movies on the list yet. Use `/suggest` to add some!"
        )
        return
    movie = r.json()
    votes = movie.get("vote_count", 0)
    await interaction.followup.send(
        f"Next up: **{movie['title']}** with **{votes}** vote(s)."
    )


@tree.command(guild=guild, name="watched", description="Mark a movie as watched")
@app_commands.describe(title="The movie you just watched")
async def watched(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    movie_id = await find_movie_id(title)
    if movie_id is None:
        await interaction.followup.send(f"**{title}** was not found on the watchlist.")
        return
    async with httpx.AsyncClient() as http:
        r = await http.patch(f"{API_BASE}/movies/{movie_id}/watched")
    if r.status_code == 404:
        await interaction.followup.send(f"**{title}** was not found.")
        return
    await interaction.followup.send(
        f"Marked **{title}** as watched! Use `/rate` to leave a score."
    )


@tree.command(guild=guild, name="rate", description="Rate a watched movie from 1 to 5")
@app_commands.describe(title="The movie to rate", score="Your score from 1 to 5")
async def rate(interaction: discord.Interaction, title: str, score: int):
    await interaction.response.defer()
    if score < 1 or score > 5:
        await interaction.followup.send("Score must be between 1 and 5.")
        return
    movie_id = await find_movie_id(title)
    if movie_id is None:
        await interaction.followup.send(f"**{title}** was not found on the watchlist.")
        return
    async with httpx.AsyncClient() as http:
        r = await http.post(
            f"{API_BASE}/movies/{movie_id}/ratings",
            json={"user_id": str(interaction.user.id), "score": score}
        )
    if r.status_code == 400:
        await interaction.followup.send(f"**{title}** hasn't been marked as watched yet.")
        return
    if r.status_code == 409:
        await interaction.followup.send(f"You already rated **{title}**.")
        return
    await interaction.followup.send(f"Rated **{title}** {score}/5!")


@tree.command(guild=guild, name="top-rated", description="Show the highest rated movies")
async def top_rated(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/top-rated")
    movies = r.json()
    if not movies:
        await interaction.followup.send("No rated movies yet.")
        return
    lines = ["**Top Rated Movies:**"]
    for i, m in enumerate(movies[:10], 1):
        avg = m.get("avg_score")
        avg_str = f"{avg}/5" if avg is not None else "no ratings"
        count = m.get("rating_count", 0)
        lines.append(f"{i}. **{m['title']}** — {avg_str} ({count} rating(s))")
    await interaction.followup.send("\n".join(lines))


@tree.command(guild=guild, name="history", description="Show everything the server has watched")
async def history(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/history")
    movies = r.json()
    if not movies:
        await interaction.followup.send("No movies watched yet.")
        return
    lines = ["**Watch History:**"]
    for m in movies:
        avg = m.get("avg_score")
        avg_str = f"{avg}/5" if avg is not None else "no ratings"
        date_str = m.get("watched_at") or "unknown date"
        lines.append(f"• **{m['title']}** — watched {date_str} — {avg_str}")
    await interaction.followup.send("\n".join(lines))


# ── Startup ────────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    await tree.sync(guild=guild)
    print(f"Logged in as {client.user} — commands synced")


client.run(TOKEN)
