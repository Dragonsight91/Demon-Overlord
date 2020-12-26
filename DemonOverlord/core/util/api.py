# imports
from DemonOverlord.core.util.logger import LogMessage, LogType
import aiohttp
import random
from random import randint


class API:
    """
    This is the base API class. all APIs inherit from this class, so we have a standardized way to create instances of such
    """

    def __init__(self, apikey: str, name: str, url: str):
        self.apikey = apikey
        self.name = name
        self.url = url
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


class TenorAPI(API):
    """
    This is the Tenor API class, used to interact with Tenor, the GIF service.
    """

    def __init__(self, apikey: str):

        # initialize super class
        super().__init__(apikey, "tenor", "https://api.tenor.com/v1/search")

    async def get_interact(self, name: str) -> str:
        try:
            url = f'{self.url}?q={name.replace(" ", "+")}&key={self.apikey}&limit=20'
            
            async with await self.session.get(url) as response:
                assert response.status == 200
                data = await response.json()
                res_list = list(data["results"])

        except Exception:
            return False
        else:
            result = random.choice(res_list)["media"][0]["gif"]["url"]
            return result

        



class InspirobotAPI(API):
    """
    This is the Inspirobot API class, which handles all interaction with the inspirobot API.
    """

    def __init__(self):
        super().__init__("", "inspirobot", "https://inspirobot.me")

    # get the list of stuff from inspirobot
    async def __get_flow(self) -> str:

        # let's try getting something
        try:
            # you know... i don't like that you treat me like an object...
            url = f"{self.url}/api?generate=true"
            async with await self.session.get(self.url) as response:
                assert response.status == 200
                return await response.json()

        except Exception:
            # I've had enough of this... this is just WRONG
            return None

    # public function that gets data from inspiro and then gets the shortest quote
    async def get_quote(self) -> str:

        # get a flow and init quotes array
        img = await self.__get_flow()

        # FUCK, NO. WHY DOESN'T THIS WORK???? ~ Luzi
        if not img:
            return False

        # return the image
        return img


class SteamAPI(API):
    def __init__(self):
        super().__init__("", "Steam", "https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    
    async def get_appdata(self) -> dict:
        try:
            print(LogMessage(f"Trying to get steam appdata from '{self.url}'") )
            async with await self.session.get(self.url) as response:
                assert response.status == 200
                return await response.json()
        except AssertionError:
            print(LogMessage(f"Getting steam appdata failed.")) 

    async def get_gamedata(self, bot, game:str) -> dict:
        try:
            with bot.database.connection_main.cursor() as cursor:
                cursor.execute("SELECT * FROM public.steam_data WHERE game_name LIKE %s", [f"%{game}%"])
                results = cursor.fetchall()
                if len(results) == 0:
                    return None
                else:
                    return results[0]
        except Exception as e:
            print(LogMessage("something went wrong when requesting Game data", msg_type=LogType.ERROR))
            print(LogMessage(e, msg_type=LogType.ERROR))
