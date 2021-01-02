
import datetime
from enum import auto, unique
from os.path import join
import time
import discord
import os
import ujson as json
import asyncio
import psycopg2, psycopg2.extras, psycopg2.extensions


from DemonOverlord.core.util.api import TenorAPI, InspirobotAPI, SteamAPI
from DemonOverlord.core.util.logger import LogMessage, LogType

class BotConfig(object):
    """
    This is the Bot config object, it holds the core configuration of the bot
    """

    def __init__(self, bot: discord.Client, confdir: str, argv: list):
        # set all vars None first, this also gives us a list of all currently available vars
        self.raw = None
        self.mode = None
        self.izzymojis = dict()
        self.token = None
        self.env = None
        self.emoji = None
        self.status_messages = list()

        # get the raw config.json
        with open(os.path.join(confdir, "config.json")) as f:
            self.raw = json.load(f)

        # create config from cli stuff
        for arg in argv:

            # set bot mode
            if arg in self.raw["cli_options"]["bot_modes"]:
                self.mode = self.raw["cli_options"]["bot_modes"][argv[1]]
            else:
                self.mode = self.raw["cli_options"]["bot_modes"]["--dev"]

        # all usable activity types
        status_types = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }

        # go through status messages and add them to the list of possible messages
        for message in self.raw["status_messages"]:

            self.status_messages.append(
                discord.Activity(
                    name=message["content"],
                    type=status_types[message["type"]],

                    # the url is a special case, as a joking promo for vecter
                    url=(
                        "https://www.youtube.com/watch?v=dBRSjTKdtrI"
                        if "Vecter" in message["content"]
                        else None
                    ),
                )
            )

        # set the token
        self.env = self.raw["env_vars"]
        self.token = os.environ[self.env["discord"][f"{self.mode['name']}_token"]]
        self.emoji = self.raw["emoji"]

    def post_connect(self, bot: discord.Client):
        """this function loads any configuration that needs the bot to be online (like emoji)"""

        # generate izzymoji list
        for key in self.raw["izzymojis"].keys():
            self.izzymojis[key] = bot.get_emoji(self.raw["izzymojis"][key])


class APIConfig(object):
    """
    This is the API config class, it combines and initializes the APIs into a single point
    """

    def __init__(self, config: BotConfig):
        # var init
        self.tenor = None
        self.inspirobot = InspirobotAPI()
        self.steam = SteamAPI()

        tenor_key = os.environ.get(config.env["tenor"]["token"])
        if tenor_key:
            self.tenor = TenorAPI(tenor_key)

    async def close_connections(self):
        await self.tenor.close() if self.tenor else None
        await self.steam.close()
        await self.inspirobot.close()


