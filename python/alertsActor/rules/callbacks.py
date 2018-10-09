#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from alertsActor.rules import apogee

# keep track of all heartbeats here. 
# might need to move to an init? should be ok...
heartbeats = dict()

def pulse(actor):
    '''updates the heartbeat for an actor'''
    print(actor)
    heartbeats[actor] = time.time()
    print('pulsing!')
    print(actor)

# how do i get those keys? its easy; check...
# e.g.
datamodel_callbacks = {"apogee.ditherPosition": pulse,  # used for heartbeat  # "apogee"
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
