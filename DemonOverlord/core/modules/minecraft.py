import discord

from DemonOverlord.core.util.responses import TextResponse

async def handler(command) -> discord.Embed:
    if command.action == "info":
        pass

class McInfoResponse(TextResponse):
    def __init__(self, title:str, info:dict, bot :discord.Client):
        super().__init__(f"Minecraft Server - {title}", color=0x5D7C15, icon=bot.config.izzymojis[""])