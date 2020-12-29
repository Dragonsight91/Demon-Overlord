import discord

from DemonOverlord.core.util.responses import WelcomeResponse

async def handler(command):
    if command.action == "show":
        welcome = await command.bot.database.get_welcome(command.invoked_by.guild.id)
        return WelcomeResponse(welcome, command.bot, command.invoked_by)