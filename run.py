#!/usr/bin/env python
import sys, os
from DemonOverlord.core.util.logger import LogCommand, LogFormat, LogMessage, LogType


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
    workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DemonOverlord")
    bot = DemonOverlord(sys.argv, workdir)
    bot.loop.create_task(DemonOverlord.change_status(bot))
    bot.run(bot.config.token) # this will block execution


    # clean up after ourselves
    print(LogMessage("Bot Stopped, exiting gracefully", msg_type=LogType.WARNING))
    bot.database.connection_main.close()
    bot.database.connection_maintenance.close()



if __name__ == "__main__" and not missing_module:
    run()
