#!/usr/bin/env python
# encoding: utf-8
#
# callbacks.py
#
# Created by John Donor on 9 Mar 2018.

import time
from alertsActor.rules import apogee


def parseAndPassArgs(wrapper, keywords):
    """remove 'cast' and action from 'args' list
       execute relevant args to function
       necessary to delay evaluation of function, I think
    """
    passedArgs = {k: keywords[k] for k in keywords.keys() if k not in ('cast', 'action')}
    # return fn(**passedArgs)

    # this feels clumsy, but it should work...
    translate = {"pulse": wrapper.pulse,
                 "warning": wrapper.warning,
                 "serious": wrapper.serious,
                 "critical": wrapper.critical,
                 "str": str}

    print("parsing: ", keywords)
    # print(translate[keywords['cast']], translate[keywords['action']](**passedArgs))

    cast = translate[keywords['cast']]

    # when callback is called, it is given an argument. maybe ask Jose?
    # meanwhile: "_" means expect a variable, and implicitly ignore it, more or less
    # so this line defines an anonomymous function that is a copy of keywords['action']
    # with the appropriate **kwargs, that can be called as needed
    callback = lambda _: translate[keywords['action']](**passedArgs)

    print(cast, callback)

    return cast, callback


class wrapCallbacks(object):
    """Lets try this. Pass in keywords read from a file
       along with their alert type. 
    """

    def __init__(self, alertsActor, keywords):
        # keywords of the form {key: (cast, action)}
        self.alertsActor = alertsActor
        self.datamodel_casts = dict()
        self.datamodel_callbacks = dict()

        for k, v in keywords.items():
            assert len(v) >= 2, 'must specify an alert action and cast for {}'.format(k)
            # self.datamodel_casts[k] = translate[v['cast']]
            # self.datamodel_callbacks[k] = lambda: parseAndPassArgs(translate[v['action']], v)
            self.datamodel_callbacks[k], self.datamodel_casts[k] = parseAndPassArgs(self, v)


    def pulse(self, actor='NOT_SPECIFIED'):
        """Update the heartbeat for a specified actor
        """
        self.alertsActor.heartbeats[actor] = time.time()
        print('pulsing {}, time {}'.format(actor, self.alertsActor.heartbeats[actor]))


    def warning(self):
        """Raise a warning alert
        """
        self.alertsActor.raiseAlert(name, cause, "warning")
        # print some stuff?


    def serious(self):
        """Raise a serious alert
        """
        self.alertsActor.raiseAlert(name, cause, "serious")


    def critical(self):
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
