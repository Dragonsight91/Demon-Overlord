#!/usr/bin/env python
import sys, os, asyncio
from DemonOverlord.core.util.logger import LogCommand, LogFormat, LogMessage, LogType
import DemonOverlord.core.util.services
# try importing the module and throw an error if can't be imported
try:
    from DemonOverlord.core.demonoverlord import DemonOverlord

    missing_module = False

except (ImportError):
    missing_module = True
    print(
        LogMessage(
            f"not all dependencies seem to be installed, please run {LogFormat.format('pip install -Ur requirements.txt', LogFormat.BOLD)}",
            prefix=f"{LogFormat.format('ERROR', LogFormat.FAIL)}",
            time=False,
        )
    )


def run():
    try:
        # initialize the bot
        workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DemonOverlord")
        bot = DemonOverlord(sys.argv, workdir)

        # actually run the bloody thing
        bot.run(bot.config.token)  # this will block execution from here
    finally:
        # clean up after ourselves, when we crash or stop
        print(LogMessage("Bot Stopped, exiting gracefully", msg_type=LogType.WARNING))
        bot.database.connection_main.close()
        bot.database.connection_maintenance.close()
        asyncio.run(bot.api.close_connections())


if __name__ == "__main__" and not missing_module:
    run()
