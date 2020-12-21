#!/usr/bin/env python
import sys
from DemonOverlord.core.util.logger import LogFormat, LogMessage


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
    bot = DemonOverlord(sys.argv)
    bot.loop.create_task(DemonOverlord.change_status(bot))
    bot.run(bot.config.token)


if __name__ == "__main__" and not missing_module:
    run()
