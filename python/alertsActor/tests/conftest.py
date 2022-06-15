#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import pathlib
import click

import pytest_asyncio

from clu import AMQPActor, AMQPClient
from clu.testing import setup_test_actor

from clu.parsers.click import CluGroup, ping

from alertsActor.tools import Timer

DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"


@click.group(cls=CluGroup)
def parser(*args):
    pass

parser.add_command(ping)

@parser.command()
@click.argument('keyword', type=str)
@click.argument('value', type=int)
def modify_state_int(command, keyword, value):
    actor = command.actor
    actor.state[keyword] = value

    command.finish()

@parser.command()
@click.argument('keyword', type=str)
@click.argument('value', type=str)
def modify_state_str(command, keyword, value):
    actor = command.actor
    actor.state[keyword] = value
    command.finish()


class TestActor(AMQPActor):
    parser = parser
    def __init__(self, **kwargs):
        super().__init__(name='test',
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


@pytest_asyncio.fixture
async def test_actor(rabbitmq, event_loop):

    port = rabbitmq.args["port"]

    actor = TestActor(port=port)
    await actor.start()

    yield actor

    await actor.stop()


@pytest_asyncio.fixture
async def test_client(rabbitmq, event_loop):

    port = rabbitmq.args["port"]

    client = AMQPClient(name="test_client", port=port)
    await client.start()

    yield client

    await client.stop()