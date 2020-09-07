import discord

from DemonOverlord.core.util.responses import TextResponse, BadCommandResponse


async def handler(command) -> discord.Embed:
    command_help = list(
        filter(lambda x: x["command"] == command.action, command.bot.commands.list)
    )

    if command.action is None or command.action == "help":
        return HelpMain(command, command.bot.commands.command_info["help"])
    elif command.action in command.bot.commands.command_info:
        if len(command.bot.commands.command_info[command.action]["commands"]) == 0:
            if command.action == "interactions":
                return HelpInteractionsCategory(
                    command,
                    command.bot.commands.command_info[command.action],
                    command.bot.commands.interactions,
                )
        else:
            return HelpCommandCategory(
                command, command.bot.commands.command_info[command.action]
            )
    elif len(command_help) > 0:
        return HelpCommand(command, command_help[0])
    else:
        return BadCommandResponse(command)


async def gen_help(command):
    command.action = command.command
    command_help = list(
        filter(lambda x: x["command"] == command.command, command.bot.commands.list)
    )
    return HelpCommand(command, command_help[0])


# each normal command only gets this.
class HelpCommandCategory(TextResponse):
    def __init__(self, command, help_dict: dict):
        super().__init__(
            f"Help - {command.action}",
            color=0x2CD5C9,
            icon=command.bot.config.izzymojis["what"] or "❓",
        )
        self.help = help_dict
        self.timeout = self.help["timeout"]
        self.syntax = (
            f'`{command.bot.config.mode["prefix"]} {self.help["command_syntax"]}`'
        )
        self.description = self.help["description"]
        self.actions = None

        # add the action list
        self.actions = ""
        for i in self.help["commands"]:
            self.actions += f'{i["command"]}\n'

        self.add_field(name="Command usage:", value=f"`{self.syntax}`", inline=False)
        self.add_field(
            name="Available Commands:",
            value=f"```asciidoc\n{self.actions}\n```",
            inline=False,
        )


class HelpMain(HelpCommandCategory):
    def __init__(self, command, help_dict: dict):
        command.action = "Main"
        super().__init__(command, help_dict)
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


# commands are special help pages. they focus on nothing but that command
class HelpCommand(TextResponse):
    def __init__(self, command, help_dict: dict):
        super().__init__(
            f"Help - {command.action}",
            color=0x2CD5C9,
            icon=command.bot.config.izzymojis["what"] or "❓",
        )
        self.help = help_dict
        self.description = self.help["description"]
        self.syntax = f'{command.bot.config.mode["prefix"]} {self.help["syntax"]}'
        self.ratelimit = f'This command is currently limited to one execution every `{self.help["ratelimit"]["limit"]} seconds`'
        self.timeout = 60

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
                actionlist += f"Parameters  :: \n  {paramlist}\n"
                actionlist += "\n"
        else:
            actionlist = None

        self.actions = f"```asciidoc\n{actionlist}\n```"

        # add all necessary fields
        self.add_field(name="Syntax:", value=self.syntax, inline=False)
        if self.help["ratelimit"]["limit"] > 0:
            self.add_field(name="Ratelimit:", value=self.ratelimit, inline=False)
        self.add_field(name="Actions:", value=self.actions)


class HelpInteractionsCategory(HelpCommandCategory):
    def __init__(self, command, help_dict: dict, interact_dict: dict):
        super().__init__(command, help_dict)
        self.interact = interact_dict
        self.syntax = self.help["command_syntax"].replace(
            "%prefix%", command.bot.config.mode["prefix"]
        )
        self.remove_field(1)

        self.set_field_at(
            0, name="Command usage:", value=f"{self.syntax}", inline=False
        )

        # add the action list
        for i in self.interact.keys():
            actions = "\n".join(self.interact[i].keys())
            self.add_field(
                name=f"{i.upper()} INTERACTIONS", value=f"```diff\n{actions}\n```"
            )
