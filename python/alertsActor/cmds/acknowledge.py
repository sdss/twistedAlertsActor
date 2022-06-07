#!/usr/bin/env python
# encoding: utf-8
#
# acknowledge.py
#

import click

from alertsActor.cmds import parser


@parser.command()
@click.argument('alertkey', type=str, required=True,
                help='alert to disable')
@click.argument('severity', required=True, default='info',
                type=click.Choice(['ok', 'info', 'apogeediskwarn', 'warn',
                                   'serious', 'critical']))
@click.option('-m', '--message', multiple=True, default=None,
              help='a short message to hang on to')
@click.option('-u', '--user', type=str, default=None,
              help='user acknowledging this alert')
async def acknowledge(command, alertkey=None, severity='info', message=None, user=None):
    """acknowledge an alert"""

    if user is None:
        user = ""

    actor = command.actor

    keyword = actor.monitoring[alertkey]

    if keyword.severity != severity:
        command.fail(error="Severity does not match alert severity")
        return None

    # it seems messages can't be passed right. geez..
    if len(message) > 0:
        msg = "".join(("{} ".format(m) for m in message))
    else:
        msg = None

    await keyword.acknowledge(msg=msg, acknowledgedBy=user)
    await actor.broadcastAll()

    return command.finish()
