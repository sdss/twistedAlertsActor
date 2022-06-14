#!/usr/bin/env python
# encoding: utf-8
#
# enable.py

import click

from alertsActor.cmds import parser


@parser.command()
@click.argument('alertkey', type=str, required=True)
async def enable(command, alertkey=None):
    """enable an alert"""

    actor = command.actor

    keyword = actor.monitoring[alertkey]

    await keyword.enable()

    await actor.broadcastAll()

    return command.finish()
