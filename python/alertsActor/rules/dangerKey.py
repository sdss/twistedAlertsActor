#!/usr/bin/env python
# encoding: utf-8
#
# dangerKey.py
#
# Created by John Donor on 10 April 2019

import re, time
from yaml import YAMLObject


class diskCheck(YAMLObject):
    """evaluate a disk keyword
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        """The keyval is an enum ('Ok','Warning','Serious','Critical')
        and the amount of free space (GB)
        """
        keyval = keyState.keyword
        if (keyval[0]).upper() == 'OK':
            return "ok"
        elif  (keyval[0]).upper() == 'WARNING':
            return "warning"
        elif  (keyval[0]).upper() == 'SERIOUS':
            return "serious"
        elif  (keyval[0]).upper() == 'CRITICAL':
            return "critical"
        else:
            return "info"


class doNothing(object):
    """camcheck alerts can't check themselves

       dummy class to facilitate that
    """
    def __init__(self):
        pass


    def __call__(self, keyState):
        return keyState.severity


class camCheck(YAMLObject):
    """evaluate a camCheck alert
    """
    def __init__(self):
        # NEVER GETS CALLED!!!! -_-
        pass


    def generateCamCheckAlert(self, key, severity):
        key = "camCheck." + key
        if key not in self.alertsActor.monitoring:
            dumbCheck = doNothing()
            self.alertsActor.addKey(key, severity=severity, checkAfter=120,
                                    selfClear=False, checker=dumbCheck,
                                    keyword="'Reported by camCheck'")
        self.alertsActor.monitoring[key].setActive(severity)

    def __call__(self, keyState):
        keyval = keyState.keyword
        if self.alertsActor is None:
            self.alertsActor = keyState.alertsActorReference

        for k in keyval:
            if re.search(r"SP[12][RB][0-3]?CCDTemp", k):
                self.generateCamCheckAlert(k, "critical")
            elif re.search(r"SP[12]SecondaryDewarPress", k):
                self.generateCamCheckAlert(k, "critical")
            elif re.search(r"SP[12](DAQ|Mech|Micro)NotTalking", k):
                self.generateCamCheckAlert(k, "critical")
            elif re.search(r"DACS_SET", k):
                self.generateCamCheckAlert(k, "critical")
            elif re.search(r"SP[12]LN2Fill", k):
                self.generateCamCheckAlert(k, "serious")
            elif re.search(r"SP[12](Exec|Phase)Boot", k):
                self.generateCamCheckAlert(k, "serious")
            else:
                self.generateCamCheckAlert(k, "warn")

        for k in self.triggered:
            if k.split(".")[-1] not in keyval:  # b/c we know its camCheck already
                self.alertsActor.monitoring[key].severity = "ok"
                # now it can check itself and find out its cool
                # and then decide to disappear if its acknowledged, etc etc
                self.alertsActor.monitoring[key].checkKey()

        # never flag camCheck, always monitored keys
        return "ok"


class heartbeatCheck(YAMLObject):
    """check a heartbeat. 
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if time.time() - keyState.lastalive < keyState.checkAfter:
            return "ok"
        elif time.time() - keyState.lastalive > 5*keyState.checkAfter:
            return "serious"
        else:
            return "warning"


class above(YAMLObject):
    """literally: is the value too high
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if keyState.keyword > keyState.dangerVal:
            return keyState.defaultSeverity
        else:
            return "ok"


class below(YAMLObject):
    """literally: is the value too low
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if keyState.keyword < keyState.dangerVal:
            return keyState.defaultSeverity
        else:
            return "ok"


class neq(YAMLObject):
    """literally: is the value too low
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if keyState.keyword != keyState.dangerVal:
            return keyState.defaultSeverity
        else:
            return "ok"


class inList(YAMLObject):
    """is any value in the list "True", e.g. flagged
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if [k for k in keyState.keyword if k]:
            return keyState.defaultSeverity
        else:
            return "ok"

class default(object):
    """check equality to a dangerval
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if keyState.keyword == keyState.dangerVal:
            return keyState.defaultSeverity
        else:
            return "ok"
