import asyncio
import discord
import psycopg2

from DemonOverlord.core.util.responses import (
    BadCommandResponse,
    WelcomeResponse,
    ConfirmedResponse,
    TextResponse,
    AbortedResponse,
)
from DemonOverlord.core.util.logger import LogMessage, LogType, LogFormat


async def handler(command) -> discord.Embed:
    cursor = command.bot.database.connection_main.cursor()
    # does user have permissions? 
    if not command.action == "show" and (not command.invoked_by.guild_permissions.administrator or not command.invoked_by.guild_permissions.manage_guild):
        res = AbortedResponse(
            "Enabling the Welcome Message", "User has no permission to enable this feature"
        )
        res.description = f"Please make sure the you or your role has either `Administrator` or `Manage Server` permission."
        return res

    if command.action == "show":
        welcome = await command.bot.database.get_welcome(command.invoked_by.guild.id)
        res = WelcomeResponse(welcome, command.bot, command.invoked_by)

    elif command.action == "enable":
        if len(command.channels) < 1:
            res = AbortedResponse(
                "Enabling the Welcome Message", "Welcome channel was not specified"
            )
            res.description = f"Please mention a channel to use as welcome channel."
            return res
        elif not command.channels[0].permissions_for(command.guild.me).send_messages:
            res = AbortedResponse(
                "Enabling the Welcome Message", "Bot has no permission to send messages to specified channel"
            )
            res.description = f"Please make sure the bot or bot role has `Read Messages` permission in {command.channels[0].mention}"
            return res

        cursor.execute(
            "UPDATE admin.admin_core SET has_welcome='true' WHERE guild_id=%s",
            [command.guild.id],
        )
        try:
            cursor.execute(
                "INSERT INTO admin.welcome_messages (guild_id, welcome_channel) VALUES (%s, %s)",
                [command.guild.id, command.channels[0].id],
            )
        except psycopg2.IntegrityError:
            print(
                LogMessage(
                    f"Entry for guild '{command.guild.name}' already exists, skipping insertion"
                )
            )

        res = ConfirmedResponse("Welcome Message", "enabled")
        res.description = (
            f"The welcome message was enabled in channel {command.channels[0].mention}"
        )

    elif command.action == "disable":

        def check_msg(reaction, user):
            print(reaction)
            return (
                user == command.invoked_by
                and str(reaction.emoji) in command.bot.config.emoji["yes_no"]
            )

        res = None
        cursor.execute(
            "SELECT guild_id FROM admin.welcome_messages WHERE guild_id=%s",
            [command.guild.id],
        )
        result = cursor.fetchone()
        if result == None:
            res = AbortedResponse(
                "Deleting the Welcome Message", "Welcome message is not enabled"
            )
            res.description = f"There was no welcome message to remove, please enable welcome messages before trying to disable them."
            return res

        embed = TextResponse("Confirm this action", 0xFF0000, icon="🚫")
        embed.description = "Are you sure you want to remove the welcome message for this server?"
        embed.description += "\n\n**This action is irreversible and will delete all data for the welcome message.**"
        embed.description += f"\nreact with {command.bot.config.emoji['yes_no'][0]} to agree"
        embed.description += f"\nreact with {command.bot.config.emoji['yes_no'][1]} to disagree"

        message = await command.channel.send(embed=embed)
        await message.add_reaction(command.bot.config.emoji["yes_no"][0])
        await message.add_reaction(command.bot.config.emoji["yes_no"][1])

        try:
            reaction, user = await command.bot.wait_for(
                "reaction_add", timeout=60, check=check_msg
            )
        except asyncio.TimeoutError:
            return AbortedResponse(
                "Deleting the Welcome Message", "The prompt timed out after 60 seconds"
            )

        if str(reaction.emoji) == command.bot.config.emoji["yes_no"][0]:

            cursor.execute(
                "UPDATE admin.admin_core SET has_welcome='false' WHERE guild_id=%s",
                [command.guild.id],
            )
            try:
                cursor.execute(
                    "DELETE FROM admin.welcome_messages WHERE guild_id=%s",
                    [command.guild.id],
                )
                res = ConfirmedResponse("Welcome Message", "disabled")
                res.description = (
                    f"The welcome message was removed and all data was deleted"
                )
            except psycopg2.Error:
                print(
                    LogMessage(
                        f"Entry for guild '{command.guild.name}' doesn't exist exists, skipping deletion"
                    )
                )

        else:
            res = AbortedResponse(
                "Deleting the Welcome Message", "User aborted the process"
            )

    else:
        res = BadCommandResponse(command)
    cursor.close()
    return res
