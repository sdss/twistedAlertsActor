#!/usr/bin/env python
# encoding: utf-8
#
# specialCasts.py
#
# Created by John Donor on 16 April 2019

import re, time
from yaml import YAMLObject


class firstElem(YAMLObject):
    """keep the first element
    """
    def __init__(self, cast=None):
        if cast = "int":
            self.cast = int
        elif cast = "float":
            self.cast = float
        elif cast = "bool":
            self.cast = bool
        else:
            self.cast = str

    def __call__(self, val):
        self.cast(val[0])

