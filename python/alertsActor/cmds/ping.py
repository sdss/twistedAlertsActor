#!/usr/bin/env python
# encoding: utf-8
#
# ping.py
#
# Created by José Sánchez-Gallego on 19 Mar 2017.


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from alertsActor.cmds import alerts_context


__all__ = ('ping')


@click.command()
@alerts_context
def ping(actor, cmd):
    """Pings the actor."""

    cmd.setState(cmd.Done, "I'm not dead yet!")
    print(actor.heartbeats)

    return False
