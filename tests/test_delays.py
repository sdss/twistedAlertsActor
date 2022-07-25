#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import time
import os
import pathlib
import asyncio

import pytest
import pytest_asyncio

from clu import AMQPClient
from clu.testing import setup_test_actor

from alertsActor.alerts_main import alertsActor
from alertsActor.tools import wrapBlocking

pytestmark = [pytest.mark.asyncio]

DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"


@pytest_asyncio.fixture
async def test_alerts(rabbitmq, event_loop, test_actor):

    port = rabbitmq.args["port"]

    actionsFile = DATA_DIR / "testing.yaml"
    test_alerts = alertsActor(actionsFile=actionsFile, port=port)
    await test_alerts.start()

    yield test_alerts

    await test_alerts.stop()


@pytest_asyncio.fixture
async def test_client(rabbitmq, event_loop, test_alerts):

    port = rabbitmq.args["port"]

    client = AMQPClient(name="test_client", port=port, models=["alerts"])
    await client.start()

    yield client

    await client.stop()


async def test_heartbeat(test_client):
    cmd = await test_client.send_command('alerts', 'get_schema')
    await cmd

    command = await test_client.send_command("test", "modify-state-int heartbeat 0")
    await command

    # wait short time and output keyword to test normal, non-dead behavior
    await wrapBlocking(time.sleep, 0.5)

    command = await test_client.send_command("test", "modify-state-int heartbeat 0")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestHeartbeat"].value["active"]

    await wrapBlocking(time.sleep, 3)

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestHeartbeat"].value["active"]

    command = await test_client.send_command("test", "modify-state-int heartbeat 0")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestHeartbeat"].value["active"]


async def test_stale(test_client):
    cmd = await test_client.send_command('alerts', 'get_schema')
    await cmd

    command = await test_client.send_command("test", "modify-state-int goesStale 2")
    await command

    # wait short time and output keyword to test normal, non-dead behavior
    await wrapBlocking(time.sleep, 0.5)

    command = await test_client.send_command("test", "modify-state-int goesStale 3")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestGoesStaleStale"].value["active"]

    for i in range(3):
        await wrapBlocking(time.sleep, 1)

        command = await test_client.send_command("test", "modify-state-int goesStale 3")
        await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestGoesStaleStale"].value["active"]

    command = await test_client.send_command("test", "modify-state-int goesStale 2")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestGoesStaleStale"].value["active"]
