# Demon Overlord



A discord bot custom built for the use of The InnerDemons discord community 




## Installation

**THE BOT ONLY WORKS ON PYTHON 3.7+**

The bot uses three environment variables

- DISCORD_TESTBOT_TOKEN
- DISCORD_MAIN_TOKEN
- TENOR_TOKEN



*NOTE: You only need one of the bot keys.*

To get the bot keys

1. Ask on programmer-hell to be added to the dev team
2. Accept the invite
3. Go to `Applications` and select the bot you want.
4. Got to `Bots` copy the `TOKEN` next to the bot icon



Once you have the bot key, add the environment vatriable.

`export <var_name>=<token_value>`



The demon overlord automatically installs other requirements when run incase you do not have the required permissons, use 

`pip --user install -r requirements.txt`


## Running The Bot



You can run the bot in two different modes. 

### FOR TESTING

Please only use `testmao` for testing any features. 

`python run.py --dev`



### FOR DEPLOYMENT

If you're trying to do this and you're reading this, you're doing something very wrong. Don't do it.

Talk to the dev demons.

## The directory structure

```
`-- DemonOverlord
   |-- config
   |   |-- cmd_info.json
   |   |-- config.json
   |   `-- special
   `-- core
       |-- modules
       `-- util
```

All source files concerning the bot are contained within the DemonOverlord directory. anything above that is unimportant and is mostly documentation or setup stuff. Anything below this will be relative to the `DemonOverlord` directory

### <u>Config</u>

This is the main directory for all the configuration files. These help keep the code cleaner and make simple text changes much easier.

The main config is `config/config.json`, which states all the necessary base configurations and definitions. It holds all the emoji, envvar names and prefixes the bot has in both production and testing mode.

`config/cmd_info.json` is all the help information for all commands. Any command the bot uses has to be added and documented here, so all its functions can easily be seen. Although it is mainly for the Help command, several other commands also use this file for extra functions.

Anything in the folder `config/special` is command specific info or configuration in the form of JSON files. These specify certain functionality or just text, so they are not hardcoded and keep the code cleaner.

### <u>Core</u>

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