from random import randint
from time import time
import discord

from DemonOverlord.core.util.game_responses import (
    GameResponse,
    GameLostResponse,
    GameWonResponse,
)
from DemonOverlord.core.util.responses import BadCommandResponse


async def handler(command) -> None:
    # we have to make VERY sure, that the command is correct
    def msg_test(message: discord.Message) -> bool:
        if message.content != "":
            # is it the same person?
            same_author = message.author == command.invoked_by
            if same_author:
                # test if it is a command
                make_command = message.content.split(" ")
                # let's test this against all possible patterns...
                if len(make_command) >= 3:
                    has_prefix = make_command[0] == command.bot.config.mode["prefix"]
                    if has_prefix and make_command[1] == "ms":
                        if make_command[2] == "flag" or make_command[2] == "reveal":
                            if len(make_command) == 5:
                                try:
                                    x = int(make_command[3])
                                    y = int(make_command[4])
                                except:
                                    return False
                                else:
                                    if x >= 1 and y >= 1 and x <= 10 and y <= 10:
                                        return True
                        elif make_command[2] == "quit":
                            return True
            return False

    if command.action == "start":

        # create initial game state
        timestamp = int(time())
        game_won = False
        game_grid = generate_game()
        running = True
        reason = "You hit a mine and lost. Better luck next time"
        description = f'This is minesweeper.\nYou can do the following things:\n__Toggle Flag:__\n  `{command.bot.config.mode["prefix"]} ms flag {{x}} {{y}}`\n\n__Reveal a field:__\n  `{command.bot.config.mode["prefix"]} ms reveal {{x}} {{y}}`\n\n__End Game:__\n `{command.bot.config.mode["prefix"]} ms quit`'
        response = await command.message.channel.send(
            embed=GameResponse(
                "Minesweeeper", description, get_grid(command.bot, game_grid)
            )
        )

        # the main loop of the game.
        while running and not game_won:
            try:
                message = await command.bot.wait_for(
                    "message", check=msg_test, timeout=60
                )
                # we can assume here, that the message has the correct information, based on msg_test
                make_command = message.content.split(" ")
                await message.delete()

                # take the specified action
                if make_command[2] == "flag":
                    running = game_grid[int(make_command[4]) - 1][
                        int(make_command[3]) - 1
                    ].flag()
                elif make_command[2] == "reveal":
                    running = game_grid[int(make_command[4]) - 1][
                        int(make_command[3]) - 1
                    ].uncover()
                elif make_command[2] == "quit":
                    reason = "User ended the game."
                    running = False
                    del message
                    break

                # have we won? update win and show status
                game_won = determine_win(game_grid)
                await response.edit(
                    embed=GameResponse(
                        "Minesweeeper",
                        description,
                        get_grid(command.bot, game_grid),
                        timestamp=timestamp,
                    )
                )
            except Exception:
                running = False
                reason = "The game timed out after 60 seconds, therefore you lost.\nDon't start something you can't end."
        await response.delete()

        # have we won? send appropriate response and delete message
        if game_won:
            return GameWonResponse(
                "Minesweeper",
                "Congratulations, you finished the game without hitting a single bomb.",
                get_grid(command.bot, game_grid),
                timestamp=timestamp,
            )
        else:
            return GameLostResponse(
                "Minesweeper", reason, get_grid(command.bot, game_grid)
            )

    return


def determine_win(game_grid: list) -> bool:
    """
    This function determines if the player won.
    """
    count = 0
    for i in game_grid:
        for j in i:
            temp = (j.flagged and isinstance(j, BombField)) or (
                j.uncovered and not isinstance(j, BombField)
            )
            if temp:
                count += 1

    return count == len(game_grid) * len(game_grid[0])


def get_grid(bot: discord.Client, game_grid: list) -> str:
    """
    This function generates the emoji field that is later shown in the Embed
    """
    out = ""
    out += bot.config.emoji["minesweeper"]["N"]
    for i in range(1, len(game_grid) + 1):
        out += bot.config.emoji["numbers"][i]
    out += "\n"

    # go trough the grid and place everything with its relevant emoji
    for i in enumerate(game_grid):
        out += bot.config.emoji["numbers"][i[0] + 1]
        for j in i[1]:
            try:
                out += (
                    bot.config.emoji["numbers"][int(str(j))] if int(str(j)) > 0 else "🟦"
                )
            except Exception:
                out += bot.config.emoji["minesweeper"][str(j)]
        out += "\n"
    return out


