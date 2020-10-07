import discord
import traceback

from DemonOverlord.core.util.responses import ImageResponse, ErrorResponse
from DemonOverlord.core.util.api import InspirobotAPI


async def handler(command) -> discord.Embed:

    # try to get an image URL from inspirobot and return it as such
    try:
        inspirobot = InspirobotAPI()
        url = await inspirobot.get_quote()
        res = ImageResponse("Quote by Inspirobot", url, color=0xFE0A2E, icon="📃")
    except Exception:
        res = ErrorResponse(command, traceback.format_exc())

    return res
