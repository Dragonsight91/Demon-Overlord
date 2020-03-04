# imports
import requests as req
import json
from random import randint


class TenorAPI(object):

    def __init__(self: object, apikey: str):
        self.apikey = apikey
        self.url = "https://api.tenor.com/v1"

    async def get_interact(self: object, name: str) -> str:
        res = await self.__request_list(name, 20)
        res_list = list(res["results"])

        index = randint(0, len(res_list)-1)
        return res_list[index]["media"][0]["gif"]["url"]

    async def __request_list(self: object, query: str, limit: int) -> object:
        print(query)
        try:
            url = f'{self.url}/search?q={query.replace(" ", "+")}&key={self.apikey}&limit={limit}'
            response = req.get(url)
            response.raise_for_status()
        except Exception:
            return False
        else:
            return json.loads(response.text)
