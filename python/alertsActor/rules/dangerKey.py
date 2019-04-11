#!/usr/bin/env python
# encoding: utf-8
#
# dangerKey.py
#
# Created by John Donor on 10 April 2019

import time
from yaml import YAMLObject

__all__ = ("diskCheck", "heartbeatCheck")


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
            return "warning"


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
        if keyState.keyword > keyState.dangerVal[0]:
            return keyState.defaultSeverity
        else:
            return "ok"


class below(YAMLObject):
    """literally: is the value too low
    """
    def __init__(self):
        pass

    def __call__(self, keyState):
        if keyState.keyword < keyState.dangerVal[0]:
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
