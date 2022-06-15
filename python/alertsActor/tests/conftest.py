#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import pathlib
import click

import pytest

from clu import AMQPActor, command_parser
from clu.testing import setup_test_actor

from alertsActor.tools import Timer

DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"


@command_parser.command()
@click.argument('keyword', type=str)
@click.argument('value', type=int)
def modify_state_int(command, keyword, value):
    actor = command.actor
    actor.state[keyword] = value
    command.finish()

@command_parser.command()
@click.argument('keyword', type=str)
@click.argument('value', type=str)
def modify_state_str(command, keyword, value):
    actor = command.actor
    actor.state[keyword] = value
    command.finish()


class TestActor(AMQPActor):
    def __init__(self, **kwargs):
        super().__init__(name='test_actor',
                         schema=DATA_DIR / "schema.json",
                         **kwargs)

        self.state = dict()
        self.timer = Timer()

        self.timer.start(1, self.writeStatus)

    def writeStatus(self):
        for keyword, value in self.state.items():
            self.write(message_code="i",
                       message={keyword: value})
        self.timer.start(1, self.writeStatus)


@pytest.fixture
async def test_actor(rabbitmq, event_loop):

    port = rabbitmq.args["port"]

    actor = TestActor(port=port)
    await setup_test_actor(actor)

    yield actor
