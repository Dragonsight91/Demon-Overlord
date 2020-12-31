import discord
import re


class TextResponse(discord.Embed):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class gives a base for all Text responses used by the bot
    """

    def __init__(
        self, title: str, color: int = 0xFFFFFF, icon: str = "", msg: dict = None
    ):
        super().__init__(title=f"{icon} {title}", color=color)
        self.timeout = 0

        if msg != None:
            self.add_field(name=msg["name"], value=msg["value"], inline=False)


class ImageResponse(discord.Embed):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class gives a base for all Image type responses used by the bot
    """

    def __init__(self, title: str, url: str, *, color: int = 0xFFFFFF, icon: str = ""):
        super().__init__(title=f"{icon} {title}".lstrip(" "), color=color)
        self.set_image(url=url)


class WelcomeResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class represents a Welcome Message
    """

    def __init__(self, welcome, bot: discord.Client, member: discord.Member):
        # properties
        self.channel = member.guild.get_channel(welcome["welcome_channel"])

        # other variables
        regex = re.compile(
            r"{(?P<ctrl_char>[#@!]?)(?P<ctrl_seq>[\w\s]*)\.?(?P<ctrl_arg>\w*)}"
        )
        guild = member.guild

        self.welcome = welcome

        for key in self.welcome:
            if not key in ("embed_color", "guild_id", "welcome_channel", "wait_pending") and not self.welcome[key] in (None, ""):
                for match in regex.finditer(self.welcome[key]):
                    group = match.groupdict()
                    var = None  # must always be string or None

                    if group["ctrl_char"] == "@":
                        user_name = group["ctrl_seq"]
                        user = guild.get_member_named(user_name)

                        if group["ctrl_arg"] == "name":
                            var = user.display_name
                        elif group["ctrl_arg"] == "id":
                            var = user.id
                        elif group["ctrl_arg"] == "icon":
                            var = user.avatar_url
                        elif group["ctrl_arg"] == "mention":
                            var = user.mention
                        else:
                            var = user.display_name
                            

                    elif group["ctrl_char"] == "#":
                        channel_name = group["ctrl_seq"]
                        channel = discord.utils.get(guild.channels, name=channel_name)

                    elif group["ctrl_char"] == "!":
                        role_name = group["ctrl_seq"]
                        role = discord.utils.get(guild.roles, name=role_name)
                    else:
                        if group["ctrl_seq"] == "server":
                            if group["ctrl_arg"] == "name":
                                var = guild.name
                            elif group["ctrl_arg"] == "id":
                                var = guild.id
                            elif group["ctrl_arg"] == "icon":
                                var = guild.icon_url
                            else:
                                var = guild.name
                        elif group["ctrl_seq"] == "user":
                            if group["ctrl_arg"] == "name":
                                var = member.display_name
                            elif group["ctrl_arg"] == "id":
                                var = member.id
                            elif group["ctrl_arg"] == "icon":
                                var = member.avatar_url
                            elif group["ctrl_arg"] == "mention":
                                var = member.mention
                            else:
                                var = member.display_name

                    if not var == None:
                        self.welcome[key] = (
                            re.sub(regex.pattern, str(var), self.welcome[key], count=1)
                            if not var == None
                            else self.welcome[key]
                        )
                        
        super().__init__(self.welcome["embed_title"], color=self.welcome["embed_color"])

        if (
            not self.welcome["embed_image"] == None
            and not self.welcome["embed_image"] == ""
        ):
            self.set_image(url=self.welcome["embed_image"])

        if (
            not self.welcome["embed_thumbnail"] == None
            and not self.welcome["embed_thumbnail"] == ""
        ):
            self.set_thumbnail(url=self.welcome["embed_thumbnail"])

        if (
            not self.welcome["embed_author"] == None
            and not self.welcome["embed_author"] == ""
        ):
            self.set_author(name=self.welcome["embed_author"], 
            icon_url=(
                self.welcome["embed_author_img"] 
                if not self.welcome["embed_author_img"] == None and not self.welcome["embed_author_img"] == "" 
                else None
            ))

        if (
            not self.welcome["embed_description"] == None
            and not self.welcome["embed_description"] == ""
        ):
            self.description = self.welcome["embed_description"]


class RateLimitResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class is used when the rate limiter prevented the command from execution
    """

    def __init__(self, command, time_remain):
        super().__init__(
            f"RATELIMIT ERROR FOR: {command.command} [{time_remain} seconds]",
            color=0xFF0000,
            icon="⛔",
        )

        self.timeout = 10

        # add necessary fields
        self.add_field(name="Full Command:", value=command.full, inline=False)
        self.add_field(
            name="Message",
            value="Sorry, but this command is rate limited. Please be patient and don't spam the command.",
        )


class ErrorResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class is used when a python error occurred in the bot.
    """

    def __init__(self, command, tb):
        super().__init__(
            f"ERROR WHEN EXECUTING COMMAND: {command.command} ",
            color=0xFF0000,
            icon="🚫",
        )
        self.timeout = 60
        self.description = "An internal error occured. This message will remove itself after 60 seconds to not clutter the chat, please make a screenshot and send it in a bug report on github."
        self.url = "https://github.com/Dragonsight91/Demon-Overlord/issues"
        self.set_author(
            name="DemonOverlord",
            icon_url="https://cdn.discordapp.com/avatars/684101090429632534/f3982bfaaa59c042aa0895d7ca7c7a36.png",
        )
        self.add_field(name="Full Command:", value=command.full, inline=False)
        self.add_field(name="Message:", value=f"```\n{tb}\n```", inline=False)

class ConfirmedResponse(TextResponse):
    def __init__(self, msg, ctrl_seq):
        super().__init__(title=f"{msg} was {ctrl_seq} on this server", color=0x1ceb1c)

class AbortedResponse(TextResponse):
    def __init__(self, message, reason):
        super().__init__(
            f"{message} was aborted because {reason}", color=0xFF0000, icon="🚫"
        )
class BadCommandResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class is used if the user enters a wrong or faulty command
    """

    def __init__(self, command):
        super().__init__(
            f"ERROR - COMAND OR ACTION NOT FOUND", color=0xFF0000, icon="🚫"
        )
        self.timeout = 10
        self.add_field(name="Full Command:", value=command.full, inline=False)
        self.add_field(
            name="Message:",
            value=f"""Sorry, but this doesn\'t seem to be a valid command.
            Please use `{command.prefix} help` to find out about the available commands.""",
        )