def generate_game():
    """
    This function generates the initial game grid
    """
    # the initial list. an empty 10x10 grid.
    game_grid = [[None] * 10 for x in range(0, 10)]

    # generate the mines, then the numbers
    game_grid = generate_mines(game_grid)
    game_grid = generate_numbers(game_grid)
    return game_grid


def generate_mines(game_grid: list) -> list:
    """
    This function generates the mines on the game grid
    """

    # go through the game grid and generate 11 bombs at random positions
    for i in range(0, 11):
        x = randint(0, len(game_grid) - 1)
        y = randint(0, len(game_grid) - 1)
        game_grid[y][x] = BombField()

    return game_grid


def generate_numbers(game_field: list) -> list:
    """
    This function creates the value and zero fields on the game grid
    """

    # this creates an ofset range, so the rest of the code knows where it can or can't check
    def make_range(num: int) -> list:
        if num < 1:
            return range(0, 2)
        elif num > 8:
            return range(-1, 1)
        else:
            return range(-1, 2)

    # then we just go through the 2D array and generate the numbers around the bombs
    for y, row in enumerate(game_field):
        for x, field in enumerate(row):
            temp_value = 0

            # generate -1, 0 and 1
            for i in make_range(y):
                for j in make_range(x):
                    # we don't have to check our own position
                    coord_y = y + (1 * i)
                    coord_x = x + (1 * j)
                    if (
                        isinstance(game_field[coord_y][coord_x], BombField)
                        and (
                            coord_x,
                            coord_y,
                        )
                        != (x, y)
                    ):
                        temp_value += 1

            # if the field isn't a bomb, we can set it
            if field == None:
                if temp_value == 0:
                    game_field[y][x] = ZeroField()
                else:
                    game_field[y][x] = ValueField(temp_value)

    # second pass to add neighbors
    for y, row in enumerate(game_field):
        for x, field in enumerate(row):

            # generate -1, 0 and 1
            for i in make_range(y):
                for j in make_range(x):
                    # we don't have to check our own position
                    coord_y = y + (1 * i)
                    coord_x = x + (1 * j)
                    if (coord_x, coord_y) != (x, y):
                        field.neighbors.append(game_field[coord_y][coord_x])

    return game_field


class ValueField:
    """
    This represents a game field with a numerical value. it also serves as the base for all other classes.
    """

    def __init__(self, value: int):
        self.value = value
        # we only need to add it here, because all other fields inherit this property
        self.neighbors = []
        self.uncovered = False  # False means it's hidden, True means it's not.
        self.flagged = False  # False means it is not flagged True means it is.

    # this flags a field
    def flag(self) -> bool:
        if not self.uncovered:
            self.flagged = not self.flagged
        return True

    # overwrite the __str__ function so we can easily generate the string
    def __str__(self):
        if self.flagged:
            return "F"
        elif self.uncovered:
            return str(self.value) if self.value else "B"

        else:
            return "X"

    # this uncovers a ValueField

    def uncover(self) -> bool:
        # have we been flagged? if no, continue, otherwise do nothing.
        if not self.flagged:
            self.uncovered = True
        return True


class ZeroField(ValueField):
    """
    This represents a Value Fieldd with the value of 0. it also has an overwritten uncover method.
    """

    def __init__(self):
        super().__init__(0)

    # now we have to override this, because this does something else.

    def uncover(self) -> bool:
        # have we been flagged? if no, continue, otherwise do nothing.
        if not self.flagged:
            self.uncovered = True  # uncover THIS field
            # uncover all neighbors
            for i in self.neighbors:
                # if this neighbour has not been uncovered, uncover it, otherwise leave it alone
                if not i.uncovered:
                    i.uncover()
        return True


class BombField(ValueField):
    """
    This is a Bomb field in minesweeper. The uncover function is also overwritten.
    """

    def __init__(self):
        super().__init__(None)
        self.triggered = False

    def uncover(self):
        # have we been flagged? if no, continue, otherwise do nothing.
        if not self.flagged:
            self.uncovered = True
            self.triggered = True
            return False  # game ends. no matter what
        return True
