#!/usr/bin/env python

import errno
import os
import subprocess
import sys

def install_requirements():
    workdir = os.path.dirname(os.path.abspath(__file__))
    pip_cmd = [
        "pip3.8",
        "install",
        "-Ur",
        os.path.join(workdir, "requirements.txt"),
    ]
    print("Missing required modules, trying to install them...")
    subprocess.run(
        pip_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    try:

        modules_installed = True
    except (OSError, subprocess.SubprocessError):
        print("Requirement update failed!")
        exit(errno.EINVAL)


def run():
    try:
        from DemonOverlord.core.demonoverlord import DemonOverlord

        bot = DemonOverlord(sys.argv)
        bot.run(bot.config.token)
    except (ImportError, ModuleNotFoundError):
        install_requirements()
        run()


if __name__ == "__main__":
    run()