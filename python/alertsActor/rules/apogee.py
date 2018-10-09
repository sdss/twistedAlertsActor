#!/usr/bin/env python
# encoding: utf-8
#
# apogee.py
#
# Created by John Donor on 17 Sep 2018.


# define new behavior for problems below
# will need to define one for each in callbacks

def tempAlarms(key):
    if key:
        print("tempAlarms", key, "I got called; fix me!")
        # raise alert

def vacuumAlarm(key):
    if key:
        print("vacuumAlarm", key, "I got called; fix me!")
        # raise alert

def ln2Alarm(key):
    if key:
        print("ln2Alarm", key, "I got called; fix me!")
        # raise alert

def collIndexer(key):
    if key == "Off":
        print("collIndexer", key, "I got called; fix me!")
        # raise alert

def ditherIndexer(key):
    if key == "Off":
        print("ditherIndexer", key, "I got called; fix me!")
        # raise alert