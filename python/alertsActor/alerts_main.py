#!/usr/bin/env python
# encoding: utf-8
#
# alerts_main.py
#


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import json
# import yaml
import sys
import traceback

import time

from click.testing import CliRunner

from RO.StringUtil import strFromException
from RO.Comm.TwistedTimer import Timer
from twistedActor import BaseActor, CommandError, UserCmd

from alertsActor import __version__, alertActions
from alertsActor.cmds.cmd_parser import alerts_parser
from alertsActor.logger import log

from alertsActor.rules import callbackWrapper, mail, sms


class alertsActor(BaseActor):
    """the actor"""

    def __init__(self, config, **kwargs):

        self.cmdParser = alerts_parser
        self.config = config

        super(alertsActor, self).__init__(**kwargs)

        # a dictionary of actor keys we're watching
        self.monitoring = dict()

        # keep track of downed instruments
        # since its either up or down, make boolean
        # UP = True, DOWN = False
        self.instrumentUp = dict()

        # keep track of heartbeats
        self.heartbeats = dict()

        self.callbacks = callbackWrapper.wrapCallbacks(self, alertActions)

        self.connectHub('localhost', datamodel_casts=self.callbacks.datamodel_casts,
                                     datamodel_callbacks=self.callbacks.datamodel_callbacks)

        log.info('starting alertsActor actor version={!r} in port={}'
                 .format(__version__, kwargs['userPort']))

        # Sets itself as the default actor to write to when logging.
        log.set_actor(self)


    def addKey(self, key, severity, **kwargs):
        self.monitoring[key] = keyState(self, actorKey=key, severity=severity, **kwargs)


    @property
    def activeAlerts(self):
        active = []
        for k, a in self.monitoring.items():
            if a.active:
                active.append(a)

        return active


    @property
    def disabledAlerts(self):
        disabled = []
        for k, a in self.monitoring.items():
            if a.disabled:
                disabled.append(a)

        return disabled


    def broadcastActive(self):
        activeMessage = "activeAlerts{}".format(("=" if len(self.activeAlerts) else "")) +\
                       ", ".join(["{}".format(a.actorKey) for a in self.activeAlerts])
        self.writeToUsers("i", activeMessage)


    def broadcastDisabled(self):
        disabledMessage = "disabledAlertRules{}".format(("=" if len(self.disabledAlerts) else "")) +\
                       ", ".join(['"({}, {}, {})"'.format(a.actorKey, a.severity, a.disabledBy)
                                  for a in self.disabledAlerts])
        self.writeToUsers("i", disabledMessage)


    def broadcastAll(self):
        for a in self.activeAlerts:
            a.dispatchAlertMessage()


    def broadcastInstruments(self):
        instruments = list()
        for k, a in self.monitoring.items():
            if a.instrument is not None and not a.instrument in instruments:
                instruments.append(a.instrument)
        down = [i for i in instruments if not self.instrumentUp[i]]
        self.writeToUsers("i", 'instrumentNames={}'.format(",".join(instruments)))
        self.writeToUsers("i", 'downInstruments={}'.format(",".join(down)))

    @property
    def hubModel(self):
        # keeps a running data model of keywords coming from the hub
        # allows callbacks on updates

        # this may need to be more careful... test!
        if self.hub is None:
            print("no hub connection, reconnecting!")
            self.connectHub('localhost', datamodel_casts=self.callbacks.datamodel_casts,
                                         datamodel_callbacks=self.callbacks.datamodel_callbacks)

        return self.hub.datamodel


    def parseAndDispatchCmd(self, cmd):
        """Dispatch the user command. Stolen from BMO."""

        def test_cmd(args):
            result = CliRunner().invoke(alerts_parser, args)
            if result.exit_code > 0:
                # If code > 0, there was an error. We fail the command and inform the users.
                textMsg = result.output
                for line in textMsg.splitlines():
                    line = json.dumps(line).replace(';', '')
                    cmd.writeToUsers('w', 'text={0}'.format(line))
                cmd.setState(cmd.Failed)
                return False
            else:
                if '--help' in args:
                    # If help was in the args, we just want to print the usage to the users.
                    textMsg = result.output
                    for line in textMsg.splitlines():
                        line = json.dumps(line).replace(';', '')
                        cmd.writeToUsers('w', 'text={0}'.format(line))
                    cmd.setState(cmd.Done)
                    return False

                return True

        if not cmd.cmdBody:
            # echo to show alive
            self.writeToOneUser(":", "", cmd=cmd)
            return

        cmd.setState(cmd.Running)

        try:
            # stui wants to pass keyword args, parse doesn't support that
            # this is definitely bad form, but we're trying not to change
            # stui yet
            # click is case sensetive and requires lower-case -_-
            args = [a.split("=")[-1].lower() for a in cmd.cmdBody.split()]
            result = test_cmd(args)
            if result is False:
                return
            alerts_parser(args, obj=dict(actor=self, cmd=cmd))
        except CommandError as ee:
            cmd.setState('failed', textMsg=strFromException(ee))
            return
        except Exception as ee:
            sys.stderr.write('command {0!r} failed\n'.format(cmd.cmdStr))
            traceback.print_exc(file=sys.stderr)
            textMsg = strFromException(ee)
            hubMsg = 'Exception={0}'.format(ee.__class__.__name__)
            cmd.setState("failed", textMsg=textMsg, hubMsg=hubMsg)
        except BaseException:
            # This catches the SystemExit that Click insists in returning.
            pass

