from datetime import time
from DemonOverlord.core.util.logger import LogMessage, LogType
import discord
import os
import sys
import json
import asyncio
import psycopg2, psycopg2.extras, psycopg2.extensions

from DemonOverlord.core.util.api import TenorAPI, InspirobotAPI
from DemonOverlord.core.util.limit import RateLimiter


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

            

        status_types = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,  # not used
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing
        }
        for message in self.raw["status_messages"]:
            
            self.status_messages.append(
                discord.Activity(
                    name=message["content"], 
                    type=status_types[message["type"]], 
                    url=("https://www.youtube.com/watch?v=dBRSjTKdtrI" if "Vecter" in message["content"] else None)
                )
            )

        # set the token
        self.token = os.environ.get(self.mode["tokenvar"])
        self.env = self.raw["env_vars"]
        self.emoji = self.raw["emoji"]

    def post_connect(self, bot: discord.Client):
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

        tenor_key = os.environ.get(config.env["tenor"][0])
        if tenor_key:
            self.tenor = TenorAPI(tenor_key)


class DatabaseConfig(object):
    """
    This class handles all Database integrations and connections as well as setup and testing the database.
    """

    def __init__(self, bot, confdir):
        temp = {}
        for var in bot.config.env["postgres"]:
            temp.update({var: os.environ[var]})

        self.db_user = temp["POSTGRES_USER"]
        self.db_pass = temp["POSTGRES_PASSWORD"]
        self.db_addr = temp["POSTGRES_SERVER"]
        self.db_port = temp["POSTGRES_PORT"]
        self.connection = None
        self.tables_scanned = asyncio.Event()
        
        with open(os.path.join(confdir, "db_template.json")) as file:
            db_template = json.load(file)

        self.tables = db_template["tables"]
        self.tables_to_fix = []
        # mark all schemata as missing
        self.schemata = {}
        for i in db_template["schemata"]:
            self.schemata.update({
                i : False
            })

        self.connection_maintenance = psycopg2.connect(
            user=self.db_user,
            password=self.db_pass,
            host=self.db_addr,
            port=self.db_port,
            database="postgres",
        )
        self.connection_maintenance.set_session(autocommit=True)

        # try to connect 5 times
        success = False
        n = 5
        while not success and n >1:
            try:
                self.connection_main = psycopg2.connect(
                    user=self.db_user,
                    password=self.db_pass,
                    host=self.db_addr,
                    port=self.db_port,
                    database="DemonOverlord",
                )
                self.connection_main.set_session(autocommit=True)
                success = True
            except Exception:
                try: 
                    print(LogMessage(f"Database DemonOverlord does not exist, trying to create, try {n-4}", msg_type=LogType.ERROR,time=False))
                    cursor = self.connection_maintenance.cursor()
                    cursor.execute("CREATE DATABASE \"DemonOverlord\" WITH OWNER = bot ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8' TABLESPACE = pg_default CONNECTION LIMIT = -1;")
                except Exception:
                    print(LogMessage(f"Failed to create database", msg_type=LogType.ERROR, time=False))
                else:
                    print(LogMessage(f"Database successfully created", time=False))
            n-=1
        if not success:
            print(LogMessage(f"Failed to create database after 5 tries", msg_type=LogType.ERROR, time=False))

    async def table_test(self) -> bool:
        """
        Test if all tables exist and are set up properly, otherwise add them to the `self.tables_to_fix` list with tag
        """
        
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)

        for table in self.tables:
            # test if tables exist
            cursor.execute("SELECT table_name, table_schema FROM information_schema.tables WHERE table_name=%s;", [table["table_name"]])
            result = cursor.fetchall()

            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING"))
                continue

            # test if the table has columns at all
            cursor.execute("SELECT column_name, column_default, data_type, is_nullable, character_maximum_length FROM information_schema.columns WHERE table_name=%s;", [table["table_name"]])
            result = cursor.fetchall()
            
            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING_COLS"))
                continue

            # test if columns exist and are set up correctly
            for column in table["columns"]:
                row = list(filter(lambda x: x["column_name"] == column["column_name"], result))

                if len(row) == 0:
                    self.tables_to_fix.append((table, "MISSING_COL", column))
                    continue
                
                # scan through columns and see if all are set up correctly
                for key in column:
                    if key == "auto_increment":
                        continue
                
                    if key == "is_nullable":
                        nullable = "YES" if column[key] else "NO"
                        if not nullable == row[0][key]:
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue


                    if row[0]["data_type"] == "boolean" and key == "column_default":
                        if not column[key] == eval((row[0][key].lower()).capitalize()):
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

                    if row[0]["data_type"] == "character varying" and key == "column_default":
                        if not str(row[0][key]) == f"'{column[key]}'::character varying" and ( not str(column[key]) == str(row[0][key])):
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue
                            
                    if row[0]["data_type"] in ("integer", "bigint") and key == "column_default":
                        if not str(column[key]) == str(row[0][key]):
                            self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

                    if not str(column[key]) == str(row[0][key]):
                        self.tables_to_fix.append((table, "WRONG_SETUP", column))
                        continue

            # test if constraints exist 
            cursor.execute("SELECT table_name, column_name, constraint_name FROM information_schema.constraint_column_usage WHERE column_name=%s AND constraint_name=%s;",[table["primary_key"], f"{table['table_name']}_pkey"])
            result = cursor.fetchall()

            if len(result) == 0:
                self.tables_to_fix.append((table, "MISSING_PKEY"))
                continue    
                        
                        
        cursor.close()  
        if len(self.tables_to_fix) > 0:
            return False
        else:
            return True

    async def schema_test(self) -> bool:
        """A function to test if all schemas exist"""
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM information_schema.schemata")
        table = cursor.fetchall()
        cursor.close()

        count = 0
        for row in table:
            if row["schema_name"] in self.schemata:
                self.schemata[row["schema_name"]] = True
                count+=1
                
        
        # are all schemata in the database? 
        if count == len(self.schemata):
            return True
        else:
            return False

    async def table_fix(self):
        while True:
            to_fix = None
            try:
                to_fix = self.tables_to_fix.pop(0)
            except IndexError:
                print(LogMessage("All database issues fixed"))
                break
            
            
            if to_fix[1] == "MISSING": 
                print(LogMessage(f"Creating Table '{to_fix[0]['table_name']}'"))
                await self._create_table(to_fix[0])
            
            elif to_fix[1] == "MISSING_PKEY": # primary key is not set
                print(LogMessage(f"Creating PKEY '{to_fix[0]['primary_key']}' on Table '{to_fix[0]['table_name']}'"))
                await self._fix_pkey(to_fix[0]['table_name'], to_fix[0]['table_schema'], to_fix[0]['primary_key'])

            elif to_fix[1] == "MISSING_COLS": # none exist
                print(LogMessage(f"Creating columns in Table '{to_fix[0]['table_name']}'"))
                for column in to_fix[0]["columns"]:
                    print(LogMessage(f"Creating column '{column['column_name']}' in Table '{to_fix[0]['table_name']}'"))
                    await self._add_column(to_fix[0]['table_name'], to_fix[0]['table_schema'], column)

            
            elif to_fix[1] == "MISSING_COL": # single missing case
                print(LogMessage(f"Add missing column '{to_fix[2]['column_name']}' in Table '{to_fix[0]['table_name']}'"))
                await self._add_column(to_fix[0]['table_name'], to_fix[0]['table_schema'], to_fix[2])

            elif to_fix[1] == "WRONG_SETUP": # wrong type or similar
                print(LogMessage(f"Correcting column '{to_fix[2]['column_name']}' in Table '{to_fix[0]['table_name']}'"))
                await self._fix_column(to_fix[0]['table_name'],to_fix[0]['table_schema'], to_fix[2])

    async def _create_table(self, table: dict):
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)
        columns = []
        
        for column in table["columns"]:
            nullable = 'NOT NULL' if not column['is_nullable'] else ''

            # escape the actual string
            if type(column['column_default']) is str:
                escape_val = f"\'{column['column_default']}\'::character varying"
            
            # convert python bool to SQL bool
            elif type(column['column_default']) is bool:
                escape_val = str(column['column_default']).upper()
            
            # everything else
            else:
                escape_val=f"{column['column_default']}"
            
            # handle default value
            default = f"DEFAULT {escape_val}"

            # handle maximum legth
            max_len = f"({column['character_maximum_length']})" if column['character_maximum_length'] else ""

            # send query
            query = f"{column['column_name']} {column['data_type'] if not column['auto_increment'] else 'serial'}{max_len} {nullable} {default if not column['column_default'] is None else ''}"
            columns.append(query)
        
        if table["primary_key"]:
            columns.append(f"CONSTRAINT \"{table['table_name']}_pkey\" PRIMARY KEY ({table['primary_key']})")
        
        query = f"CREATE TABLE {table['table_schema']}.{table['table_name']} ({','.join(columns)}) TABLESPACE {table['table_space']}"
        cursor.execute(query)

        cursor.execute(f"COMMENT ON TABLE {table['table_schema']}.{table['table_name']} IS %s;", [table["comment"]])
        cursor.close()

    async def _fix_pkey(self, table_name, schema_name, column):
        """This fixes the table if the primary key is not set correctly"""

        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ADD PRIMARY KEY ({column})")

    async def _add_column(self, table_name, schema_name, column):
        """This fixes the table if a column does not exist"""
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)

        # some stuff to prepare
        nullable = 'NOT NULL' if not column['is_nullable'] else ''
        escape_val = f"\'{column['column_default']}\'" if type(column['column_default']) is str else f"{column['column_default']}"
        default = f"DEFAULT {escape_val}"  

        # the query
        cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ADD {column['column_name']} {column['data_type'] if not column['auto_increment'] else 'serial'} {nullable} {default if column['column_default'] else ''};")
        cursor.close()

    async def _fix_column(self, table_name, schema_name, column):
        """This fixes the table if a column has not been set up properly"""
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)

        escape_val = f"\'{column['column_default']}\'" if type(column['column_default']) is str else f"{column['column_default']}"

        cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} TYPE {column['data_type'] if not column['auto_increment'] else 'serial'};")
        
        if column["column_default"]:
            cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} SET DEFAULT {escape_val}")

        if not column['is_nullable']:
            cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ALTER COLUMN {column['column_name']} SET NOT NULL")

        cursor.close()

    async def schema_fix(self):
        cursor = self.connection_main.cursor(cursor_factory = psycopg2.extras.DictCursor)

        while not await self.schema_test():
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
        self.interactions = None
        self.command_info = None
        self.list = []
        self.ratelimits = None
        self.izzylinks = None
        self.chats = None
        self.short = dict()
        self.minecraft = dict()

        with open(os.path.join(confdir, "interactions.json")) as f:
            self.interactions = json.load(f)

        with open(os.path.join(confdir, "cmd_info.json")) as f:
            self.command_info = json.load(f)

        with open(os.path.join(confdir, "special/izzy.json")) as f:
            self.izzylinks = json.load(f)

        with open(os.path.join(confdir, "special/chats.json")) as f:
            self.chats = json.load(f)

        with open(os.path.join(confdir, "special/minecraft.json")) as f:
            self.minecraft = json.load(f)

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

        # generate all other rate limits
        self.ratelimits = RateLimiter(self.list)
