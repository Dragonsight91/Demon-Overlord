from time import time

from DemonOverlord.core.util.responses import TextResponse


class GameResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class gives a base for Discord game responses.
    """

    def __init__(
        self, game_title: str, description: str, game_field: str, timestamp: int = 0
    ):
        super().__init__(game_title, color=0x000000, icon="🕹️")
        self.description = description

        self.add_field(name="Game", value=game_field)

        if timestamp != 0:
            self.insert_field_at(
                0,
                name="Time:",
                value=f'`{str((int(time())-timestamp)//60).rjust(2)}:{str((int(time())-timestamp)%60).rjust(2, "0")}`',
                inline=False,
            )


class GameWonResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class gives a base for Discord game responses if the game was lost.
    """

    def __init__(
        self, game_title: str, win_message: str, game_field, timestamp: int = 0
    ):
        super().__init__(f"YOU WON - {game_title}", color=0xFFD700, icon="🥇")
        self.description = win_message

        self.add_field(name="Game:", value=game_field)

        if timestamp != 0:
            self.insert_field_at(
                0,
                name="Time:",
                value=f'`{str((int(time())-timestamp)//60).rjust(2)}:{str((int(time())-timestamp)%60).rjust(2, "0")}`',
                inline=False,
            )


class GameLostResponse(TextResponse):
    """
    This Represents a Discord Embed and any properties of that embed are active and usable by this class.
    This class gives a base for Discord game responses if the game was lost.
    """

    def __init__(self, game_title: str, win_message: str, game_field):
        super().__init__(f"GAME OVER - {game_title}", color=0x646464, icon="☠️")
        self.description = win_message

        self.add_field(name="Game:", value=game_field)
