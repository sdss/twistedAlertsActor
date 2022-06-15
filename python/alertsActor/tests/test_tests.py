#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import asyncio

import pytest


pytestmark = [pytest.mark.asyncio]


async def test_test_actor(test_actor):

	test_actor.invoke_mock_command("modify_state_int isPositive 5")

	print("\n \n ACTOR STATE", test_actor.state)

	assert test_actor.state["isPositive"] == 5
