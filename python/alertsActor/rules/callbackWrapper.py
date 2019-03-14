#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from RO.Comm.TwistedTimer import Timer


class wrapCallbacks(object):
    """Pass in keywords read from a file
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
                alertKey = actions['heartbeat'] + '.heartbeat'
                callback = self.pulse(alertKey=alertKey, checkAfter=actions['checkAfter'])
                self.datamodel_callbacks[key] = callback

            else:
                alertKey = key
                callback = self.updateKey(key)
                self.datamodel_callbacks[key] = callback

            if "instrument" in actions.keys():
                alertsActor.instrumentUp[actions["instrument"]] = True

            self.alertsActor.addKey(alertKey, severity=actions['severity'], **otherArgs)


    def pulse(self, alertKey='NOT_SPECIFIED', checkAfter=30):
        """Update the heartbeat for a specified actor.
           The timer is restarted everytime its called, if it isn't restarted 
           in time, a "dead actor" alert is raised
        """
        if alertKey not in self.alertsActor.heartbeats.keys():
            self.alertsActor.heartbeats[alertKey] = Timer()

        deadCallback = self.itsDeadJim(alertKey=alertKey)
        def startTime(newKeyval):
            # called as callback, so the updated key is passed by default
            print('pulse: ', alertKey, newKeyval)
            self.alertsActor.monitoring[alertKey].keyword = newKeyval
            self.alertsActor.heartbeats[alertKey].start(checkAfter, deadCallback)

        return startTime


    def updateKey(self, actorKey):
        def check(newKeyval):
            # called as callback, so the updated key is passed by default
            self.alertsActor.monitoring[alertKey] = newKeyval
            self.alertsActor.monitoring[alertKey].checkKey()

        return check


    def itsDeadJim(self, alertKey='NOT_SPECIFIED'):
        # some actor stopped outputting a keyword, raise the alarm!
        def setActive():
            self.alertsActor.monitoring[alertKey].setActive()
        
        return setActive

