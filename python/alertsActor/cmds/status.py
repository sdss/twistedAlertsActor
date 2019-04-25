#!/usr/bin/env python
# encoding: utf-8
#
# status.py


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds import alerts_context

__all__ = ('status')


@click.command()
@alerts_context
def status(actor, cmd):
    """returns actor status"""

    print("current model: ", actor.hubModel)

    actor.broadcastActive()
    actor.broadcastDisabled()
    actor.broadcastAll()
    actor.broadcastInstruments()

    cmd.setState(cmd.Done, 'text="Now you know all I know"')

    return False
