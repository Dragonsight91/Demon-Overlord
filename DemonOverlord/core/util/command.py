from DemonOverlord.core.util.responses import (
    TextResponse,
    RateLimitResponse,
    ErrorResponse,
    BadCommandResponse,
)
from importlib import import_module
from inspect import getmembers

import discord
import pkgutil
import DemonOverlord.core.modules as cmds


class Command(object):
    def __init__(self, bot: discord.Client, message: discord.message):
        self.invoked_by = message.author
        self.mentions = message.mentions
        self.action = None
        self.bot = bot
        self.channel = message.channel
        self.full = message.content.replace("\n", " ")
        self.special = None
        self.message = message

        # create the command
        to_filter = ["", " ", None]
        temp = list(filter(lambda x: not x in to_filter, message.content.split(" ")))
        self.prefix = temp[0]
        self.command = temp[1]

        # Import all the submodules
        for importer, modname, ispkg in pkgutil.iter_modules(cmds.__path__):
            import_module("." + modname, "DemonOverlord.core.modules")

        # is it a special case??
        # WE DO
        if (
            temp[1] in bot.commands.interactions["alone"]
            or temp[1] in bot.commands.interactions["social"]
            or temp[1] in bot.commands.interactions["combine"]
        ):
            self.command = "interactions"
            self.action = temp[1]
            self.special = bot.commands.interactions
            self.params = temp[2:] if len(temp) > 2 else None

        # WE LUV
        elif temp[1] in bot.commands.relations:
            self.action = "relation"
            self.params = temp[2:] if len(temp) > 2 else None
        elif self.command == "chat":
            self.action = None
            self.params = temp[2:] if len(temp) > 2 else None
        # Y'AIN'T SPECIAL, YA LIL BITCH
        else:
            self.action = temp[2] if len(temp) > 2 else None
            self.params = temp[2:] if len(temp) > 3 else None

    async def exec(self) -> None:
        try:
            if self.bot.commands.ratelimits.exec(self):
                if self.command in dir(cmds):
                    response = await getattr(cmds, self.command).handler(self)

                # commented for 2.0.0a1
                # elif self.command == "vote":
                #    response = await vote.handler(self)

                else:
                    # rate limit error
                    response = RateLimitResponse(self)
                message = await self.channel.send(embed=response)

                # remove error messages and messages with timeout
                if isinstance(response, (TextResponse)):
                    if response.timeout > 0:
                        await message.delete(delay=response.timeout)

                    if isinstance(response, (ErrorResponse)):

                        # send an error meassage to dev channel
                        dev_channel = message.guild.get_channel(684100408700043303)
                        await dev_channel.send(embed=response)
                await self.message.delete()
        except:
            pass # we don't have to do anything, we just don't want an error message that we expect anyways

    async def rand_status(self) -> discord.BaseActivity:
        pass
