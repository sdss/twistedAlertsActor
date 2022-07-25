#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import pathlib
import asyncio

import pytest
import pytest_asyncio

from clu import AMQPClient
from clu.testing import setup_test_actor

from alertsActor.alerts_main import alertsActor

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


async def test_disable(test_client):
    cmd = await test_client.send_command('alerts', 'get_schema')
    await cmd

    command = await test_client.send_command("test", "modify-state-int isPositive 5")
    await command

    command = await test_client.send_command("alerts", "disable test.isPositive")
    await command

    command = await test_client.send_command("test", "modify-state-int isPositive -5")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestIspositive"].value["disabled"]

    command = await test_client.send_command("alerts", "enable test.isPositive")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestIspositive"].value["disabled"]
    assert test_client.models["alerts"]["alertTestIspositive"].value["active"]


async def test_instrument(test_client):
    cmd = await test_client.send_command('alerts', 'get_schema')
    await cmd

    command = await test_client.send_command("alerts", "instrumentState test down")
    await command

    command = await test_client.send_command("test", "modify-state-int isPositive -5")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestIspositive"].value["disabled"]

    command = await test_client.send_command("alerts", "instrumentState test up")
    await command

    command = await test_client.send_command("test", "modify-state-int isPositive -5")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert not test_client.models["alerts"]["alertTestIspositive"].value["disabled"]
    assert test_client.models["alerts"]["alertTestIspositive"].value["active"]


async def test_acknowledge(test_client):
    cmd = await test_client.send_command('alerts', 'get_schema')
    await cmd

    command = await test_client.send_command("test", "modify-state-int isPositive -5")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestIspositive"].value["active"]

    # ack and unack just to check and for coverage
    command = await test_client.send_command("alerts", "acknowledge test.isPositive critical")
    await command

    assert test_client.models["alerts"]["alertTestIspositive"].value["acknowledged"]

    command = await test_client.send_command("alerts", "unacknowledge test.isPositive critical")
    await command

    assert not test_client.models["alerts"]["alertTestIspositive"].value["acknowledged"]

    # that was fun, back to useful stuff

    command = await test_client.send_command("test", "modify-state-int isPositive 5")
    await command

    command = await test_client.send_command("alerts", "status")
    await command

    assert test_client.models["alerts"]["alertTestIspositive"].value["active"]

    command = await test_client.send_command("alerts", "acknowledge test.isPositive serious")
    await command

    assert command.status.did_fail

    command = await test_client.send_command("alerts", "acknowledge test.isPositive critical")
    await command

    assert not test_client.models["alerts"]["alertTestIspositive"].value["active"]
