#!/usr/bin/env python

import errno
import os
import subprocess
import sys
from DemonOverlord.core.demonoverlord import DemonOverlord

def run():
    bot = DemonOverlord(sys.argv)
    bot.run(bot.config.token)

if __name__ == "__main__":
    run()