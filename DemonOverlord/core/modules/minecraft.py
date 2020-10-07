import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse
from DemonOverlord.core.modules.help import gen_help


async def handler(command) -> discord.Embed:

    # default action if no action specified
    if command.action == None:
        return await gen_help(command)

    # if this works, it's a proper command, otherwise it isn't. any eror that isn't a KeyError is not being caught
    try:
        return McInfoResponse(
            command.action, command.bot.commands.minecraft[command.action], command.bot
        )

    except KeyError:
        return BadCommandResponse(command)


class McInfoResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class represents a custom formatted embed showing info about the minecraft server
    """

    def __init__(self, title: str, info: dict, bot: discord.Client):

        # initialize the super class
        super().__init__(f"Minecraft Server - {title.capitalize()}", color=0x5D7C15)

        # set all properties
        self.description = info["description"]
        self.set_thumbnail(url=info["logo"])
        self.timeout = 120

        # add the fields
        for field in info["list"]:
            self.add_field(
                name=field["name"], value=field["description"], inline=field["inline"]
            )
