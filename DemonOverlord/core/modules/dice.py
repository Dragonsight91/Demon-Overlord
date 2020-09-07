import discord
from random import randint
from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse


async def handler(command) -> discord.Embed:

    # test if we have one of the defined dice classes
    if (
        command.action == "d6"
        or command.action == "d8"
        or command.action == "d10"
        or command.action == "d12"
        or command.action == "d20"
    ):
        return DiceResponse(command)
    
    else:
        BadCommandResponse(command)


class DiceResponse(TextResponse):
    def __init__(self, command):
        # get the number emoji sequence 
        def get_roll(bot, die: str) -> str:
            out = list()
            for i in die:
                out.append(bot.config.emoji["numbers"][int(i)])
            return "".join(out)


        title = f"Dice - {command.action.upper()}"
        super().__init__(
            title,
            color=0x2CD5C9,
            icon=":game_die:",
        )
        self.description = get_roll(
            command.bot, str(randint(1, int(command.action[1:])))
        )
