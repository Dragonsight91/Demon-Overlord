import discord

# core imports
from DemonOverlord.core.util.responses import ImageResponse, BadCommandResponse
from DemonOverlord.core.util.logger import LogCommand, LogMessage, LogHeader


async def handler(command) -> discord.Embed:
    # create shortcuts to make life easier
    alone_interactions = command.bot.commands.interactions["alone"]
    social_interactions = command.bot.commands.interactions["social"]
    combine_interactions = command.bot.commands.interactions["combine"]

    # what interaction do we have?
    if command.action in alone_interactions:
        # get the url from tenor
        url = await command.bot.api.tenor.get_interact(
            f'anime {alone_interactions[command.action]["query"]}'
        )

        # actually create the interaction
        interact = Interaction(
            command.bot,
            alone_interactions[command.action],
            command.invoked_by,
            url,
            color=0xE2268F,
            title=f'{command.invoked_by.display_name} {alone_interactions[command.action]["action"]}.',
        )
    else:
        # filter mentions from params. double mentions are ignored
        # this is the case where we don't mention everyone
        if (
            command.params != None
            and len(command.mentions) > 0
            and command.params[0] != "everyone"
        ):
            command.params = command.params[len(command.mentions) :]
            mentions = [i.display_name for i in command.mentions]

        # this is the previous case, but we DO mention everyone
        elif (
            command.params != None
            and len(command.mentions) > 0
            and command.params[0] == "everyone"
        ):
            command.params = command.params[len(command.mentions) + 1 :]
            mentions = ["everyone"] + [i.display_name for i in command.mentions]

        # we only mention everyone
        elif command.params != None and command.params[0] == "everyone":
            command.params = command.params[1:]  # filter everyone
            mentions = ["everyone"]

        # we mention nobody (used for combine interactions)
        else:
            mentions = []

        # what other type of interaction is this?, just check and try to match
        if command.action in social_interactions:
            # no mentions. not good
            if len(mentions) < 1:
                return BadCommandResponse(command)

            url = await command.bot.api.tenor.get_interact(
                f'anime {social_interactions[command.action]["query"]}'
            )
            interact = SocialInteraction(
                command.bot,
                social_interactions[command.action],
                command.invoked_by,
                mentions,
                url,
            )

        # these are combine interactions, interactions that are capable of alone AND social interaction behavior
        elif command.action in combine_interactions:
            url = await command.bot.api.tenor.get_interact(
                f'anime {combine_interactions[command.action]["query"]}'
            )
            if combine_interactions[command.action]["type"] == "music":
                interact = MusicInteraction(
                    command.bot,
                    combine_interactions[command.action],
                    command.invoked_by,
                    mentions,
                    url,
                )
            elif combine_interactions[command.action]["type"] == "game":
                interact = GameInteraction(
                    command.bot,
                    combine_interactions[command.action],
                    command.invoked_by,
                    mentions,
                    url,
                )
            else:
                interact = CombineInteraction(
                    command.bot,
                    combine_interactions[command.action],
                    command.invoked_by,
                    mentions,
                    url,
                )
        # this is the default error
        else:
            return BadCommandResponse(command)

    # add the user's message to the interaction.
    if command.params != None and len(command.params) > 0:
        interact.add_message(" ".join(command.params))

    return interact


