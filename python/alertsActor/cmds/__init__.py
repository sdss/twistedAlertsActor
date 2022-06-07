#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# __init__.py
#

import glob
import importlib
import os

import click
from clu.parsers.click import CluGroup, get_schema, help_, keyword, ping, version


@click.group(cls=CluGroup)
def parser(*args):
    pass


parser.add_command(ping)
parser.add_command(version)
parser.add_command(help_)
parser.add_command(get_schema)
parser.add_command(keyword)


# Autoimport all modules in this directory so that they are added to the parser.

exclusions = ["__init__.py"]

cwd = os.getcwd()
os.chdir(os.path.dirname(os.path.realpath(__file__)))

files = [
    file_ for file_ in glob.glob("**/*.py", recursive=True) if file_ not in exclusions
]

for file_ in files:
    modname = file_[0:-3].replace("/", ".")
    mod = importlib.import_module("alertsActor.cmds." + modname)

os.chdir(cwd)
