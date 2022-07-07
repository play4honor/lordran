import discord
from discord.ext import commands
import logging
import datetime

logger = logging.getLogger("discord")

def get_utc_offset(local_time: datetime.time):

    hour_diff = local_time.hour - datetime.datetime.utcnow().hour

    if hour_diff > 12:
        hour_diff = hour_diff - 24
    elif hour_diff < -12:
        hour_diff = hour_diff + 24

    return hour_diff


def get_time_response(res):

    try:
        tm = datetime.time.fromisoformat(res)
        utc_offset = get_utc_offset(tm)
        prefix = "+" if utc_offset > 0 else ""
        tm_str = f"{prefix}{utc_offset}"
    except ValueError:
        tm_str = None

    return tm_str


def get_time_range(res):

    time_list = [d.strip() for d in res.split(",")]
    try:
        iso_list = [datetime.time.fromisoformat(d) for d in time_list]
    except ValueError:
        return None

    if len(iso_list) != 2 or iso_list[0] >= iso_list[1]:
        return None

    return [str(t) for t in iso_list]


def get_reasonable_hours(res):
    try:
        hrs = int(res)
        if hrs >= 12:
            hrs = None
    except ValueError:
        hrs = None
    return hrs


def get_dates(res):
    date_list = [d.strip() for d in res.split(",")]
    try:
        iso_list = [datetime.date.fromisoformat(d) for d in date_list]
    except ValueError:
        return None

    # mirai
    for d in iso_list:
        if d < datetime.date.today():
            return None

    return [d.isoformat() for d in iso_list]


def get_expiration(res):
    try:
        hrs = float(res)
    except ValueError:
        hrs = None
    return hrs

def make_iso_timestamp(date, hours, tz=0):
    if tz >= 0:
        tz_str = f"+{tz :02}:00"
    else:
        tz_str = f"{tz :03}:00"

    return f"{date}T{hours :02}:00:00{tz_str}"

def check_response(m, author):

    return m.author == author and isinstance(m.channel, discord.DMChannel)


def create_event_request_json(
    guild_id, channel_id, event_name, date_resp, time_of_day, event_length, expiration_time, timezone
):
    return {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "timezone": timezone,
        "name": event_name,
        "dates": date_resp,
        "time_of_day": time_of_day,
        "event_length": event_length,
        "expiration_time": expiration_time,
    }


class Solaire(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def validated_response(self, ctx, question, error_msg, validation_func):

        author = ctx.message.author

        await author.send(question)

        is_valid = False

        while not is_valid:

            reply = await self.wait_for(
                "message", check=lambda m: check_response(m, author), timeout=60
            )

            validated_reply = validation_func(reply.content)

            if validated_reply is None:
                await author.send(error_msg)
            else:
                is_valid = True

        return validated_reply