# base interaction
class Interaction(ImageResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This is the Base class for all interactions. Every interaction inherits properties from here.
    This also serves as the most basic of all interactions.
    """

    def __init__(
        self,
        bot: discord.Client,
        interaction_type: dict,
        user: discord.Member,
        url: str,
        title: str = "Interaction",
        color: int = 0xFFFFFF,
    ):

        super().__init__(
            title,
            url=url,
            color=color,
            icon=bot.config.izzymojis[interaction_type["emoji"]],
        )
        self.interaction_type = type
        self.user = user

    def add_message(self, msg: str) -> None:
        self.add_field(name="Message:", value=msg)


class SocialInteraction(Interaction):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles Social Interactions, which are interactions between two or more people.
    """

    def __init__(
        self,
        bot: discord.Client,
        interaction_type: dict,
        user: discord.Member,
        mentions: list,
        url: str,
    ):
        # initialize the super class
        super().__init__(bot, interaction_type, user, url, color=0xA251AF)

        # parse the interaction
        if len(mentions) > 1:
            self.interact_with = f'{", ".join(mentions[:-1])} and {mentions[-1]}'
        else:
            self.interact_with = f"{mentions[0]}"
        self.title = f'{bot.config.izzymojis[interaction_type["emoji"]]} {user.display_name} {interaction_type["action"]} {self.interact_with}'


class CombineInteraction(Interaction):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles Interactions that are a combination of the base interaction class and the SocialInteraction class
    """

    def __init__(
        self,
        bot,
        interaction_type: dict,
        user: discord.Member,
        mentions: list,
        url: str,
        color: int = 0xA251AF,
    ):
        # initialize the super class
        super().__init__(bot, interaction_type, user, url, color=color)

        # parse the mentions, so we can set them properly or act as base interaction
        if len(mentions) > 1:
            self.interact_with = f'{", ".join(mentions[:-1])} and {mentions[-1]}'
            self.title = f'{user.display_name} {interaction_type["action"]["social"]} {self.interact_with}'

        elif len(mentions) == 1:
            self.interact_with = f"{mentions[0]}"
            self.title = f'{user.display_name} {interaction_type["action"]["social"]} {self.interact_with}'
        else:
            self.title = f'{bot.config.izzymojis[interaction_type["emoji"]]} {user.display_name} {interaction_type["action"]["alone"]}'


# music interaction, a special case that has both Alone and Social aspects
class MusicInteraction(CombineInteraction):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles interactions that may display the song currently playing on spotify (if discord can see it)
    """

    def __init__(
        self,
        bot: discord.Client,
        interaction_type: dict,
        user: discord.Member,
        mentions: list,
        url: str,
    ):
        # initialize the super class
        super().__init__(bot, interaction_type, user, mentions, url, color=0x1DB954)
        # get the spotify action
        spotify = list(
            filter(lambda x: isinstance(x, discord.Spotify), user.activities)
        )
        self.spotify = spotify[0] if len(spotify) > 0 else None

        # if the user is listening to something (and discord sees it) then set a text field to reflect that. also ad a url, so the user can open it in spotify.
        if self.spotify:
            self.description = f"{user.display_name} seems to be listening to music. Click on the title to open it in Spotify."
            self.insert_field_at(
                0,
                name=self.spotify.artist,
                value=f"__**Song:**__ {self.spotify.title}\n__**Album:**__ {self.spotify.album}",
                inline=False,
            )
            self.url = f"https://open.spotify.com/track/{self.spotify.track_id}"


class GameInteraction(CombineInteraction):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class handles interactions that can show the game that is being played or the livestream, if the user is streaming (and discord sees it)
    """

    def __init__(
        self,
        bot: discord.Client,
        interaction_type: dict,
        user: discord.Member,
        mentions: list,
        url: str,
    ):

        # initialize the super class
        super().__init__(bot, interaction_type, user, mentions, url, color=0x1DB954)

        # get the list of game actions and then the first match. we don't bother selecting a specific one
        game = list(
            filter(
                lambda x: isinstance(x, (discord.Game, discord.Streaming))
                or x.type
                in (discord.ActivityType.playing, discord.ActivityType.streaming),
                user.activities,
            )
        )
        self.game = game[0] if len(game) > 0 else None

        # The user is playing a game
        if self.game != None:

            # the user is just playing a game
            if (
                isinstance(self.game, discord.Game)
                or self.game.type == discord.ActivityType.playing
            ):
                self.insert_field_at(
                    0, name="Game:", value=self.game.name, inline=False
                )

            # the user is streaming on a streaming platform
            else:
                self.insert_field_at(
                    0,
                    name=f"Streaming on {self.game.platform}",
                    value=f"**__Game:__** {self.game.game}",
                )
                self.url = self.game.url
