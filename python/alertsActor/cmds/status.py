#!/usr/bin/env python
# encoding: utf-8
#
# status.py

import os
import yaml

import click

from alertsActor.cmds import parser
from alertsActor.tools import wrapBlocking


def dumpModel(model, path=None):
    if path is None:
        path = "alerts.hubModel.yaml"
    with open(path, "w") as dump:
        print(yaml.dump(model), file=dump)


@parser.command()
async def status(command):
    """returns actor status"""

    actor = command.actor

    await actor.broadcastAll(command=command)
    await actor.broadcastInstruments(command=command)

    # try:
    #     dontClutterSDSSUser = os.getlogin()
    # except OSError:
    #     # when run as a daemon, getlogin will fail
    #     dontClutterSDSSUser = "sdss5"
    # if "sdss" in dontClutterSDSSUser:
    #     path = "/data/logs/actors/alerts/alerts.hubModel.yaml"
    #     await wrapBlocking(dumpModel, actor.hubModel, path)

    # # otherwise we can clutter the home directory a bit
    # # write a log of the hubModel for posterity
    # else:
    #     path = "alerts.hubModel.yaml"
    #     await wrapBlocking(dumpModel, actor.hubModel, path)

    return command.finish(text="Now you know all I know")
