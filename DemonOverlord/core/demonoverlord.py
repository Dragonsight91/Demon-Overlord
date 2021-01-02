import discord
import os
import random
import asyncio
import re

from discord import guild
from discord import embeds


# core imports
from DemonOverlord.core.util import services
from DemonOverlord.core.util.config import (
    CommandConfig,
    BotConfig,
    DatabaseConfig,
    APIConfig,
)

from DemonOverlord.core.util.command import Command
from DemonOverlord.core.util.responses import WelcomeResponse
from DemonOverlord.core.util.logger import (
    LogCommand,
    LogMessage,
    LogHeader,
    LogFormat,
    LogType,
)


class DemonOverlord(discord.Client):
    """
    This class is the main bot class, which represents the client's connection to discord
    """

    def __init__(self, argv: list, workdir):
        # initialize properties
        self.config = None
        self.commands = None
        self.database = None
        self.local = False
        self._db_ready = asyncio.Event()

        print(LogHeader("Initializing Bot"))

        confdir = os.path.join(workdir, "config")
        print(
            LogMessage(
                f"WORKDIR: {LogFormat.format(workdir, LogFormat.UNDERLINE)}", time=False
            )
        )

        # set the main bot config
        self.config = BotConfig(self, confdir, argv)
        self.commands = CommandConfig(confdir)

        try:
            self.database = DatabaseConfig(self, confdir)
            print(LogMessage("Database connection established", time=False))
        except Exception as e:
            self.local = True
            print(
                LogMessage(
                    "Database connection not established, running in local mode",
                    msg_type="WARNING",
                    color=LogFormat.WARNING,
                    time=False,
                )
            )
            print(LogMessage(f"{type(e).__name__}: {e}", msg_type=LogType.ERROR))
        self.api = APIConfig(self.config)

        # initial presence
        presence = random.choice(self.config.status_messages)
        presence_type = str(presence.type).split(".")[1]
        print(
            LogMessage(
                f"Initial Presence: \"{LogFormat.format(f'{presence_type} {presence.name}', LogFormat.BOLD)}\"",
                time=False,
            )
        )

        # set intents
        intents = discord.Intents().all()
        print(LogMessage(f"set intents to: {intents.value}", time=False))

        # initializing discord client
        super().__init__(intents=intents, activity=presence)

        # initialize our own services
        try:
            self.loop.create_task(services.change_status(self))
            self.loop.create_task(services.fetch_steamdata(self))
        except Exception:
            print(LogMessage("Setup for services failed"))

    async def wait_until_done(self) -> None:
        await self.wait_until_ready()
        await self._db_ready.wait()

    async def on_guild_join(self, guild) -> None:
        print(LogMessage(f"Joined guild {guild.name}, setting up database..."))
        await self.database.add_guild(guild.id)

    async def on_guild_remove(self, guild) -> None:
        print(
            LogMessage(f"Removed guild {guild.name}, removing all data from database")
        )
        await self.database.remove_guild(guild.id)

    async def on_member_join(self, member: discord.Member):
        if self.local or member.pending:
            return
        autoroles = await self.database.get_autorole(member.guild.id)
        if autoroles != None:
            role = member.guild.get_role(autoroles["role_id"])
            roles = [role] if role else []

            if len(roles) > 0:
                try:
                    await member.add_roles(
                        *roles, reason="Automatic Role Assignment", atomic=True
                    )
                    print(LogMessage("Autorole assigned successfully"))
                except discord.errors.Forbidden:
                    print(
                        LogMessage(
                            f"Issue on Server '{member.guild}', permissions missing."
                        )
                    )

        welcome = await self.database.get_welcome(member.guild.id)
        if welcome != None:
            response = WelcomeResponse(welcome, self, member)
            await response.channel.send(embed=response)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self.wait_until_done()

        if not after.pending and before.pending != after.pending:

            autoroles = await self.database.get_autorole(
                after.guild.id, wait_pending=True
            )
            if autoroles != None:
                role = after.guild.get_role(autoroles["role_id"])
                roles = [role] if role else []

                if len(roles) > 0:
                    try:
                        await after.add_roles(
                            *roles, reason="Automatic Role Assignment", atomic=True
                        )
                        print(LogMessage("Autorole assigned successfully"))
                    except discord.errors.Forbidden:
                        print(
                            LogMessage(
                                f"Issue on Server '{after.guild}', permissions missing."
                            )
                        )

            welcome = await self.database.get_welcome(after.guild.id, wait_pending=True)
            if welcome != None and welcome["wait_pending"]:
                welcome = WelcomeResponse(welcome, self, after)
                await welcome.channel.send(embed=welcome)

    async def on_ready(self) -> None:
        print(LogHeader("CONNECTED SUCCESSFULLY"))
        print(LogMessage(f"{'USERNAME': <10}: {self.user.name}", time=False))
        print(LogHeader("loading other data"))

        # configure all things that need a connection to discord
        try:
            self.config.post_connect(self)
        except Exception:
            print(
                LogMessage(
                    "Post connection config Failed",
                    msg_type="WARNING",
                    color=LogFormat.WARNING,
                )
            )
        else:
            print(LogMessage("Post Connection config Finished"))

        # test the database
        print(LogMessage("Testing Database..."))
        if self.local:
            # we're in local mode, no connection exists
            print(
                LogMessage(
                    "No database configuration, running in local mode, some functions may be limited",
                    msg_type="WARNING",
                    color=LogFormat.WARNING,
                )
            )
        else:
            try:
                # test schemas
                print(LogMessage("Checking Schemas..."))
                if not await self.database.schema_test():
                    print(
                        LogMessage(
                            "Some schemas don't exist, correcting...",
                            msg_type=LogType.WARNING,
                        )
                    )
                    await self.database.schema_fix()
                else:
                    print(LogMessage("All schemas are in place."))

                # test tables
                print(LogMessage("Checking Tables..."))
                if not await self.database.table_test():
                    print(
                        LogMessage(
                            "Some tables don't exist or are wrong, correcting...",
                            msg_type=LogType.WARNING,
                        )
                    )
                    await self.database.table_fix()
                else:
                    print(LogMessage("All Tables are in place and seem to be correct."))

                # print(LogMessage("Updating Guild status...."))
                # self.database.update_guilds(self.guilds)

            except Exception as e:
                # catch all errors and log them
                print(
                    LogMessage(
                        "Something went wrong when testing and/or fixing the database, continuing in local mode",
                        msg_type=LogType.ERROR,
                    )
                )
                print(LogMessage(e, msg_type=LogType.ERROR))
                self.local = True
        for guild in self.guilds:
            print(f"Joined guild {guild.name} at {guild.me.joined_at}")

        # finish up and send the ready event
        print(LogHeader("startup done"))
        self._db_ready.set()

    async def on_message(self, message: discord.Message) -> None:

        # handle all commands
        if not message.author.bot and message.content.startswith(
            self.config.mode["prefix"]
        ):

            try:
                # signal typing status
                async with message.channel.typing():

                    # wait until bot has finished loading
                    await self.wait_until_done()

                    # build the command and execute it
                    command = Command(self, message)
                    print(LogCommand(command))
                    await command.exec()
            except discord.errors.Forbidden:
                print(
                    LogMessage(
                        "No permission to send to channel", msg_type=LogType.ERROR
                    )
                )
