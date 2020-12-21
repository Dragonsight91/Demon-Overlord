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
from DemonOverlord.core.util.logger import LogCommand, LogMessage, LogHeader,LogFormat

class DemonOverlord(discord.Client):
    """
    This class is the main bot class.
    """

    def __init__(self, argv: list):
        # initialize properties
        self.config = None
        self.commands = None
        self.database = None
        self.local = False

        print(LogHeader("Initializing Bot"))

        workdir = os.path.dirname(os.path.abspath(__file__))
        confdir = os.path.join(workdir, "../config")
        print(LogMessage(f"WORKDIR: {LogFormat.format(workdir, LogFormat.UNDERLINE)}", time=False))

        # set the main bot config
        self.config = BotConfig(self, confdir, argv)
        self.commands = CommandConfig(confdir)

        try:
            self.database = DatabaseConfig(self, confdir)
            print(LogMessage("Database connection established", time=False))
        except Exception:
            self.local = True
            print(LogMessage("Database connection not established, running in local mode", msg_type="WARNING", color=LogFormat.WARNING, time=False))

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
        print(LogMessage("Testing Data"))
        if self.local:
            print(LogMessage("No database configuration, running in local mode, some functions may be limited", msg_type="WARNING", color=LogFormat.WARNING))
        else:
            pass
            # self.loop.create_task(self.database.test_servers())

        
        print(LogHeader("startup done"))
        self.dispatch("my_event")


    async def on_message(self, message: discord.Message) -> None:

        # handle all commands
        if message.author != self.user and message.content.startswith(
            self.config.mode["prefix"]
        ):

            async with message.channel.typing():
                await self.wait_until_ready()
                command = Command(self, message)
                print(LogCommand(command))
                await command.exec() 