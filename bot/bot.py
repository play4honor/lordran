import discord
from discord.ext import commands
import logging
import sys
import bot_helpers as bh
from solaire import Solaire

import requests

# Should come from the environment
QUELAAG_CREATE_URL = "http://127.0.0.1:5000/create_form"
QUELAAG_GET_TZ_URL = "http://127.0.0.1:5000/get_tz"
QUELAAG_SET_TZ_URL = "http://127.0.0.1:5000/set_tz"

logger = logging.getLogger("discord")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

with open("../SECRETS/bot_key", "r") as f:
    bot_key = f.read()

bot = Solaire(command_prefix=commands.when_mentioned_or("!"))


@bot.event
async def on_ready():
    logger.info(f"Bot {bot.user} active")


@bot.command()
async def testo(ctx):

    await ctx.channel.send("Time is distorted in Lordran.")


@bot.command()
async def plan(ctx, *event_name):

    author = ctx.message.author
    event_name = " ".join(event_name)

    logger.info(f"!plan received from {author}")

    # Verify Continue
    continue_resp = await bot.validated_response(
        ctx,
        f"Would you like to continue planning event {event_name}?",
        "wat",
        lambda x: x,
    )

    if continue_resp.lower() not in {"yes", "y", "ye", "ya", "yiss"}:
        logger.info("dirty quitter")
        return

    user_tz = requests.post(QUELAAG_GET_TZ_URL, json={"user_id": author.id}).json()["tz"]

    if user_tz != -100:
        tz_resp = user_tz

    else:

        # Time Zone Determination
        tz_resp = await bot.validated_response(
            ctx,
            "Please enter your current time as HH:MM (24H) (so I can determine what time zone you're in).",
            "Please provide a time in HH:MM (24H) format.",
            bh.get_time_response,
        )

        tz_response = {"user_id": author.id, "utc_offset": tz_resp}
        response = requests.post(QUELAAG_SET_TZ_URL, json=tz_response)
        if response.status_code != 200:
            await author.send("Failed to save event details, go yell at your bot admin")

    await author.send(f"You're in the UTC{tz_resp} timezone.")

    
    # Event Dates
    date_resp = await bot.validated_response(
        ctx,
        "What dates would like your event to be? (Please give dates as **YYYY-MM-DD**, separated by commas.)",
        "Please give dates **in the future** as **YYYY-MM-DD**, separated by commas.",
        bh.get_dates,
    )

    # Time of Day
    time_of_day = await bot.validated_response(
        ctx,
        "What range of times should be available each day? (Please provide start and end times as **HH:MM, HH:MM** (24H) your local time.)",
        "Please provide start and end times in order as **HH:MM, HH:MM** (24H) your local time.",
        bh.get_time_range,
    )

    # Event Length
    event_length = await bot.validated_response(
        ctx,
        "How long should your event be, in hours?",
        "This should be a number of hours, and less than 12.",
        bh.get_reasonable_hours,
    )

    # Expiration time
    expiration_time = await bot.validated_response(
        ctx,
        "How many hours should we wait for responses before setting a time?",
        "This should be a number of hours",
        bh.get_expiration,
    )

    logger.info(event_name)
    logger.info(date_resp)
    logger.info(time_of_day)
    logger.info(event_length)
    logger.info(expiration_time)

    event_request = {
        "name": event_name,
        "dates": date_resp,
        "time_of_day": time_of_day,
        "event_length": event_length,
        "window_end_time": expiration_time,
    }

    response = requests.post(QUELAAG_CREATE_URL, json=event_request)

    if response.status_code == 200:
        await author.send(f"Planning complete, see {ctx.channel.mention} for your planning link")
        await ctx.channel.send(f"Planning URL for {event_request['name']}: {response.json()['form_url']}")
    else:
        await author.send("Failed to save event details, go yell at your bot admin")

@bot.command()
async def cancel():
    pass

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         pass
#     if not message.guild:
#         await message.channel.send("You are not currently planning an event. Please use `!plan` in a channel to start a planning session.")
#     else:
#         pass

bot.run(bot_key)
