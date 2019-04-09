#!/usr/bin/env python
# encoding: utf-8
#
# instrumentState.py
#


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds import alerts_context

__all__ = ('instrumentState')


@click.command()
@click.argument('instrument', nargs=1, default=None, required=True)
@click.argument('state', nargs=1, default='up', type=click.Choice(['up', 'down']))
@alerts_context
def instrumentState(actor, cmd, instrument=None, state="up"):
    """set the state of an instrument"""

    if state == "down":
        actor.instrumentUp[instrument] = False
        for a in actor.activeAlerts:
            if a.instrument == instrument:
                a.disable("i")
    else:
        actor.instrumentUp[instrument] = True
        for a in actor.disabledAlerts:
            if a.instrument == instrument:
                a.enable()

    actor.broadcastActive()
    actor.broadcastDisabled()
    actor.broadcastAll()
    actor.broadcastInstruments()

    cmd.setState(cmd.Done, '{} set to {}'.format(instrument, state))

    return False
