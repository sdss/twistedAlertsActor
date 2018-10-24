#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from RO.Comm.TwistedTimer import Timer


class wrapCallbacks(object):
    """Lets try this. Pass in keywords read from a file
       along with their alert type. 
    """

    def __init__(self, alertsActor, keywords):
        # keywords read from config
        self.alertsActor = alertsActor
        self.datamodel_casts = dict()
        self.datamodel_callbacks = dict()

        for key, actions in keywords.items():
            self.datamodel_casts[key] = actions['cast']

            initKeys = ('cast', 'severity', 'heartbeat')

            otherArgs = {k: actions[k] for k in actions.keys() if k not in initKeys}

            if 'heartbeat' in actions.keys():
                alertKey = actions['heartbeat'] + '.hearbeat'
                callback = lambda _: self.pulse(actorKey=alertKey)
                self.datamodel_callbacks[key] = callback
                # print(key, actions, alertKey)

            else:
                alertKey = key
                callback = lambda _: self.updateKey(key)
                self.datamodel_callbacks[key] = callback
                # print(key, actions, alertKey)

            self.alertsActor.addKey(alertKey, severity=actions['severity'], **otherArgs)


    def pulse(self, actorKey='NOT_SPECIFIED', checkAfter=30):
        """Update the heartbeat for a specified actor
        """
        if actorKey not in self.alertsActor.heartbeats.keys():
            self.alertsActor.heartbeats[actorKey] = Timer()

        self.alertsActor.heartbeats[actorKey].start(checkAfter, lambda: self.itsDeadJim(alertKey=actorKey))
        print('pulsing {}, time {}'.format(actorKey, time.time()))


    def updateKey(self, key):
        self.alertsActor.checkKey(key)


    def itsDeadJim(self, alertKey='NOT_SPECIFIED'):
        print("its dead its dead!!! {}".format(alertKey))
        self.alertsActor.monitoring[alertKey].setActive()

