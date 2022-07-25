#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import time
import os
import pathlib
import asyncio

import pytest
import pytest_asyncio

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


async def test_is_positive_actor(test_alerts):

    command = await test_alerts.send_command("test", "modify-state-int isPositive 5")
    await command

    command = await test_alerts.send_command("test", "modify-state-int isPositive 2")
    await command

    assert len(test_alerts.activeAlerts) == 0

    command = await test_alerts.send_command("test", "modify-state-int isPositive -5")
    await command

    assert "test.isPositive" in [t.actorKey for t in test_alerts.activeAlerts]


async def test_is_negative_actor(test_alerts):

    command = await test_alerts.send_command("test", "modify-state-int isNegative -5")
    await command

    command = await test_alerts.send_command("test", "modify-state-int isNegative -2")
    await command

    assert len(test_alerts.activeAlerts) == 0

    command = await test_alerts.send_command("test", "modify-state-int isNegative 5")
    await command

    assert "test.isNegative" in [t.actorKey for t in test_alerts.activeAlerts]


async def test_is_always_actor(test_alerts):

    command = await test_alerts.send_command("test", "modify-state-str always good")
    await command

    assert len(test_alerts.activeAlerts) == 0

    command = await test_alerts.send_command("test", "modify-state-str always bad")
    await command

    assert "test.always" in [t.actorKey for t in test_alerts.activeAlerts]


async def test_is_flagged_actor(test_alerts):
    # tests default checker

    command = await test_alerts.send_command("test", "modify-state-int flagged 0")
    await command

    assert len(test_alerts.activeAlerts) == 0

    command = await test_alerts.send_command("test", "modify-state-int flagged 1")
    await command

    assert "test.flagged" in [t.actorKey for t in test_alerts.activeAlerts]
