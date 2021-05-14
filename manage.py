#!/usr/bin/env python3
import os
import sys

# don't create pyc or __pycache__ files/directories when in dev environment
sys.dont_write_bytecode = True

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "sharky.settings.dev")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
