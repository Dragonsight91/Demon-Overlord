import discord
from random import randint
from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse


async def handler(command) -> discord.Embed:
    if command.action == "d6" or command.action == "d8" or command.action == "d10" or command.action == "d12" or command.action == "d20":
        return DiceResponse(command)
    else:
        BadCommandResponse(command)

def get_dice(bot, die: str) -> str:
    die = die[1:]
    out = list()
    for i in die:
        out.append(bot.config.emoji["numbers"][int(i)])
    return "".join(out)


class DiceResponse(TextResponse):
    def __init__(self, command):
        title = f"{get_dice(command.bot, command.action)} Dice - {command.action.upper()}"
        super().__init__(
            title,
            color=0x2CD5C9,
            icon=command.bot.config.izzymojis["what"] or "❓",
        )
        result = get_dice(command.bot, f"d{randint(1, int(command.action[1:]))}")
        self.description = f"The result is: {result}"
