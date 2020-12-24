# Demon Overlord

A discord bot custom built for the use of The InnerDemons discord community

## Installation

### THE BOT ONLY WORKS ON PYTHON 3.7+

The bot uses five environment variables

- `DISCORD_TESTBOT_TOKEN` OR `DISCORD_MAIN_TOKEN` (depending on whether you're starting in testing mode or production.)
- `TENOR_TOKEN` (an api token for tenor)
- `POSTGRES_USER` (the postgres bot user)
- `POSTGRES_PASSWORD` (the password for the postgres bot user)
- `POSTGRES_SERVER` (the server address, e.g `localhost:5000`)
- `POSTGRES_PORT` (the port on `POSTGRES_SERVER` )
- `POSTGRES_DB` (The name of the bot database) 

*NOTE: You only need one of the bot keys.*

To get a bot key:

- if you are member of InnerDemons:
    1. Ask on [#programmer-hell](https://discordapp.com/channels/658407338822336554/684088661884928040) on the Discord server to be added to the dev team
    2. Accept the invite
    3. Go to `Applications` and select the bot you want.
    4. Got to `Bots` copy the `TOKEN` next to the bot icon
- else:
    1. go to the [discord developer site](https://discord.com/developers/applications)
    2. create an application
    3. navigate to `bot`
    4. click `Add Bot` and confirm
    5. go to token and click `copy`
    6. this bot needs privileged gateway intents, so also scroll down and enable all of them
    7. to add the bot to a server just go to `OAuth2 > scopes`
    8. tick the `bot` scope, copy the URL and click `copy`
    9. paste the link into the browser and select the server where you wish to add the bot

Once you have the bot key, add the environment variable (this is how you do it in linux. For windows instructions, please consult the internet).

`export <var_name>=<token_value>`

Before you run it, please make sure you get the necessary dependencies

`pip --user install -r requirements.txt`

After that you will need a local postgreSQL database and set the envvars accordingly.

you can find more info in the [postgres documentation](https://www.postgresql.org/docs/9.3/tutorial-start.html).

## Running The Bot

You can run the bot in two different modes.

### FOR TESTING

Please only use `testmao` for testing any features.

`python run.py --dev`

### FOR DEPLOYMENT

If you're trying to do this and you're reading this, you're doing something very wrong. Don't do it. This is a mode reserved exclusively for running it on the server and it uses a different token.

## The directory structure

```none
\-- DemonOverlord
   |-- config
   |   |-- cmd_info.json
   |   |-- config.json
   |   \-- special
   \-- core
       |-- modules
       \-- util
```

All source files concerning the bot are contained within the DemonOverlord directory. anything above that is unimportant and is mostly documentation or setup stuff. Anything below this will be relative to the `DemonOverlord` directory.

### Config

This is the main directory for all the configuration files. These help keep the code cleaner and make simple text changes much easier.

The main config is `config/config.json`, which states all the necessary base configurations and definitions. It holds all the emoji, envvar names and prefixes the bot has in both production and testing mode.

`config/cmd_info.json` is all the help information for all commands. Any command the bot uses has to be added and documented here, so all its functions can easily be seen. Although it is mainly for the Help command, several other commands also use this file for extra functions.

Anything in the folder `config/special` is command specific info or configuration in the form of JSON files. These specify certain functionality or just text, so they are not hardcoded and keep the code cleaner.

### Core

Anything in this folder is the core functionality and code of the bot. it also holds `core/demonoverlord.py` which is the main file that defined the DemonOverlord class. `run.py` in the root directory merely accesses this to create an instance of DemonOverlord.

The folder `core/modules` holds all the commands. Any command simply has an async function called `handler`, which returns an instance of one of the responses, which can be found in the `core/util/responses.py` or a custom response that inherits from one of them, as seen in `core/modules/interactions.py`, which takes an ImageResponse and sends that. The common ancestor to all of them is `discord.Embed`.  

A simple command would be the Hello World command that is also implemented in `core/modules/hello.py` which simply greets the user that called the command. These commands are detected and imported automatically.

```python
import discord
from DemonOverlord.core.util.responses import TextResponse

async def handler(command) -> discord.Embed:
    msg = {"name": "Response:", "value": f"Hello, {command.invoked_by.mention}"}
    res = TextResponse(
        "Command - Hello",
        color=0xEF1DD9,
        icon=command.bot.config.izzymojis["hello"] or "🌺",
        msg=msg,
    )
    return res
```

The last folder, `core/util` holds core utilities for the bot. In there is the Command class, which gets used in all commands, the responses, config handler and any tool the bot needs to fulfill its task. Any API definitions like Tenor or InspiroBot are also in here.
