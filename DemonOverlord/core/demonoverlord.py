import discord
import os
import random
import asyncio


# core imports
from DemonOverlord.core.util import services
from DemonOverlord.core.util.config import (
    CommandConfig,
    BotConfig,
    DatabaseConfig,
    APIConfig,
)
from DemonOverlord.core.util.command import Command
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
        print(LogMessage(f"Removed guild {guild.name}, removing all data from database"))
        await self.database.remove_guild(guild.id)

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

                # test data in tables, since certain entries NEED to exist
                print(LogMessage("Checking Table Data"))
                if not await self.database.data_test(self.guilds):
                    print(LogMessage("Some default data desn't exist, trying to correct...", msg_type=LogType.WARNING))
                    await self.database.data_fix()
                else:
                    print(LogMessage("All Servers are in place and seem to be correctly set up."))


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

        # finish up and send the ready event
        print(LogHeader("startup done"))
        self._db_ready.set()

    async def on_message(self, message: discord.Message) -> None:

        # handle all commands
        if message.author != self.user and message.content.startswith(
            self.config.mode["prefix"]
        ):

            # signal typing status
            async with message.channel.typing():

                # wait until bot has finished loading
                await self.wait_until_done()

                # build the command and execute it
                command = Command(self, message)
                print(LogCommand(command))
                await command.exec()
