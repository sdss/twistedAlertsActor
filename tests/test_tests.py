#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import asyncio

import pytest


pytestmark = [pytest.mark.asyncio]


async def test_test_actor(test_actor, test_client):

    command = await test_client.send_command("test", "modify-state-int isPositive 5")
    await command

    assert test_actor.state["isPositive"] == 5
