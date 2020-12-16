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
from DemonOverlord.core.util.logger import LogCommand, LogMessage, LogHeader,TermFormat

class DemonOverlord(discord.Client):
    """
    This class is the main bot class.
    """

    def __init__(self, argv: list):
        intents = discord.Intents().all()
        super().__init__(intents=intents)

        workdir = os.path.dirname(os.path.abspath(__file__))
        confdir = os.path.join(workdir, "../config")

        # set the main bot config
        self.config = BotConfig(self, confdir, argv)
        self.commands = CommandConfig(confdir)
        #\ self.database = DatabaseConfig(self, confdir)
        self.api = APIConfig(self.config)


    async def change_status(self):
        """
            Change the status to a random one one specified in the config
        """
        await self.wait_until_ready()
        while True:
            if random.random() < 0.05:
                presence = random.choice(self.config.status_messages)
                
                await self.change_presence(activity=presence)
                presence_type = str(presence.type).split(".")[1]
                print(LogMessage(f"Set Status \"{TermFormat.format(f'{presence_type} {presence.name} ', TermFormat.BOLD)}\""))

            await asyncio.sleep(1800)

    async def on_ready(self) -> None:
        print(LogHeader("CONNECTED SUCCESSFULLY"))
        print(LogMessage(f"Connected as {self.user.name}"))
        print(LogHeader("loading other data"))


        try:
            self.config.post_connect(self)
        except Exception:
            print(LogMessage("Post connection config Failed", prefix=TermFormat.format("WARNING", TermFormat.WARNING)))
        else:
            print(LogMessage("Post Connection config Finished"))
        
        print(LogMessage("Testing Data"))

        presence=random.choice(self.config.status_messages)
        presence_type = str(presence.type).split(".")[1]
        print(LogMessage(f"Set Status \"{TermFormat.format(f'{presence_type} {presence.name}', TermFormat.BOLD)}\""))
        
        await self.change_presence(activity=presence)
        print(LogHeader("startup done"))

    async def on_message(self, message: discord.Message) -> None:

        # handle all commands
        if message.author != self.user and message.content.startswith(
            self.config.mode["prefix"]
        ):
            await self.wait_until_ready()

            command = Command(self, message)
            print(LogCommand(command))
            await command.exec() 
            await self.change_status()