from discord.ext import commands, tasks
import logging
import os
import sys
import solaire_helpers as sh
from scheduler import DiscordEvents

import requests

# Should come from the environment
QUELAAG_CREATE_URL = "http://quelaag:5000/create_form"
QUELAAG_GET_TZ_URL = "http://quelaag:5000/get_tz"
QUELAAG_SET_TZ_URL = "http://quelaag:5000/set_tz"
QUELAAG_CHECK_CLOSE_URL = "http://quelaag:5000/check_closing"
QUELAAG_SYNC_DB_URL = "http://quelaag:5000/sync_db"

logger = logging.getLogger("discord")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

bot_key = os.environ["BOT_KEY"]

bot = sh.Solaire(command_prefix=commands.when_mentioned_or("!"))


@bot.event
async def on_ready():
    logger.info(f"Bot {bot.user} active")
    check_for_ready_events.start()


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
            sh.get_time_response,
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
        sh.get_dates,
    )

    # Time of Day
    time_of_day = await bot.validated_response(
        ctx,
        "What range of times should be available each day? (Please provide start and end times as **HH:MM, HH:MM** (24H) your local time.)",
        "Please provide start and end times in order as **HH:MM, HH:MM** (24H) your local time.",
        sh.get_time_range,
    )

    # Event Length
    event_length = await bot.validated_response(
        ctx,
        "How long should your event be, in hours?",
        "This should be a number of hours, and less than 12.",
        sh.get_reasonable_hours,
    )

    # Expiration time
    expiration_time = await bot.validated_response(
        ctx,
        "How many hours should we wait for responses before setting a time?",
        "This should be a number of hours",
        sh.get_expiration,
    )

    logger.info(f"guild: {ctx.guild.id}")
    logger.info(f"channel: {ctx.channel.id}")
    logger.info(event_name)
    logger.info(date_resp)
    logger.info(time_of_day)
    logger.info(event_length)
    logger.info(expiration_time)

    event_request = sh.create_event_request_json(
        ctx.guild.id,
        ctx.channel.id,
        event_name,
        date_resp,
        time_of_day, 
        event_length,
        expiration_time,
        tz_resp
    )

    response = requests.post(QUELAAG_CREATE_URL, json=event_request)

    if response.status_code == 200:
        await author.send(f"Planning complete, see {ctx.channel.mention} for your planning link")
        await ctx.channel.send(f"Planning URL for {event_request['name']}: {response.json()['form_url']}. Please respond within {expiration_time} hours.")
        requests.get(QUELAAG_SYNC_DB_URL)
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

@tasks.loop(minutes=1)
async def check_for_ready_events():
    response = requests.get(QUELAAG_CHECK_CLOSE_URL)
    if len(parsed_response := response.json()) != 0: # This is totally clear.
        event_manager = DiscordEvents(bot_key)

        for event in parsed_response:
            start_time = sh.make_iso_timestamp(event['schedule_time'][0], event['schedule_time'][1], event['timezone'])
            end_time = sh.make_iso_timestamp(event['schedule_time'][0], event['schedule_time'][1]+int(event['event_length']), event['timezone'])
            scheduled = await event_manager.create_guild_event(
                guild_id=event["guild_id"],
                event_name=event["name"],
                event_description=f"Solaire scheduled event for {event['name']}",
                event_start_time=start_time,
                event_end_time=end_time,
                event_metadata={"location": "Lordran"}
            )
            if scheduled:
                logger.info(f"Scheduled event {event['name']} for {start_time} - {end_time}")
                ch = await bot.fetch_channel(event["channel_id"])
                await ch.send(f"Event Scheduled for {event['name']}")
            else:
                logger.info(f"Scheduling Failed for {event['name']} for {start_time} - {end_time}")

        requests.get(QUELAAG_SYNC_DB_URL)

bot.run(bot_key)
