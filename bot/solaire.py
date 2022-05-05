import discord
from discord.ext import commands
import logging
import sys

logger = logging.getLogger("discord")


def check_response(m, author):

    return m.author == author and isinstance(m.channel, discord.DMChannel)


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
