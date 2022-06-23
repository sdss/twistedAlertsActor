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
              help='user setting state')
async def instrumentState(command, instrument=None, state="up", user=None):
    """set the state of an instrument"""

    actor = command.actor

    if user is None:
        user = ""

    if state == "down":
        actor.instrumentDown[instrument] = True
        for k, alert in actor.monitoring.items():
            if instrument in alert.instruments:
                await alert.disable(user)
    else:
        actor.instrumentDown[instrument] = False
        for k, alert in actor.monitoring.items():
            if not alert.instDown:
                await alert.enable()

    await actor.broadcastAll()
    await actor.broadcastInstruments()

    return command.finish()
