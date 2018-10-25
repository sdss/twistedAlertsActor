#!/usr/bin/env python
# encoding: utf-8
#
# cmds.py
#
# Created by José Sánchez-Gallego on 17 Feb 2017.


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds.help import help
from alertsActor.cmds.ping import ping
from alertsActor.cmds.version import version
from alertsActor.cmds.status import status
from alertsActor.cmds.acknowledge import acknowledge


__all__ = ('alerts_parser')


@click.group()
@click.pass_context
def alerts_parser(ctx):
    pass


alerts_parser.add_command(help)
alerts_parser.add_command(ping)
alerts_parser.add_command(version)
alerts_parser.add_command(status)
alerts_parser.add_command(acknowledge)


if __name__ == '__main__':
    alerts_parser()
