import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse
from DemonOverlord.core.modules.help import gen_help


async def handler(command):

    # default action if there is none: just get the help info for the command
    if command.action == None:
        return await gen_help(command)

    # if we have it: use it. if it's wrong, throw an error
    elif command.action in command.bot.commands.izzylinks:
        try:
            return IzzyLink(command, command.bot.commands.izzylinks[command.action])
        except:
            return BadCommandResponse(command)

    # default action if shit goes wee: bad comand
    else:
        return BadCommandResponse(command)


class IzzyLink(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles deconstructing the data from izzy.json into a proper discord embed
    """

    def __init__(self, command, links: dict):

        # initialize the Parent with necessary attributes
        super().__init__(
            f'Izzy - {command.action.replace("_", " ").upper()}',
            color=0x784381,
            icon=command.bot.config.izzymojis["izzyyay"],
        )

        if command.action != "forbidden_fruit":

            # get and set the description for the command
            command_obj = list(
                filter(lambda x: x["command"] == "izzy", command.bot.commands.list)
            )[0]
            action_obj = list(
                filter(lambda x: x["action"] == command.action, command_obj["actions"])
            )
            self.description = action_obj[0]["description"]
        else:
            # set the timeout and the description (this is static, no need to load it from config)
            self.timeout = 20
            self.description = "This is the forbidden fruit. Careful, it vanishes."

        # set all links as fields
        for link in links:
            self.add_field(name=link["name"], value=link["link"])
