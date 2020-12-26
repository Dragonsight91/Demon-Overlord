
import discord
import asyncio
import random
import time
import psycopg2


from DemonOverlord.core.util.logger import LogHeader, LogMessage, LogType, LogFormat

async def change_status(client: discord.Client) -> None:
    """
    Change the status to a random one one specified in the config
    this is a coroutine and it's supposed to run in the background 
    """
    await client.wait_until_ready()
    while True:
        # there's a 5% chance of the status changing at all
        if random.random() < 0.05:
            # choose a random one from the list and set it
            presence = random.choice(client.config.status_messages)
            await client.change_presence(activity=presence)

            # log the action
            presence_type = str(presence.type).split(".")[1]
            print(
                LogMessage(
                    f"Set Status \"{LogFormat.format(f'{presence_type} {presence.name}', LogFormat.BOLD)}\""
                )
            )
        # sleep for 30 min and hand over control
        await asyncio.sleep(1800)

async def fetch_steamdata(client: discord.Client):
    await client.wait_until_done()
    while True:
        if not client.local:
            # client in local mode means no database connection and therefore this is impossible

            with client.database.connection_main.cursor() as cursor:
                cursor.execute("SELECT * FROM public.api_refresh WHERE api_name=%s", [client.api.steam.name])
                results = cursor.fetchall()
                if len(results) == 0:
                    print(LogMessage(f"API '{client.api.steam.name}' has not been used, creating entry..."))
                    cursor.execute("INSERT INTO public.api_refresh (api_name, last_access) VALUES (%s, %s)", [client.api.steam.name, int(time.time())])
                else: 
                    if (int(time.time()) - results[0]["last_access"]) < 864000:
                        LogMessage(f"API '{client.api.steam.name}' has been used within the last 24h, no update required.")
                        return
                    else:
                        cursor.execute("UPDATE public.api_refresh SET last_access=%s WHERE api_name=%s", [int(time.time()), client.api.steam.name])
                
                appdata = await client.api.steam.get_appdata()
                delay = 0.01
                amount = len(appdata["applist"]["apps"])
                print(LogMessage(f"inserting {amount} games into the database. this will take approximately {int((delay*amount)/3600)} hours"))
                for app in appdata["applist"]["apps"]:
                    if not app["name"] == "" and not app["appid"] == None:
                        try:
                            print(LogMessage(f"Trying to add game '{app['name']}' to local database."))
                            url = f"https://steamcdn-a.akamaihd.net/steam/apps/{app['appid']}/header.jpg"
                            storepage = f"https://store.steampowered.com/app/{app['appid']}"
                            cursor.execute("INSERT INTO public.steam_data (appid, game_name, image_url, store_url) VALUES (%s, %s, %s, %s)", [app["appid"],app["name"],url, storepage ])

                        except psycopg2.Error as e:
                            print(LogMessage(f"Game '{app['name']}' already exists, skipping."))

                        
                        await asyncio.sleep(delay) # limit to one/ delay sec
                    
        else:
            print(LogMessage(f"Running in local mode, cannot update information", msg_type=LogType.WARNING))
            return
        # try every 5 hours
        await asyncio.sleep(3600*24)