class DatabaseConfig(object):
    """
    This class handles all Database integrations and connections as well as setup and testing the database.
    """

    def __init__(self, bot: discord.Client, confdir):

        # set internal to env
        self.db_user = os.environ[bot.config.env["postgres"]["user"]]
        self.db_pass = os.environ[bot.config.env["postgres"]["pass"]]
        self.db_addr = os.environ[bot.config.env["postgres"]["host"]]
        self.db_port = os.environ[bot.config.env["postgres"]["port"]]
        self.main_db = os.environ[bot.config.env["postgres"]["db"]]
        self.connection = None
        self.tables_scanned = asyncio.Event()
        self.settings = {}

        # load database templates
        with open(os.path.join(confdir, "db_template.json")) as file:
            db_template = json.load(file)

        self.tables = db_template["tables"]
        self.tables_to_fix = []
        self.necessary_tables = list(filter(lambda x : x["entry_required"], self.tables))

        # mark all schemata as missing by default
        self.schemata = {}
        for i in db_template["schemata"]:
            self.schemata.update({i: False})

        # create maintenance connection
        self.connection_maintenance = psycopg2.connect(
            user=self.db_user,
            password=self.db_pass,
            host=self.db_addr,
            port=self.db_port,
            database="postgres",
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        self.connection_maintenance.set_session(autocommit=True)

        # try to connect to the main database 5 times and give up after
        success = False
        n = 5
        while not success and n > 1:
            try:
                # try creating a connection
                self.connection_main = psycopg2.connect(
                    user=self.db_user,
                    password=self.db_pass,
                    host=self.db_addr,
                    port=self.db_port,
                    database=self.main_db,
                    cursor_factory=psycopg2.extras.RealDictCursor,
                )
                self.connection_main.set_session(autocommit=True)
                success = True
            except Exception:
                # if it fails, we try creating it
                try:
                    print(
                        LogMessage(
                            f"Database {self.main_db} does not exist, trying to create",
                            msg_type=LogType.ERROR,
                            time=False,
                        )
                    )
                    cursor = self.connection_maintenance.cursor()
                    cursor.execute(
                        f"CREATE DATABASE \"{self.main_db}\" WITH OWNER = bot ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8' TABLESPACE = pg_default CONNECTION LIMIT = -1;"
                    )
                except Exception:
                    # and we log our failure
                    print(
                        LogMessage(
                            f"Failed to create database",
                            msg_type=LogType.ERROR,
                            time=False,
                        )
                    )
                else:
                    print(LogMessage(f"Database successfully created", time=False))
            n -= 1
        if not success:
            print(
                LogMessage(
                    f"Failed to create database after 5 tries",
                    msg_type=LogType.ERROR,
                    time=False,
                )
            )

    async def table_test(self) -> bool:
        """
        Test if all tables exist and are set up properly, otherwise add them to the `self.tables_to_fix` list with tag
        """

        # create out infanmous cursor
        cursor = self.connection_main.cursor()

        # walk through all tables and check them 
        for table in self.tables:

            # test if tables exist
            cursor.execute(
                "SELECT table_name, table_schema FROM information_schema.tables WHERE table_name=%s;",
                [table["table_name"]],
            )
            result = cursor.fetchall()

            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING"))
                continue

            # test if the table has columns at all
            cursor.execute(
                "SELECT column_name, column_default, data_type, is_nullable, character_maximum_length FROM information_schema.columns WHERE table_name=%s;",
                [table["table_name"]],
            )
            result = cursor.fetchall()

            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING_COLS"))
                continue

            # test if columns exist and are set up correctly
            for column in table["columns"]:
                row = list(
                    filter(lambda x: x["column_name"] == column["column_name"], result)
                )

                if len(row) == 0:
                    self.tables_to_fix.append((table, "MISSING_COL", column))
                    continue

                # scan through columns and see if all are set up correctly
                for key in column:

                    # this key is unimportant for the database, and i don't know how to test for it
                    if key == "auto_increment":
                        continue

                    # yay, we arrived at nullable, now we have to handle the YES and NO
                    if key == "is_nullable":
                        nullable = "YES" if column[key] else "NO"
                        if not nullable == row[0][key]:
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

                    # this part handles boolean types and type comparison to Python bool
                    if row[0]["data_type"] == "boolean" and key == "column_default" and not column["is_nullable"]:
                        if not column[key] == eval((str(row[0][key]).lower()).capitalize()):
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))

                        continue

                    # The part that handles if the default_column being a string
                    if (
                        row[0]["data_type"] == "character varying"
                        and key == "column_default"
                    ):
                        if not str(
                            row[0][key]
                        ) == f"'{column[key]}'::character varying" and (
                            not str(column[key]) == str(row[0][key])
                        ):
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

                    # handle everything else
                    if not str(column[key]) == str(row[0][key]):
                        self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

            # test if primary key exists
            cursor.execute(
                "SELECT table_name, column_name, constraint_name FROM information_schema.constraint_column_usage WHERE column_name=%s AND constraint_name=%s;",
                [table["primary_key"], f"{table['table_name']}_pkey"],
            )
            result = cursor.fetchall()

            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING_PKEY"))
                continue
        # close the cursor and finish up
        cursor.close()
        if len(self.tables_to_fix) > 0:
            return False
        else:
            return True

    async def schema_test(self) -> bool:
        """A function to test if all schemas exist"""

        # make cursor and get all schemas
        cursor = self.connection_main.cursor()
        cursor.execute("SELECT * FROM information_schema.schemata")
        table = cursor.fetchall()
        cursor.close()

        # mark all existing schemas as such and leave others alone 
        count = 0
        for row in table:
            if row["schema_name"] in self.schemata:
                self.schemata[row["schema_name"]] = True
                count += 1

        # are all schemata in the database?
        if count == len(self.schemata):
            return True
        else:
            return False

    async def table_fix(self) -> None:
        """The function that fixes all broken tables and columns"""

        # do until done
        while True:
            to_fix = None
            # try to pop the first element from the array, treating it essentially as queue
            try:
                to_fix = self.tables_to_fix.pop(0)
            except IndexError:
                print(LogMessage("All table issues fixed"))
                break

            # the table doesn't exist
            if to_fix[1] == "MISSING":
                print(LogMessage(f"Creating Table '{to_fix[0]['table_name']}'"))
                await self._create_table(to_fix[0])

            # the primary key of the table is missing or incorrect
            elif to_fix[1] == "MISSING_PKEY":
                print(
                    LogMessage(
                        f"Creating PKEY '{to_fix[0]['primary_key']}' on Table '{to_fix[0]['table_name']}'"
                    )
                )
                await self._fix_pkey(
                    to_fix[0]["table_name"],
                    to_fix[0]["table_schema"],
                    to_fix[0]["primary_key"],
                )

            # table has no columns
            elif to_fix[1] == "MISSING_COLS":  # none exist
                print(
                    LogMessage(f"Creating columns in Table '{to_fix[0]['table_name']}'")
                )

                # go through all columns and add them
                for column in to_fix[0]["columns"]:
                    print(
                        LogMessage(
                            f"Creating column '{column['column_name']}' in Table '{to_fix[0]['table_name']}'"
                        )
                    )
                    await self._add_column(
                        to_fix[0]["table_name"], to_fix[0]["table_schema"], column
                    )

            # database has certain columns missing
            elif to_fix[1] == "MISSING_COL":  # single missing case
                print(
                    LogMessage(
                        f"Add missing column '{to_fix[2]['column_name']}' in Table '{to_fix[0]['table_name']}'"
                    )
                )
                await self._add_column(
                    to_fix[0]["table_name"], to_fix[0]["table_schema"], to_fix[2]
                )

            # the column id not set up correctly
            elif to_fix[1] == "WRONG_SETUP": 
                print(
                    LogMessage(
                        f"Correcting column '{to_fix[2]['column_name']}' in Table '{to_fix[0]['table_name']}'"
                    )
                )
                await self._fix_column(
                    to_fix[0]["table_name"], to_fix[0]["table_schema"], to_fix[2]
                )

    async def _create_table(self, table: dict) -> None:
        """the function to create a table from a template"""
        cursor = self.connection_main.cursor()
        columns = []

        for column in table["columns"]:
            nullable = "NOT NULL" if not column["is_nullable"] else ""

            # escape the actual string
            if type(column["column_default"]) is str:
                escape_val = f"'{column['column_default']}'::character varying"

            # convert python bool to SQL bool
            elif type(column["column_default"]) is bool:
                escape_val = str(column["column_default"]).upper()

            # everything else
            else:
                escape_val = f"{column['column_default']}"

            # handle default value
            default = f"DEFAULT {escape_val}"

            # handle maximum legth
            max_len = (
                f"({column['character_maximum_length']})"
                if column["character_maximum_length"]
                else ""
            )

            # aggregate column specific query snippets
            query = f"{column['column_name']} {column['data_type'] if not column['auto_increment'] else 'serial'}{max_len} {nullable} {default if not column['column_default'] is None else ''}"
            columns.append(query)

        # do we need a primary key?
        if table["primary_key"]:
            columns.append(
                f"CONSTRAINT \"{table['table_name']}_pkey\" PRIMARY KEY ({table['primary_key']})"
            )

        # send the query
        query = f"CREATE TABLE {table['table_schema']}.{table['table_name']} ({','.join(columns)}) TABLESPACE {table['table_space']}"
        cursor.execute(query)

        # add any comment that exists (Null returns false)
        if table["comment"]:
            cursor.execute(
                f"COMMENT ON TABLE {table['table_schema']}.{table['table_name']} IS %s;",
                [table["comment"]],
            )
        cursor.close()

    async def _fix_pkey(self, table_name:str, schema_name:str, column:dict) -> None:
        """This fixes the table if the primary key is not set correctly. It simply overwrites the current PKEY"""

        cursor = self.connection_main.cursor()
        cursor.execute(
            f"ALTER TABLE {schema_name}.{table_name} ADD PRIMARY KEY ({column})"
        )

    async def _add_column(self, table_name:str, schema_name:str, column:dict) -> None:
        """This adds a column to a table"""
        cursor = self.connection_main.cursor()

        # some stuff to prepare
        nullable = "NOT NULL" if not column["is_nullable"] else ""

        # escape the actual string
        if type(column["column_default"]) is str:
            escape_val = f"'{column['column_default']}'::character varying"

        # convert python bool to SQL bool
        elif type(column["column_default"]) is bool:
            escape_val = str(column["column_default"]).upper()

        # everything else
        else:
            escape_val = f"{column['column_default']}"

        # more query snippets
        nullable = "NOT NULL" if not column["is_nullable"] else ""
        default = f"DEFAULT {escape_val}"

        # the query
        cursor.execute(
            f"ALTER TABLE {schema_name}.{table_name} ADD {column['column_name']} {column['data_type'] if not column['auto_increment'] else 'serial'} {nullable} {default if column['column_default'] else ''};"
        )
        cursor.close()

    async def _fix_column(self, table_name:str, schema_name:str, column:dict) -> None:
        """This fixes a column if a it has not been set up properly"""
        
        cursor = self.connection_main.cursor()

        # handle maximum legth
        max_len = (
            f"({column['character_maximum_length']})"
            if column["character_maximum_length"]
            else ""
        )
        escape_val = (
            f"'{column['column_default']}'"
            if type(column["column_default"]) is str
            else f"{column['column_default']}"
        )

        # set the data type
        cursor.execute(
            f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} TYPE {column['data_type'] if not column['auto_increment'] else 'serial'}{max_len};"
        )

        # set  or unset default value
        if column["column_default"] is not None:
            cursor.execute(
                f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} SET DEFAULT {escape_val}"
            )
        else:
            cursor.execute(
                f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} DROP DEFAULT "
            )

        # set or unset NOT NULL constraint
        if not column["is_nullable"]:
            cursor.execute(
                f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} SET NOT NULL"
            )
        else:
            cursor.execute(
                f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} DROP NOT NULL"
            )
        cursor.close()

    async def add_guild(self, guild:int) -> None:
        """Add a guild to the mandatory tables in the database"""
        cursor = self.connection_main.cursor()
        for table in self.necessary_tables:
            if not table["all_required"]:
                # these ones can be set by default
                cursor.execute(f"INSERT INTO {table['table_schema']}.{table['table_name']} (guild_id) VALUES (%s)", [guild.id])
        
        # manual insertion of data
        cursor.execute(f"INSERT INTO public.last_seen (guild_id, joined_at, last_seen) VALUES (%s, %s, %s)", [guild.id, int(datetime.datetime.timestamp(guild.me.joined_at)), int(time.time())])
        cursor.close()

    async def check_guilds(self, bot:discord.Client):
        cursor = self.connection_main.cursor()

    async def remove_guild(self, guild:int) -> None:
        """Remove a guild from all tables"""
        cursor = self.connection_main.cursor()

        for table in self.tables:
            cursor.execute(f"DELETE FROM {table['table_schema']}.{table['table_name']} WHERE guild_id=%s", [guild.id])
        cursor.close()

    async def update_guilds(self, guilds: list):
        cursor = self.connection_main.cursor()

    async def _fix_guild_entry(self, table_name:str, schema_name:str, guild_id:int, column:dict) -> None:
        """fix a wrong default value (Null where NOT NULL is set)"""
        cursor = self.connection_main.cursor()
        cursor.execute(f"UPDATE {schema_name}.{table_name} SET column=%s WHERE guild_id=%s", [column["column_default"], guild_id])
        cursor.close()

    async def get_welcome(self, guild_id, *,  wait_pending=False) -> dict:
        with self.connection_main.cursor() as cursor:
            cursor.execute(f"SELECT * FROM admin.welcome_messages WHERE guild_id=%s", [guild_id])

            if (res := cursor.fetchone()):
                return res if res["wait_pending"] == wait_pending else None
            else:
                return None

    async def update_welcome(self) -> None:
        pass
    
    async def get_autorole(self, guild_id, *, wait_pending=False) -> list():
        with self.connection_main.cursor() as cursor:
            cursor.execute(f"SELECT * FROM admin.autoroles WHERE guild_id=%s", [guild_id])
            if (res := cursor.fetchone()):
                return res if res["wait_pending"] == wait_pending else None
            else:
                return None

    async def add_autorole(self, guild_id, role_id, delay=None, wait_pending=None):
        with self.connection_main.cursor() as cursor:
            attr = [guild_id, role_id]
            col_delay = col_wait = ""
            values = "%s, %s"

            if delay != None:
                col_delay =',delay'
                attr.append(delay)
                values += ",%s"

            if wait_pending != None:
                col_wait = ',wait_pending' 
                values += ",%s"
                attr.append(wait_pending)

            cursor.execute(f"INSERT INTO admin.autoroles (guild_id, role_id {col_delay} {col_wait}) VALUES ({values})", attr)

            cursor.execute(f"SELECT * FROM admin.autoroles WHERE guild_id=%s", [guild_id])
            res = cursor.fetchall()

    async def schema_fix(self) -> None:
        """"adds any schema marked as missing"""
        cursor = self.connection_main.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # step through all schemas and check the ones that aren't marked (False), then add it
        for key in self.schemata:
            if not self.schemata[key]:
                cursor.execute(f"CREATE SCHEMA {key} AUTHORIZATION bot;")
                cursor.execute(f"GRANT ALL ON SCHEMA {key} TO bot;")

        cursor.close()


class CommandConfig(object):
    """
    This is the Command Config class. It handles all the secondary configurations for specific commands and/or command groups
    """

    def __init__(self, confdir: str):
        # initialize all variables
        self.interactions = None
        self.command_info = None
        self.list = []
        self.ratelimits = None
        self.izzylinks = None
        self.chats = None
        self.short = dict()
        self.minecraft = dict()

        # load command configuration from files
        with open(os.path.join(confdir, "interactions.json")) as f:
            self.interactions = json.load(f)

        with open(os.path.join(confdir, "cmd_info.json")) as f:
            self.command_info = json.load(f)

        with open(os.path.join(confdir, "special/izzy.json")) as f:
            self.izzylinks = json.load(f)

        # load in the command list and update the short commands
        for i in self.command_info.keys():
            for j in self.command_info[i]["commands"]:
                self.list.append(j)
                if j["short"]:
                    self.short.update({j["short"]: j["command"]})

        # generate the ratelimit for all interactions
        self.list.append(
            {
                "command": "interactions",
                "ratelimit": self.command_info["interactions"]["ratelimit"],
            }
        )

