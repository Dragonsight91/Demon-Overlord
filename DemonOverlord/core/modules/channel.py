import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse


async def handler(command) -> discord.Embed:
    print("1")
    if len(command.channels) > 0:
        print("2")
        if isinstance(command.channels[0], discord.TextChannel):
            print("3")
            return ChatResponse(command.channels[0])
        else:
            print("4")
            return BadCommandResponse(command)
    else:
        print("5")
        return BadCommandResponse(command)


class ChatResponse(TextResponse):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(f"Category - {channel.category.name}", color=0x38ECF2, icon="💬")
        self.description = f"**{channel.mention}**\n{channel.topic}"
        self.timeout = 30