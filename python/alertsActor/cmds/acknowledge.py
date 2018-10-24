#!/usr/bin/env python
# encoding: utf-8
#
# acknowledge.py
#
# Created by José Sánchez-Gallego on 19 Mar 2017.


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds import alerts_context

__all__ = ('acknowledge')


@click.command()
@click.option('--alertKey', default=None, help='which actor.key to acknowledge.')
@click.option('--severity', default='i', help='the severity to acknowledge.')
@alerts_context
def acknowledge(actor, cmd, alertKey, severity):
    """acknowledge an alert"""


    cmd.writeToUsers("i", "activeAlerts={}".format(len(actor.activeAlerts)))
    cmd.writeToUsers("i", "keywordsWatching={}".format(len(actor.dataModel)))
    cmd.setState(cmd.Done)

    return False
