import discord

from DemonOverlord.core.util.responses import TextResponse


async def handler(command) -> discord.Embed:
    # make a dict for a specific message (not needed if you have more than one)
    msg = {"name": "Response:", "value": f"Hello, {command.invoked_by.mention}"}

    # return a text response, since there is nothing else to do here
    return TextResponse(
        "Command - Hello",
        color=0xEF1DD9,
        icon=command.bot.config.izzymojis["hello"] or "🌺",
        msg=msg,
    )
