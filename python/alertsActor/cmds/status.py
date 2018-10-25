#!/usr/bin/env python
# encoding: utf-8
#
# status.py
#
# Created by José Sánchez-Gallego on 19 Mar 2017.


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

    cmd.writeToUsers("i", "activeAlerts={}".format(len(actor.activeAlerts)))
    cmd.writeToUsers("i", "unacknowledged={}".format(len([a for a in actor.activeAlerts if not a.acknowledged])))
    cmd.writeToUsers("i", "keywordsWatching={}".format(len(actor.hubModel)))
    cmd.setState(cmd.Done)

    return False