def ack(acknowledged):
    if acknowledged:
        return "ack"
    else:
        return "noack"


def enabled(disabled):
    if disabled:
        return "disabled"
    else:
        return "enabled"

class keyState(object):
    '''Keep track of the state of each actor.key'''

    def __init__(self, alertsActor, actorKey='oop.forgot', severity='info', keyword="", dangerVal=None,
                 selfClear=False, emailAddresses=['fail@fail.com'], **kwargs):
        self.alertsActorReference = alertsActor
        self.triggeredTime = None
        self.actorKey = actorKey
        self.keyword = keyword
        self.lastalive = time.time()  # updated for heartbeats
        self.active = False
        self.disabled = False
        self.disabledBy = -1
        self.defaultSeverity = severity
        self.severity = 'info'
        self.acknowledged = False
        self.acknowledgeMsg = ""
        self.acknowledger = -1
        self.dangerVal = dangerVal  # value on which to raise alert
        self.checkMe = Timer()
        self.selfClear = selfClear
        self.sleepTime = 10
        self.emailAddresses = emailAddresses
        self.smtpclient = "localhost:1025"

        if "instrument" in kwargs:
            self.instrument = kwargs.get("instrument")
        else:
            self.instrument = None

        if "checkAfter" in kwargs:
            self.checkAfter = kwargs.get("checkAfter")

        assert self.severity in ['ok', 'info', 'apogeediskwarn', 'warn', 'serious', 'critical'], "severity level not allowed"


    @property
    def msg(self):
        return "alert={actorkey}, {severity}, {keyword}, {enable}, {acknowledged}, {acknowledger}".format(actorkey=self.actorKey,
               keyword=self.keyword, severity=self.severity, enable=enabled(self.disabled),
               acknowledged=ack(self.acknowledged), acknowledger=self.acknowledger)


    @property
    def instDown(self):
        if self.instrument is None:
            return False

        if self.alertsActorReference.instrumentUp[self.instrument]:
            return False
        else:
            return True


    def setActive(self):
        # something cause a problem, do stuff
        self.acknowledged = False # clear anything from old alert
        self.active = True
        self.severity = self.defaultSeverity
        self.triggeredTime = time.time()
        self.checkMe.start(self.sleepTime, self.reevaluate)

        if self.instDown:
            self.disable(self.severity , 0)
            print("!!{} instrument down, no alert!!".format(self.actorKey))
            return None

        self.dispatchAlertMessage()
        self.sendEmail()


    def clear(self):
        # everything good, back to normal
        self.active = False
        self.checkMe = Timer()
        self.severity = 'info'

        self.alertsActorReference.broadcastActive()
        self.alertsActorReference.broadcastDisabled()
        self.alertsActorReference.broadcastAll()


    def acknowledge(self, msg=None, acknowledgedBy=None, unack=False):
        if msg is not None:
            self.acknowledgeMsg += msg + ";" # so we can add many... I guess?

        if acknowledgedBy is not None:
            self.acknowledger = acknowledgedBy

        if unack:
            self.acknowledged = False
        else:
            self.acknowledged = True

        self.dispatchAlertMessage()


    def reevaluate(self):
        # at some point this will presumably raise alert level?
        # possibly send email? Or only send email for critical? Or...
        self.checkKey()
        if not self.active:
            return

        if self.acknowledged:
            # keep checking myself until I go away
            self.checkMe.start(self.sleepTime, self.reevaluate)
            return

        if self.disabled:
            self.checkMe.start(self.sleepTime, self.reevaluate)
            return

        self.dispatchAlertMessage()
        self.checkMe.start(self.sleepTime, self.reevaluate)


    def sendEmail(self):
        # notify over email
        mail.sendEmail(self, self.smtpclient)
        # and sms?
        # sms.sendSms(self)  # just a reminder for later , phoneNumbers=["+18177733196"])


    def dispatchAlertMessage(self):
        # write an alert to users

        if self.severity == 'critical':
            broadcastSeverity = 'e'
        elif self.severity == 'warn' or self.severity == 'serious':
            broadcastSeverity = 'w'
        else:
            broadcastSeverity = 'i'

        self.alertsActorReference.writeToUsers(broadcastSeverity, self.msg)


    def checkKey(self):
        # check key, should be called when keyword changes

        if "heartbeat" in self.actorKey:
            if time.time() - self.lastalive < self.checkAfter:
                self.clear()
            return None

        if self.keyword == self.dangerVal:
            if self.active:
                # we already know
                return None
            else:
                self.setActive()
        elif self.selfClear:
            # if the key changed and its good, then the alert is gone, right?
            # or possibly key changed and its just not bad? this is still fine to do
            self.clear()


    def disable(self, disabledBy):
        self.disabled = True
        self.disabledBy = disabledBy

        # self.active = False

        # probably do some more stuff


    def enable(self):
        self.disabled = False
        self.checkKey()
