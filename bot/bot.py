import os
import datetime
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
    movie = r.json()
    year = f" ({movie['year']})" if movie.get("year") else ""
    rating = f" — ⭐ {movie['imdb_rating']}" if movie.get("imdb_rating") else ""
    genre = f"\n{movie['genre']}" if movie.get("genre") else ""
    poster = movie.get("poster_url")
    msg = f"Added **{movie['title']}**{year}{rating} to the watchlist!{genre}"
    if poster:
        msg += f"\n{poster}"
    await interaction.followup.send(msg)
    channel = discord.utils.get(interaction.guild.text_channels, name=QUEUE_CHANNEL)
    if channel and channel.id != interaction.channel_id:
        await channel.send(
            f"**{interaction.user.display_name}** suggested **{movie['title']}**{year}{rating} for movie night!{genre}"
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


@tree.command(guild=guild, name="poll-top", description="Run a Discord poll on the 5 most-voted unwatched movies")
async def poll_top(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/poll/top")
    if r.status_code == 404:
        await interaction.followup.send(
            "Not enough movies on the watchlist yet. Use `/suggest` to add some!"
        )
        return
    movies = r.json()
    poll = discord.Poll(question="Which movie should we watch next?", duration=datetime.timedelta(hours=24))
    for m in movies:
        poll.add_answer(text=m["title"])
    await interaction.followup.send(poll=poll)


@tree.command(guild=guild, name="poll-random", description="Run a Discord poll on 5 random unwatched movies")
async def poll_random(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/poll/random")
    if r.status_code == 404:
        await interaction.followup.send(
            "Not enough movies on the watchlist yet. Use `/suggest` to add some!"
        )
        return
    movies = r.json()
    poll = discord.Poll(question="Which movie should we watch next? (random picks)", duration=datetime.timedelta(hours=24))
    for m in movies:
        poll.add_answer(text=m["title"])
    await interaction.followup.send(poll=poll)


@tree.command(guild=guild, name="remove", description="Remove a movie you suggested from the watchlist")
@app_commands.describe(title="The movie title to remove")
async def remove(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    movie_id = await find_movie_id(title)
    if movie_id is None:
        await interaction.followup.send(f"**{title}** was not found on the watchlist.")
        return
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/movies/{movie_id}")
    movie = r.json()
    if movie["suggested_by"] != str(interaction.user):
        await interaction.followup.send(
            f"You can't remove **{title}** — it was suggested by {movie['suggested_by']}."
        )
        return
    async with httpx.AsyncClient() as http:
        await http.delete(f"{API_BASE}/movies/{movie_id}")
    await interaction.followup.send(f"Removed **{title}** from the watchlist.")


@tree.command(guild=guild, name="info", description="Show detailed info about a movie on the watchlist")
@app_commands.describe(title="The movie title to look up")
async def info(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    movie_id = await find_movie_id(title)
    if movie_id is None:
        await interaction.followup.send(f"**{title}** was not found on the watchlist.")
        return
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/movies/{movie_id}")
    m = r.json()

    year_str = f" ({m['year']})" if m.get("year") else ""
    embed = discord.Embed(
        title=f"{m['title']}{year_str}",
        color=discord.Color.gold(),
    )
    if m.get("plot"):
        embed.description = m["plot"]
    if m.get("poster_url"):
        embed.set_thumbnail(url=m["poster_url"])
    if m.get("genre"):
        embed.add_field(name="Genre", value=m["genre"], inline=True)
    if m.get("imdb_rating"):
        embed.add_field(name="IMDB Rating", value=f"⭐ {m['imdb_rating']}", inline=True)
    embed.add_field(name="Suggested by", value=m["suggested_by"], inline=True)
    embed.add_field(name="Votes", value=str(m.get("vote_count", 0)), inline=True)
    status = "Watched" if m["watched"] else "Unwatched"
    if m.get("watched_at"):
        status += f" ({m['watched_at']})"
    embed.add_field(name="Status", value=status, inline=True)
    if m.get("imdb_id"):
        embed.add_field(
            name="IMDB", value=f"[View on IMDB](https://www.imdb.com/title/{m['imdb_id']}/)", inline=True
        )

    await interaction.followup.send(embed=embed)


@tree.command(guild=guild, name="queue", description="Show the current unwatched movie watchlist")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{API_BASE}/queue")
    movies = r.json()
    if not movies:
        await interaction.followup.send(
            "The watchlist is empty. Use `/suggest` to add some movies!"
        )
        return
    lines = ["**Watchlist:**"]
    for i, m in enumerate(movies, 1):
        year = f" ({m['year']})" if m.get("year") else ""
        rating = f" — ⭐ {m['imdb_rating']}" if m.get("imdb_rating") else ""
        votes = m.get("vote_count", 0)
        vote_str = f" — {votes} vote(s)" if votes else ""
        lines.append(f"{i}. **{m['title']}**{year}{rating}{vote_str}")
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
