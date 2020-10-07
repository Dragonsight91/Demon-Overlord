import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse
from DemonOverlord.core.modules.help import gen_help


async def handler(command) -> discord.Embed:

    # if there are no parameters, show the help page on this command
    if not command.params:
        return await gen_help(command)

    # this is the list of chats, only renamed for convenience
    chat_list = command.bot.commands.chats

    # this generates a proper chat name from the command
    chat = "_".join(command.params).lower()

    # if we have it, we respond accordingly, otherwise it's a BadCommand
    if chat in chat_list:
        return ChatDescription(command, chat_list[chat])
    else:
        return BadCommandResponse(command)


class ChatDescription(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles deconstructing the chat data into a discord embed
    """

    def __init__(self, command, chat_desc: dict):

        # initialize the super class so we get all the things set
        super().__init__(
            f'Information about Category - {" ".join(command.params).upper()}',
            color=0x5D0CB8,
            icon=command.bot.config.izzymojis["izzyyay"],
        )

        # basic setup, since this message vanishes
        self.timeout = 60
        self.description = f'This is a list of currently available chats in the category `{" ".join(command.params).upper()}`.'

        # this adds all the embed fields and modifies the descriptions based on the type of channel it is
        for chat in chat_desc:

            self.add_field(
                name=(
                    f"__{chat['name'].upper()}__ - Voice Chat"
                    if chat["type"] == "voice"
                    else f"__{chat['name'].upper()}__ - Text Channel"
                ),
                value=(
                    chat["description"]
                    if chat["type"] == "voice" or chat["type"] == "hidden"
                    else f"<#{chat['id']}> - {chat['description']}"
                ),
                inline=False,
            )
