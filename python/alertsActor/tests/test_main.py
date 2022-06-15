#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import pathlib
import asyncio

import pytest

from clu.testing import setup_test_actor

from alertsActor.alerts_main import alertsActor

pytestmark = [pytest.mark.asyncio]

DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"

async def test_is_positive_actor(rabbitmq, test_actor, test_client):

    command = await test_client.send_command("test", "ping")
    await command
    print("TEST", command.status)

    port = rabbitmq.args["port"]

    actionsFile = DATA_DIR / "testing.yaml"
    test_alerts = alertsActor(actionsFile=actionsFile, brokerPort=port)
    await test_alerts.start()
    # await test_alerts.setupCallbacks()

    command = await test_client.send_command("test", "modify-state-int isPositive 5")
    await command
    print("modified")

    assert len(test_alerts.activeAlerts) == 0

    # command = await test_client.send_command("test", "modify-state-int isPositive -5")
    # await command

    # assert "test.isPositive" in test_alerts.activeAlerts
    await test_alerts.stop()


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
