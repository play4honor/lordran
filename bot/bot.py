import discord
from discord.ext import commands
import logging
import sys
import bot_helpers as bh

logger = logging.getLogger("discord")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

with open("./SECRETS/bot_key", "r") as f:
    bot_key = f.read()

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"))


@bot.event
async def on_ready():
    logger.info(f"Bot {bot.user} active")


@bot.command()
async def testo(ctx):

    await ctx.channel.send("Time is distorted in Lordran.")


@bot.command()
async def plan(ctx, event_name):
    author = ctx.message.author

    logger.info(f"!plan received from {author}")

    def check_response(m):

        return m.author == author and isinstance(m.channel, discord.DMChannel)

    await author.send(f"Would you like to continue planning event {event_name}?")

    reply = await bot.wait_for("message", check=check_response, timeout=60)

    await author.send(
        f"Please enter your current time as HH:MM (24H) (so I can determine what time zone you're in)."
    )

    is_valid_time = False

    while not is_valid_time:

        reply = await bot.wait_for("message", check=check_response, timeout=60)

        formatted_reply = bh.get_time_response(reply.content)

        if formatted_reply is not None:
            is_valid_time = True
            utc_offset = bh.get_utc_offset(formatted_reply)
            prefix = "+" if utc_offset > 0 else ""
        else:
            await author.send("Please provide a time in HH:MM (24H) format.")

    await author.send(f"You're in the UTC{prefix}{utc_offset} timezone.")


bot.run(bot_key)
