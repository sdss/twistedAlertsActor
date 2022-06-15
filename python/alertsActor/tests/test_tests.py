#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import asyncio

import pytest


pytestmark = [pytest.mark.asyncio]


async def test_test_actor(test_actor):

    command = await test_actor.invoke_mock_command("modify-state-int isPositive 5")
    await command

    assert test_actor.state["isPositive"] == 5
