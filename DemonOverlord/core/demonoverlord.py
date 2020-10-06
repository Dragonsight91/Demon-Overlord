import discord
import sys
import os

# core imports
from DemonOverlord.core.util.config import (
    CommandConfig,
    BotConfig,
    DatabaseConfig,
    APIConfig,
)
from DemonOverlord.core.util.command import Command


class DemonOverlord(discord.Client):
    def __init__(self, argv: list):
        super().__init__()
        workdir = os.path.dirname(os.path.abspath(__file__))
        confdir = os.path.join(workdir, "../config")

        # set the main bot config
        self.config = BotConfig(self, confdir, argv)
        self.commands = CommandConfig(confdir)
        self.database = DatabaseConfig()
        self.api = APIConfig(self.config)

    async def on_ready(self) -> None:
        print("====== CONNECTED SUCCESSFULLY ======")
        print(f"[MSG]: Connected as: {self.user.name}")
        print("====== LOADING EXTRA MODULES ======")
        try:
            self.config.post_connect(self)
        except Exception as e:
            print("[WARN] : Izzymojis not loaded")
        else:
            print("[MSG]: Loaded Izzymojis")
        print("====== STARTUP DONE ======")

    async def on_message(self, message: discord.Message) -> None:
        if message.author != self.user and message.content.startswith(
            self.config.mode["prefix"]
        ):
            command = Command(self, message)
            await command.exec()
