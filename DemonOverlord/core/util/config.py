import discord
import os
import sys
import json
import asyncio
import psycopg2

from DemonOverlord.core.util.api import TenorAPI, InspirobotAPI
from DemonOverlord.core.util.limit import RateLimiter


class BotConfig(object):
    """
    This is the Bot config object, it holds the core configuration of the bot
    """

    def __init__(self, bot: discord.Client, confdir: str, argv: list):
        # set all vars None first, this also gives us a list of all currently available vars
        self.raw = None
        self.mode = None
        self.izzymojis = dict()
        self.token = None
        self.env = None
        self.emoji = None
        self.status_messages = list()

        # get the raw config.json
        with open(os.path.join(confdir, "config.json")) as f:
            self.raw = json.load(f)

        # create config from cli stuff
        for arg in argv:

            # set bot mode
            if arg in self.raw["cli_options"]["bot_modes"]:
                self.mode = self.raw["cli_options"]["bot_modes"][argv[1]]
            else:
                self.mode = self.raw["cli_options"]["bot_modes"]["--dev"]

            

        status_types = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,  # not used
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing
        }
        for message in self.raw["status_messages"]:
            
            self.status_messages.append(
                discord.Activity(
                    name=message["content"], 
                    type=status_types[message["type"]], 
                    url=("https://www.youtube.com/watch?v=dBRSjTKdtrI" if "Vecter" in message["content"] else None)
                )
            )

        # set the token
        self.token = os.environ.get(self.mode["tokenvar"])
        self.env = self.raw["env_vars"]
        self.emoji = self.raw["emoji"]

    def post_connect(self, bot: discord.Client):
        # generate izzymoji list
        for key in self.raw["izzymojis"].keys():
            self.izzymojis[key] = bot.get_emoji(self.raw["izzymojis"][key])


class APIConfig(object):
    """
    This is the API config class, it combines and initializes the APIs into a single point
    """

    def __init__(self, config: BotConfig):
        # var init
        self.tenor = None
        self.inspirobot = InspirobotAPI()

        tenor_key = os.environ.get(config.env["tenor"][0])
        if tenor_key:
            self.tenor = TenorAPI(tenor_key)


class DatabaseConfig(object):
    """
    This class handles all Database integrations and connections as well as setup and testing the database.
    """

    def __init__(self, bot, confdir):
        temp = {}
        for var in bot.config.env["postgres"]:
            temp.update({var: os.environ[var]})

        self.db_user = temp["POSTGRES_USER"]
        self.db_pass = temp["POSTGRES_PASSWORD"]
        self.db_addr = temp["POSTGRES_SERVER"]
        self.db_port = temp["POSTGRES_PORT"]
        self.connection = None

    async def db_test(self):
        """
        Test if all databases are connected and set up properly
        """
        pass

    async def db_create(self, server_id):
        pass

    async def db_connect(self):
        self.connection = psycopg2.connect(
            user=self.db_user,
            password=self.db_pass,
            host=self.db_addr,
            port=self.db_port,
            database="bot_core",
        )
        connection.set_session(autocommit=True)



class CommandConfig(object):
    """
    This is the Command Config class. It handles all the secondary configurations for specific commands and/or command groups
    """

    def __init__(self, confdir: str):
        self.interactions = None
        self.command_info = None
        self.list = []
        self.ratelimits = None
        self.izzylinks = None
        self.chats = None
        self.short = dict()
        self.minecraft = dict()

        with open(os.path.join(confdir, "interactions.json")) as f:
            self.interactions = json.load(f)

        with open(os.path.join(confdir, "cmd_info.json")) as f:
            self.command_info = json.load(f)

        with open(os.path.join(confdir, "special/izzy.json")) as f:
            self.izzylinks = json.load(f)

        with open(os.path.join(confdir, "special/chats.json")) as f:
            self.chats = json.load(f)

        with open(os.path.join(confdir, "special/minecraft.json")) as f:
            self.minecraft = json.load(f)

        # load in the command list and update the short commands
        for i in self.command_info.keys():
            for j in self.command_info[i]["commands"]:
                self.list.append(j)
                if j["short"]:
                    self.short.update({j["short"]: j["command"]})

        # generate the ratelimit for all interactions
        self.list.append(
            {
                "command": "interactions",
                "ratelimit": self.command_info["interactions"]["ratelimit"],
            }
        )

        # generate all other rate limits
        self.ratelimits = RateLimiter(self.list)
