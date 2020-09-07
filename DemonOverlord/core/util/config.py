import discord
import os
import sys
import json

from DemonOverlord.core.util.api import TenorAPI, InspirobotAPI
from DemonOverlord.core.util.limit import RateLimiter


class BotConfig(object):
    def __init__(self, bot: discord.Client, confdir: str, argv: list):
        # set all vars None first, this also gives us a list of all currently available vars
        self.raw = None
        self.mode = None
        self.izzymojis = dict()
        self.token = None
        self.env = None
        self.emoji = None

        # set all vars to their final value.

        # get the raw config.json
        with open(os.path.join(confdir, "config.json")) as f:
            self.raw = json.load(f)

        # create config from cli stuff
        for arg in argv:
            # set bot mode
            if arg in self.raw["cli_options"]["bot_modes"]:
                self.mode = self.raw["cli_options"]["bot_modes"][argv[1]]
            else:
                self.raw["cli_options"]["bot_modes"]["--prod"]
        print(self.mode)
        # set the token
        self.token = os.environ.get(self.mode["tokenvar"])
        self.env = self.raw["env_vars"]
        self.emoji = self.raw["emoji"]

    def post_connect(self, bot: discord.Client):
        # generate izzymoji list
        for key in self.raw["izzymojis"].keys():
            self.izzymojis[key] = bot.get_emoji(self.raw["izzymojis"][key])


class APIConfig(object):
    def __init__(self, config: BotConfig):
        # var init
        self.tenor = None
        self.inspirobot = InspirobotAPI()

        print(config.env)
        tenor_key = os.environ.get(config.env["api"]["tenor"][0])
        if tenor_key:
            self.tenor = TenorAPI(tenor_key)


class DatabaseConfig(object):
    def __init__(self):
        pass


class CommandConfig(object):
    def __init__(self, confdir: str):
        self.interactions = None
        self.relations = None
        self.command_info = None
        self.list = []
        self.ratelimits = None
        self.izzylinks = None
        self.chats = None

        with open(os.path.join(confdir, "special/interactions.json")) as f:
            self.interactions = json.load(f)

        with open(os.path.join(confdir, "cmd_info.json")) as f:
            self.command_info = json.load(f)

        with open(os.path.join(confdir, "../data/commands/izzylinks.json")) as f:
            self.izzylinks = json.load(f)

        with open(os.path.join(confdir, "../data/commands/chats.json")) as f:
            self.chats = json.load(f)

        for i in self.command_info.keys():
            for j in self.command_info[i]["commands"]:
                self.list.append(j)
        self.list.append(
            {
                "command": "interactions",
                "ratelimit": self.command_info["interactions"]["ratelimit"],
            }
        )

        self.ratelimits = RateLimiter(self.list)


class RelationshipConfig(object):
    def __init__(self, db_config: DatabaseConfig):
        pass
