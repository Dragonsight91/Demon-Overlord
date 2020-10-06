import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse
from DemonOverlord.core.modules.help import gen_help


async def handler(command) -> discord.Embed:
    if command.action == None:
        return await gen_help(command)

    try:
        return McInfoResponse(
            command.action, command.bot.commands.minecraft[command.action], command.bot
        )


    except KeyError:
        return BadCommandResponse(command)


class McInfoResponse(TextResponse):
    def __init__(self, title: str, info: dict, bot: discord.Client):
        super().__init__(f"Minecraft Server - {title.capitalize()}", color=0x5D7C15)

        self.description = info["description"]
        self.set_thumbnail(
            url=info["logo"]
        )
        self.timeout = 120
        for field in info["list"]:
            self.add_field(
                name=field["name"], value=field["description"], inline=field["inline"]
            )
