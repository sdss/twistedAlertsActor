#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import asyncio

import pytest


pytestmark = [pytest.mark.asyncio]


async def test_test_actor(test_actor):

	test_actor.invoke_command("modify_state_int isPositive 5")

	assert test_actor.status["isPositive"] == 5
