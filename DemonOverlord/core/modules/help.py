import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse


async def handler(command) -> discord.Embed:

    # get the command help entry
    command_help = list(
        filter(lambda x: x["command"] == command.action, command.bot.commands.list)
    )

    # if the action is none, we can ignore
    if command.action is None or command.action == "help":
        return HelpMain(command, command.bot.commands.command_info["help"])

    # if we try to access a category, that has to be handled differently
    elif command.action in command.bot.commands.command_info:

        # Some categories are generated. In this case, it is Interactions, which have a custom layout
        if (
            len(command.bot.commands.command_info[command.action]["commands"]) == 0
            and command.action == "interactions"
        ):
            return HelpInteractionsCategory(
                command,
                command.bot.commands.command_info[command.action],
                command.bot.commands.interactions,
            )

        # this is a plain command category
        else:
            return HelpCommandCategory(
                command, command.bot.commands.command_info[command.action]
            )

    # this is the case, if we have a specific command
    elif len(command_help) > 0:
        return HelpCommand(command, command_help[0])

    # and this is the default case, in which we return an error
    else:
        return BadCommandResponse(command)


async def gen_help(command):
    """
    This Function is meant to help generate a help embed, when not calling help.
    One example is the default action of showing a command's help entry
    when not specifying an action.
    """
    command.action = command.command
    command_help = list(
        filter(lambda x: x["command"] == command.command, command.bot.commands.list)
    )
    return HelpCommand(command, command_help[0])


# each normal command only gets this.
class HelpCommandCategory(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This is a basic class that handles taking apart the categories from cmd_info.json and making it into a proper discord embed
    """

    def __init__(self, command, help_dict: dict):

        # initialize the super class
        super().__init__(
            f"Help - {command.action}",
            color=0x2CD5C9,
            icon=command.bot.config.izzymojis["what"] or "❓",
        )

        # set all properties
        self.help = help_dict
        self.timeout = self.help["timeout"]
        self.syntax = (
            f'`{command.bot.config.mode["prefix"]} {self.help["command_syntax"]}`'
        )
        self.description = self.help["description"]
        self.actions = None

        # parse the action list
        self.actions = ""
        for i in self.help["commands"]:
            self.actions += f'{i["command"]}\n'

        # add the fields to the embed
        self.add_field(name="Command usage:", value=f"`{self.syntax}`", inline=False)
        self.add_field(
            name="Available Commands:",
            value=f"```asciidoc\n{self.actions}\n```",
            inline=False,
        )


class HelpMain(HelpCommandCategory):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This is the main page, which shows available commands and command categories.
    """

    def __init__(self, command, help_dict: dict):
        # initialize the super class
        command.action = "Main"
        super().__init__(command, help_dict)

        # give out the full bot syntax
        self.main_syntax = f'`{command.bot.config.mode["prefix"]} {{command}} {{action}} {{parameters}}`'

        # add the category string
        self.categories = ""
        for i in self.help["categories"]:
            self.categories += f'{i["command"]}\n'

        # add all the necessary fields
        self.insert_field_at(
            1, name="General Command Syntax:", value=self.main_syntax, inline=False
        )
        self.add_field(
            name="Available Categories:",
            value=f"```asciidoc\n{self.categories}\n```",
            inline=False,
        )


class HelpCommand(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles beautifying the datastructure of a command from cmd_info.json and making it into a proper embed
    """

    def __init__(self, command, help_dict: dict):

        # initialize the super class
        super().__init__(
            f"Help - {command.action}",
            color=0x2CD5C9,
            icon=command.bot.config.izzymojis["what"] or "❓",
        )

        # set all properties
        self.help = help_dict
        self.description = self.help["description"]
        self.syntax = f'{command.bot.config.mode["prefix"]} {self.help["syntax"]}'
        self.ratelimit = f'This command is currently limited to one execution every `{self.help["ratelimit"]["limit"]} seconds`'
        self.timeout = 60

        # parse the actions list or set None if there are no specific actions
        if self.help["actions"] != None:
            actionlist = ""
            for i in self.help["actions"]:
                if i["params"] != None:
                    paramlist = ""
                    for j in i["params"]:
                        paramlist += f'  {j["name"]} - {j["description"]}\n'
                else:
                    paramlist = None

                actionlist += f'Action      :: {i["action"]}\n'
                actionlist += f'Description :: {i["description"]}\n'
                actionlist += f'Usage       :: {command.bot.config.mode["prefix"]} {command.action} {i["usage"]}\n'
                actionlist += f"Parameters  :: \n  {paramlist}\n" if paramlist else ""
                actionlist += "\n"
        else:
            actionlist = None

        # set the parsed list string into a code block (for syntax highlighting)
        self.actions = f"```asciidoc\n{actionlist}\n```"

        # add all necessary fields
        self.add_field(name="Syntax:", value=self.syntax, inline=False)
        if self.help["ratelimit"]["limit"] > 0:
            self.add_field(name="Ratelimit:", value=self.ratelimit, inline=False)
        self.add_field(name="Actions:", value=self.actions)


class HelpInteractionsCategory(HelpCommandCategory):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This is a more customized class to show the three different columns of Interactions
    """

    def __init__(self, command, help_dict: dict, interact_dict: dict):

        # initialize the super class
        super().__init__(command, help_dict)

        # set all properties and overwrite some things the super class did
        self.interact = interact_dict
        self.syntax = self.help["command_syntax"].replace(
            "%prefix%", command.bot.config.mode["prefix"]
        )
        self.remove_field(1)

        # set the command syntax
        self.set_field_at(
            0, name="Command usage:", value=f"{self.syntax}", inline=False
        )

        # add the action list
        for i in self.interact.keys():
            actions = "\n".join(self.interact[i].keys())
            self.add_field(
                name=f"{i.upper()} INTERACTIONS", value=f"```diff\n{actions}\n```"
            )
