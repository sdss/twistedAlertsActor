#!/usr/bin/env python
# encoding: utf-8
#
# disable.py

import click

from alertsActor.cmds import parser


@parser.command()
@click.argument('alertkey', type=str, required=True)
@click.option('-u', '--user', type=str, default=None,
              help='user disabling this alert')
async def disable(command, alertkey, user=None):
    """disable an alert"""

    if user is None:
        user = ""

    actor = command.actor

    keyword = actor.monitoring[alertkey]

    await keyword.disable(user)

    await actor.broadcastAll()

    return command.finish()
