import discord


from DemonOverlord.core.util.responses import ImageResponse, BadCommandResponse


async def handler(command) -> discord.Embed:
    # create shortcuts to make life easier
    alone_interactions = command.bot.commands.interactions["alone"]
    social_interactions = command.bot.commands.interactions["social"]
    combine_interactions = command.bot.commands.interactions["combine"]

    # what interaction do we have?
    if command.action in alone_interactions.keys():
        url = await command.bot.api.tenor.get_interact(f'anime {alone_interactions[command.action]["query"]}')
        interact = AloneInteractions(
            command.bot, alone_interactions[command.action], command.invoked_by, url=url)
    else:
        # filter mentions from params. double mentions are ignored
        if command.params != None and len(command.mentions) > 0:
            command.params = command.params[len(command.mentions):]
            mentions = [i.display_name for i in command.mentions]
        elif command.params != None and command.params[0] == "everyone":
            command.params = command.params[1:]  # filter everyone
            mentions = ["everyone"]
        else:
            mentions = []

        # what other type of interaction is this?
        if command.action in social_interactions.keys():
            # no mentions. not good
            if len(mentions) < 1:
                return BadCommandResponse(command)

            url = await command.bot.api.tenor.get_interact(f'anime {social_interactions[command.action]["query"]}')
            interact = SocialInteraction(
                command.bot, social_interactions[command.action], command.invoked_by, mentions, url)

        elif command.action in combine_interactions.keys():
            url = await command.bot.api.tenor.get_interact(f'anime {combine_interactions[command.action]["query"]}')
            if combine_interactions[command.action]["type"] == "music":
                interact = MusicInteraction(
                    command.bot, combine_interactions[command.action], command.invoked_by, mentions, url)
            elif combine_interactions[command.action]["type"] == "game":
                interact = GameInteraction(
                    command.bot, combine_interactions[command.action], command.invoked_by, mentions, url)
            else:
                interact = CombineInteraction(
                    command.bot, combine_interactions[command.action], command.invoked_by, mentions, url)
        else:
            return BadCommandResponse(command)

    if command.params != None and len(command.params) > 0:
        interact.add_message(" ".join(command.params))

    return interact
# base interaction


class Interaction(ImageResponse):
    def __init__(self, bot: discord.Client, interaction_type: dict, user: discord.Member, url: str, title: str = "Interaction", color: int = 0xffffff):
        super().__init__(title, url=url,
                         color=color, icon=bot.config.izzymojis[interaction_type["emoji"]])
        self.interaction_type = type
        self.user = user

    def add_message(self, msg: str) -> None:
        self.add_field(name="Message:", value=msg)


# social Interaction
class SocialInteraction(Interaction):
    def __init__(self, bot: discord.Client, interaction_type: dict, user: discord.Member, mentions: list, url: str):
        super().__init__(bot, interaction_type, user, url, color=0xa251af)
        if len(mentions) > 1:
            self.interact_with = f'{", ".join(mentions[:-1])} and {mentions[-1]}'
        else:
            self.interact_with = f'{mentions[0]}'
        self.title = f'{bot.config.izzymojis[interaction_type["emoji"]]} {user.display_name} {interaction_type["action"]} {self.interact_with}'


class CombineInteraction(Interaction):
    def __init__(self, bot, interaction_type: dict, user: discord.Member, mentions: list, url: str, color: int = 0xa251af):
        super().__init__(bot, interaction_type, user, url, color=color)
        if len(mentions) > 1:
            self.interact_with = f'{", ".join(mentions[:-1])} and {mentions[-1]}'
            self.title = f'{user.display_name} {interaction_type["action"]["social"]} {self.interact_with}'

        elif len(mentions) == 1:
            self.interact_with = f'{mentions[0]}'
            self.title = f'{user.display_name} {interaction_type["action"]["social"]} {self.interact_with}'
        else:
            self.title = f'{bot.config.izzymojis[interaction_type["emoji"]]} {user.display_name} {interaction_type["action"]["alone"]}'


# music interaction, a special case that has both Alone and Social aspects
class MusicInteraction(CombineInteraction):
    def __init__(self, bot: discord.Client, interaction_type: dict, user: discord.Member, mentions: list, url: str):
        super().__init__(bot, interaction_type, user, mentions, url, color=0x1db954)

        spotify = list(filter(lambda x: isinstance(
            x, discord.Spotify), user.activities))
        self.spotify = spotify[0] if len(spotify) > 0 else None

        if self.spotify != None:
            self.description = f'{user.display_name} seems to be listening to music. Click on the title to open it in Spotify.'
            self.insert_field_at(0, name=self.spotify.artist,
                                 value=f'__**Song:** __{self.spotify.title}\n__**Album:** __{self.spotify.album}__', inline=False)
            self.url = f'https://open.spotify.com/track/{self.spotify.track_id}'


class GameInteraction(CombineInteraction):
    def __init__(self, bot: discord.Client, interaction_type: dict, user: discord.Member, mentions: list, url: str):
        super().__init__(bot, interaction_type, user, mentions, url, color=0x1db954)

        game = list(filter(lambda x: isinstance(
            x, (discord.Game, discord.Streaming)), user.activities))
        print(user.activities)
        self.game = game[0] if len(game) > 0 else None

        if self.game != None:
            # is playing a
            if isinstance(self.game, discord.Game):
                self.insert_field_at(0, name="Game:",
                                     value=self.game.name, inline=False)
            else:
                self.insert_field_at(0, name= f'Streaming on {self.game.platform}', value=f'**__Game:__** {self.game.game}')
                self.url = self.game.url

# alone interaction, stuff you do yourself


class AloneInteractions(Interaction):
    def __init__(self, bot: discord.Client, interaction_type: dict, user: discord.Member, url: str):
        super().__init__(bot, interaction_type, user, url, color=0xe2268f,
                         title=f'{user.display_name} {interaction_type["action"]}.')
