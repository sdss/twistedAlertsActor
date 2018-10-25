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
@click.argument('alertkey', nargs=1, default=None, required=True)
@click.argument('severity', nargs=1, default='info', 
                type=click.Choice(['info', 'warning', 'serious', 'critical']))
@click.option('-m', '--message', multiple=True, default=None, help='a short message to hang on to')
@alerts_context
def acknowledge(actor, cmd, alertkey=None, severity='info', message=None):
    """acknowledge an alert"""

    keyword = actor.monitoring[alertkey]
    if keyword.severity != severity:
        cmd.setState(cmd.Failed, "Severity does not match alert severity")
        return None

    # it seems messages can't be passed right. geez..
    if len(message) > 0:
        msg = "".join(("{} ".format(m) for m in message))
    else:
        msg = None

    keyword.acknowledge(msg=msg)
    cmd.setState(cmd.Done, 'acknowledged')

    return False
