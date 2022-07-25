#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from alertsActor.tools import Timer

from alertsActor import log


class initProperty(object):
    """a dumb property to have a value"""
    def __init__(self, value):
        self.value = value


class wrapCallbacks(object):
    """Pass in keywords read from a file
       along with their alert type.
    """

    def __init__(self, alertsActor):
        self.alertsActor = alertsActor
        # self.datamodel_casts = dict()
        self.datamodel_callbacks = dict()

    async def assignCallbacks(self, keywords):

        for key, actions in keywords.items():
            # self.datamodel_casts[key] = actions['cast']

            initKeys = ('severity', 'heartbeat', 'stale')

            otherArgs = {k: actions[k] for k in actions.keys() if k not in initKeys}

            if 'heartbeat' in actions.keys():
                alertKey = actions['heartbeat'] + '.heartbeat'
                await self.alertsActor.addKey(alertKey,
                                              severity=actions['severity'],
                                              **otherArgs)
                callback = await self.pulse(alertKey=alertKey,
                                            checkAfter=actions['checkAfter'])
                self.datamodel_callbacks[key] = callback

            elif 'stale' in actions.keys():
                staleKey = key + ".stale"
                await self.alertsActor.addKey(staleKey, severity=actions['severity'],
                                              checkAfter=actions['stale'],
                                              selfClear=True,
                                              checker=staleCheck,
                                              instruments=actions['instruments'],
                                              emailAddresses=actions['emailAddresses'],
                                              emailDelay=actions.get('emailDelay', 120))

                alertKey = key
                await self.alertsActor.addKey(alertKey,
                                              severity=actions['severity'],
                                              **otherArgs)

                requireChange = actions.get("requireChange", False)

                callback = await self.updateKeyStale(key,
                                                     checkAfter=actions['stale'],
                                                     requireChange=requireChange)
                self.datamodel_callbacks[key] = callback

            else:
                alertKey = key
                cast = otherArgs["cast"]
                await self.alertsActor.addKey(alertKey,
                                              severity=actions['severity'],
                                              keyword=cast(0.0),
                                              **otherArgs)
                callback = self.updateKey(key)
                self.datamodel_callbacks[key] = callback

            if "instruments" in actions.keys():
                for i in actions["instruments"]:
                    self.alertsActor.instrumentDown[i] = False

    async def pulse(self, alertKey='NOT_SPECIFIED', checkAfter=30):
        """Update the heartbeat for a specified actor.
           The timer is restarted everytime its called, if it isn't restarted
           in time, a "dead actor" alert is raised
        """
        if alertKey not in self.alertsActor.heartbeats.keys():
            self.alertsActor.heartbeats[alertKey] = Timer()

        deadCallback = self.itsDeadJim(alertKey=alertKey)

        async def startTime(model_property):
            # called as callback, so the updated key is passed by default
            # print('pulse: ', alertKey, newKeyval[0])
            newKeyval = model_property.value
            log.info('{}: the actor said {}'.format(alertKey, newKeyval))
            # don't remember why we want the first element of the list here
            # but it shouldn't matter for heartbeat monitoring
            self.alertsActor.monitoring[alertKey].keyword = newKeyval
            self.alertsActor.monitoring[alertKey].lastalive = time.time()
            await self.alertsActor.heartbeats[alertKey].start(checkAfter, deadCallback)
            await self.alertsActor.monitoring[alertKey].checkKey()

        initProp = initProperty("init")
        await startTime(initProp)  # call now so it raises error?

        return startTime

    async def updateKeyStale(self, actorKey, checkAfter=30, requireChange=False):
        """Update the create a "stale" heartbeat for a specified actorKey.
           The timer is restarted everytime its called, if it isn't restarted
           in time, a "stale" alert is raised
        """
        staleKey = actorKey + ".stale"
        if staleKey not in self.alertsActor.heartbeats.keys():
            self.alertsActor.heartbeats[staleKey] = Timer()

        deadCallback = self.itsDeadJim(alertKey=staleKey)

        async def check(model_property, init=False):
            newKeyval = model_property.value
            if init:
                self.alertsActor.monitoring[staleKey].keyword = 0
            if requireChange:
                # val has to change to reset timer, e.g. BPR
                # definitely don't want to do this for string keys
                if abs(self.alertsActor.monitoring[staleKey].keyword - newKeyval) < 0.1:
                    return None
            # also do the heartbeat
            self.alertsActor.monitoring[staleKey].keyword = newKeyval
            self.alertsActor.monitoring[staleKey].lastalive = time.time()
            await self.alertsActor.heartbeats[staleKey].start(checkAfter, deadCallback)
            await self.alertsActor.monitoring[staleKey].checkKey()

            if init:
                return None

            log.info('{}: the actor said {}'.format(actorKey, newKeyval))
            # called as callback, so the updated key is passed by default
            self.alertsActor.monitoring[actorKey].keyword = newKeyval
            await self.alertsActor.monitoring[actorKey].checkKey()

        initProp = initProperty(-9999)
        await check(initProp, init=True)

        return check

    def updateKey(self, actorKey):
        async def check(model_property):
            newKeyval = model_property.value
            # print("---------------------------")
            # print(newKeyval)
            # print(self.alertsActor.monitoring[actorKey].msg)
            log.info('{}: the actor said {}'.format(actorKey, newKeyval))
            # print("{} {} {}".format(actorKey, newKeyval, type(newKeyval)))
            # called as callback, so the updated key is passed by default
            self.alertsActor.monitoring[actorKey].keyword = newKeyval
            await self.alertsActor.monitoring[actorKey].checkKey()

        return check

    def itsDeadJim(self, alertKey='NOT_SPECIFIED'):
        # some actor stopped outputting a keyword, raise the alarm!
        async def setActive():
            await self.alertsActor.monitoring[alertKey].setActive()

        return setActive


def staleCheck(keyState):
    """basically same as a heartbeat
    """
    if time.time() - keyState.lastalive < keyState.checkAfter:
        return "ok"
    elif time.time() - keyState.lastalive > 5*keyState.checkAfter:
        return "critical"
    else:
        return keyState.defaultSeverity
