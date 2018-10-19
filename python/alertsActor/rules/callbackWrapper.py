#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from alertsActor.rules import apogee


class wrapCallbacks(object):
    """Lets try this. Pass in keywords read from a file
       along with their alert type. 
    """

    def __init__(self, alertsActor, keywords):
        # keywords of the form {key: (cast, action)}
        self.alertsActor = alertsActor
        self.datamodel_casts = dict()
        self.datamodel_callbacks = dict()

        # this feels clumsy, but it should work...
        translate = {"pulse": self.pulse,
                     "warning": self.warning,
                     "serious": self.serious,
                     "critical": self.critical,
                     "str": str}

        for k, v in keywords.items():
            assert len(v) == 2, 'must specify an alert action and cast for {}'.format(k)
            self.datamodel_casts[k] = translate[v[0]]
            self.datamodel_callbacks[k] = translate[v[1]]


    def pulse(self, actor):
        """Update the heartbeat for a specified actor
        """
        self.alertsActor.heartbeats['actor'] = time.time()
        print('pulse')


    def warning(self, key):
        """Raise a warning alert
        """
        self.alertsActor.raiseAlert(name, cause, "warning")
        # print some stuff?


    def serious(self, key):
        """Raise a serious alert
        """
        self.alertsActor.raiseAlert(name, cause, "serious")


    def critical(self, key):
        """Raise a critical alert
        """
        self.alertsActor.raiseAlert(name, cause, "critical")
        # EMAIL EVERYBODY!!
        # make noise?

# e.g.
datamodel_callbacks = {"apogee.ditherPosition": apogee.pulse,  # used for heartbeat  # "apogee"
                       "apogee.tempAlarms": apogee.tempAlarms,  # "key"
                       "apogee.vacuumAlarm": apogee.vacuumAlarm,  # "key"
                       "apogee.ln2Alarm": apogee.ln2Alarm,  # "key"
                       "apogee.collIndexer": apogee.collIndexer,  # "key"
                       "apogee.ditherIndexer": apogee.ditherIndexer,}  # "key"
# probably more

datamodel_casts = {"apogee.ditherPosition": str,  # used for heartbeat  # "apogee"
                   "apogee.tempAlarms": str,  # "key"
                   "apogee.vacuumAlarm": str,  # "key"
                   "apogee.ln2Alarm": str,  # "key"
                   "apogee.collIndexer": str,  # "key"
                   "apogee.ditherIndexer": str,}  # "key"
