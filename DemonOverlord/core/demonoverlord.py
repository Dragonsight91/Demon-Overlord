import discord
import sys
import os
import random
import asyncio


# core imports
from DemonOverlord.core.util.config import (
    CommandConfig,
    BotConfig,
    DatabaseConfig,
    APIConfig,
)
from DemonOverlord.core.util.command import Command
from DemonOverlord.core.util.logger import LogCommand, LogMessage, LogHeader,LogFormat, LogType

class DemonOverlord(discord.Client):
    """
    This class is the main bot class.
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
        print(LogMessage(f"WORKDIR: {LogFormat.format(workdir, LogFormat.UNDERLINE)}", time=False))

        # set the main bot config
        self.config = BotConfig(self, confdir, argv)
        self.commands = CommandConfig(confdir)

        try:
            self.database = DatabaseConfig(self, confdir)            
            print(LogMessage("Database connection established", time=False))
        except Exception as e:
            self.local = True
            print(LogMessage("Database connection not established, running in local mode", msg_type="WARNING", color=LogFormat.WARNING, time=False))
            print(LogMessage(f"{type(e).__name__}: {e}" , msg_type=LogType.ERROR))
        self.api = APIConfig(self.config)

        #

        # initial presence
        presence= random.choice(self.config.status_messages) 
        presence_type = str(presence.type).split(".")[1]
        print(LogMessage(f"Initial Presence: \"{LogFormat.format(f'{presence_type} {presence.name}', LogFormat.BOLD)}\"", time=False))

        # intents
        intents = discord.Intents().all()
        print(LogMessage(f"set intents to: {intents.value}", time=False))

        # initializing discord client
        super().__init__(intents=intents, presence=presence)
        

    @staticmethod
    async def change_status(client):
        """
            Change the status to a random one one specified in the config
        """
        await client.wait_until_ready()
        while True:
            if random.random() < 0.05:
                presence = random.choice(client.config.status_messages)
                
                await client.change_presence(activity=presence)
                presence_type = str(presence.type).split(".")[1]
                print(LogMessage(f"Set Status \"{LogFormat.format(f'{presence_type} {presence.name}', LogFormat.BOLD)}\""))

            await asyncio.sleep(3600)
    async def wait_until_done(self):
        await self.wait_until_ready()
        await self._db_ready.wait()

    async def on_ready(self) -> None:
        print(LogHeader("CONNECTED SUCCESSFULLY"))
        print(LogMessage(f"{'USERNAME': <10}: {self.user.name}", time=False))
        print(LogHeader("loading other data"))


        try:
            self.config.post_connect(self)
        except Exception:
            print(LogMessage("Post connection config Failed", msg_type="WARNING", color=LogFormat.WARNING))
        else:
            print(LogMessage("Post Connection config Finished"))
        
        # testing the database
        print(LogMessage("Testing Database..."))
        if self.local:
            print(LogMessage("No database configuration, running in local mode, some functions may be limited", msg_type="WARNING", color=LogFormat.WARNING))
        else:
            try:
                # test schemas
                if not await self.database.schema_test():
                    print(LogMessage("some schemas don't exist, trying to correct...", msg_type=LogType.WARNING))
                    await self.database.schema_fix()

                # test tables
                if not await self.database.table_test():
                    print(LogMessage("Some tables don't exist or are wrong, trying to correct...", msg_type=LogType.WARNING))
                    await self.database.table_fix()

                # # test data in tables, since certain entries NEED to exist
                # if not await self.database._data_test(self.guilds):
                #     self.database._data_test()
            except Exception as e:
                print(LogMessage("Something went wrong when testing and/or fixing the database, continuing in local mode", msg_type=LogType.ERROR))
                print(LogMessage(e, msg_type=LogType.ERROR))
                self.local = True
        
        print(LogHeader("startup done"))
        self._db_ready.set()


    async def on_message(self, message: discord.Message) -> None:

        # handle all commands
        if message.author != self.user and message.content.startswith(
            self.config.mode["prefix"]
        ):

            async with message.channel.typing():
                await self.wait_until_done()
                command = Command(self, message)
                print(LogCommand(command))
                await command.exec() 