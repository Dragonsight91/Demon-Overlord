import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse
import re

# Syntax: -mao vote create -title="Test" -options="a,b,c,d" -time=10 -desc="12345"
#
#
#
#
#
async def handler(command) -> discord.Embed:
    if command.action == "create":
        vote_str = " ".join(command.params)
        vote = compile(vote_str)


async def handle_vote(msg_id:int) -> None:
    pass 

async def compile(string : str) -> dict:

    pattern = re.compile("\B-(title|desc|options|time)=(\".*?\")")
    out = dict()

    for group in pattern.findall(string):
        if group[0] != "options":
            out.update({group[0] : group[1][1:-1]})
        else:
            out.update({group[0] : group[1][1:-1].split(",")})

    return out


class VoteMessage(TextResponse):
    def __init__(self, command, vote: dict):
        super().__init__(f'Vote - {vote["name"]}', color=0x2250af,
                         icon=command.bot.config.izzymojis["izzyyay"])
        self.name = vote["name"]
        self.description = vote["description"] if "description" in vote else None
        self.options = vote["options"]


class VoteResult(TextResponse):
    pass
