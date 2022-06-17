#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

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


async def test_is_positive_actor(rabbitmq, test_alerts):

    command = await test_alerts.send_command("test", "modify-state-int isPositive 5")
    await command

    await asyncio.sleep(2)

    command = await test_alerts.send_command("test", "modify-state-int isPositive 2")
    await command

    await asyncio.sleep(2)

    assert len(test_alerts.activeAlerts) == 0

    command = await test_alerts.send_command("test", "modify-state-int isPositive -5")
    await command

    # await asyncio.sleep(2)

    assert "test.isPositive" in test_alerts.activeAlerts


# async def test_disable(test_actor):

#     actionsFile = DATA_DIR / "testing.yaml"
#     test_alerts = await setup_test_actor(alertsActor(actionsFile=actionsFile))

#     command = await test_actor.invoke_mock_command("modify-state-int isPositive 5")
#     await command

#     command = await test_alerts.invoke_mock_command("disable test.isPositive")
#     await command

#     assert "test.isPositive" in test_alerts.disabledAlerts

#     # command = await test_actor.invoke_mock_command("modify-state-int isPositive -5")
#     # await command

#     # assert "test.isPositive" in test_alerts.activeAlerts
