#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import pytest_asyncio

import pytest

from clu import AMQPClient


pytestmark = [pytest.mark.asyncio]


@pytest_asyncio.fixture
async def test_client(rabbitmq, event_loop):

    port = rabbitmq.args["port"]

    client = AMQPClient(name="test_client", port=port)
    await client.start()

    yield client

    await client.stop()


async def test_test_actor(test_actor, test_client):

    command = await test_client.send_command("test", "modify-state-int isPositive 5")
    await command

    assert test_actor.state["isPositive"] == 5
