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
    def __call__(self, val):
        return self.cast(val[0])
