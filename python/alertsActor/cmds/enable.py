#!/usr/bin/env python
# encoding: utf-8
#
# enable.py



from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds import alerts_context

__all__ = ('enable')


@click.command()
@click.argument('alertkey', nargs=1, default=None, required=True)
@click.argument('severity', nargs=1, default='info', 
                type=click.Choice(['ok', 'info', 'apogeediskwarn','warn', 'serious', 'critical']))
@alerts_context
def enable(actor, cmd, alertkey=None, severity='info'):
    """enable an alert"""

    if isinstance(alertkey, unicode):
        alertkey = str(alertkey)  # .decode("utf-8")

    keyword = actor.monitoring[alertkey]

    keyword.enable()

    activeMessage = "activeAlerts{}".format(("=" if len(actor.activeAlerts) else "")) +\
                       ", ".join(["{}".format(a.actorKey) for a in actor.activeAlerts])

    disabledMessage = "disabledAlertRules{}".format(("=" if len(actor.disabledAlerts) else "")) +\
                       ", ".join(['"({}, {}, {})"'.format(a.actorKey, a.severity, a.disabledBy)
                                  for a in actor.disabledAlerts])

    cmd.writeToUsers("i", activeMessage)
    cmd.writeToUsers("i", disabledMessage)

    for a in actor.activeAlerts:
        a.dispatchAlertMessage()

    cmd.setState(cmd.Done, 'enabled')

    return False
