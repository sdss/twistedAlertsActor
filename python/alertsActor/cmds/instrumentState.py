#!/usr/bin/env python
# encoding: utf-8
#
# instrumentState.py
#

import click

from alertsActor.cmds import parser


@parser.command("instrumentState")
@click.argument('instrument', type=str, default=None, required=True)
@click.argument('state', default='up', required=True,
                type=click.Choice(['up', 'down']))
@click.option('-u', '--user', type=str, default=None,
              help='user unacknowledging alert')
async def instrumentState(command, instrument=None, state="up", user=None):
    """set the state of an instrument"""

    if user is None:
        user = ""

    if state == "down":
        actor.instrumentDown[instrument] = True
        for a in actor.activeAlerts:
            if instrument in a.instruments:
                await a.disable(user)
    else:
        actor.instrumentDown[instrument] = False
        for a in actor.disabledAlerts:
            if not a.instDown:
                await a.enable()

    actor = command.actor

    await actor.broadcastAll()
    await actor.broadcastInstruments()

    return command.finish()
