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

    def __init__(self, title: str, url: str, color: int = 0xFFFFFF, icon: str = ""):
        super().__init__(title=f"{icon} {title}".lstrip(" "), color=color)
        self.set_image(url=url)


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
        self.timeout = 10

        self.add_field(name="Full Command:", value=command.full, inline=False)
        self.add_field(name="Message:", value=f"```\n{tb}\n```", inline=False)


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


class MissingPermissionResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class is used when the client user has a missing permission
    """
    def __init__(self, command, tb):
        super().__init__(
            f"ERROR - MISSING PERMISSION", color=0xFF0000, icon="🚫"
        )

        # use regex to find function which raise discord.Forbidden
        to_find = re.compile(r", line \d+, in \w+")
        found_files = to_find.findall(tb)
        critical_file = found_files[-2] if len(found_files) > 1 else "MISSING FUNCTION"
        forbidden_function = critical_file[critical_file.rindex(" ")+1:]

        self.timeout = 20
        self.add_field(name="Full Command:", value=command.full, inline=False)
        self.add_field(
            name="Message",
            value=f"""Sorry, but the bot is not allowed to use `{forbidden_function}`
            This error only occurs, when there is a missing permission.
            Please fix the permissions and add the needed permission to the bot role, before trying again.""",
        )
