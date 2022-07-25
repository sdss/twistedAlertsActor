#!/usr/bin/env python
# encoding: utf-8
#
# alerts_main.py
#

import os
import time
import yaml

from clu.actor import AMQPActor
from clu.client import AMQPClient

from alertsActor import __version__, alertActions, config
from alertsActor.cmds import parser as alerts_parser
from alertsActor import log
from alertsActor.rules import callbackWrapper, mail, dangerKey
from alertsActor.tools import Timer, wrapBlocking


class alertsActor(AMQPActor):
    """the actor"""

    parser = alerts_parser

    def __init__(self, actionsFile=None, **kwargs):

        # a dictionary of actor keys we're watching
        self.monitoring = dict()

        # keep track of downed instruments
        # since its either up or down, make boolean
        # UP = False, DOWN = True
        self.instrumentDown = dict()

        # keep track of heartbeats
        self.heartbeats = dict()

        self.callbacks = callbackWrapper.wrapCallbacks(self)

        # actionsFile = kwargs.get("actionsFile", None)
        if actionsFile is not None:
            # mostly for testing
            try:
                alertActions = yaml.load(open(actionsFile), Loader=yaml.UnsafeLoader)
            except AttributeError:
                alertActions = yaml.load(open(actionsFile))

        self.alertActions = alertActions

        if "schema" not in kwargs:
            kwargs["schema"] = os.path.join(
                os.path.dirname(__file__),
                "etc/schema.json",
            )

        self.monitoredActors = list()
        for key in self.alertActions:
            actor = key.split(".")[0]
            if actor not in self.monitoredActors:
                self.monitoredActors.append(actor)

        super().__init__(name="alerts",
                         models=self.monitoredActors,
                         log=log,
                         **kwargs)

    async def setupCallbacks(self):
        """create callbacks, seperate from start because testing overrides start"""
        await self.callbacks.assignCallbacks(self.alertActions)

        for m in self.monitoredActors:
            cmd = await self.send_command(m, "ping")
            await cmd

        for key, value in self.callbacks.datamodel_callbacks.items():
            actor, keyword = key.split(".")
            self.models[actor][keyword].register_callback(value)

    async def start(self):
        await super().start()
        await self.setupCallbacks()

    async def addKey(self, key, severity, **kwargs):
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

    async def broadcastActive(self, command=None):
        for a in self.activeAlerts:
            await a.dispatchAlertMessage(command=command)

    async def broadcastDisabled(self, command=None):
        for a in self.disabledAlerts:
            await a.dispatchAlertMessage(command=command)

    async def broadcastAll(self, command=None):
        # await self.broadcastActive(command=command)
        # await self.broadcastDisabled(command=command)

        for k, a in self.monitoring.items():
            await a.dispatchAlertMessage(command=command)

        active = ", ".join([str(a.actorKey) for a in self.activeAlerts])
        self.write(message_code="i", message={"activeAlerts": active})
        if command:
            command.write(message_code="i", message={"activeAlerts": active})

    async def broadcastInstruments(self, command=None):
        for name, down in self.instrumentDown.items():
            instName = "instrumentStatus" + name.capitalize()
            self.write(message_code="i",
                       message={instName: {"name": name,
                                           "disabled": down}})
            if command:
                command.write(message_code="i",
                              message={instName: {"name": name,
                                                  "disabled": down}})

    @property
    def hubModel(self):
        # keeps a running data model of keywords coming from the hub
        # allows callbacks on updates

        return self.models


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


def parseKey(keyVal):
    """readable keyVal"""
    if type(keyVal) is list:
        return "[{}]".format("".join(["{}.".format(i) for i in keyVal]))
    else:
        return str(keyVal)


class keyState(object):
    '''Keep track of the state of each actor.key'''

    def __init__(self, alertsActor, actorKey='oop.forgot', keyword="",
                 emailAddresses=None, **kwargs):
        self.alertsActorReference = alertsActor
        self.triggeredTime = "not active"
        self.actorKey = actorKey
        self.keyword = keyword
        self.lastalive = time.time()  # updated for heartbeats
        self.active = False
        self.disabled = False
        self.disabledBy = -1
        self.severity = "ok"
        self.acknowledged = False
        self.acknowledgeMsg = ""
        self.acknowledger = ""
        self.checkMe = Timer()
        self.emailTimer = Timer()
        self.emailAddresses = emailAddresses
        self.emailSent = False
        self.smtpclient = config["email"]["mailClient"]
        self._camelCase = None

        # kwargs, second argument is the default
        self.defaultSeverity = kwargs.get("severity", "info")
        self.dangerVal = kwargs.get("dangerVal", None)
        self.selfClear = kwargs.get("selfClear", False)
        self.instruments = kwargs.get("instruments", None)
        self.checkAfter = kwargs.get("checkAfter", 120)
        self.checker = kwargs.get("checker", dangerKey.default())
        self.emailDelay = kwargs.get("emailDelay", self.checkAfter)

        assert self.severity in ['ok', 'info', 'apogeediskwarn', 'warn', 'serious', 'critical'], "severity level not allowed"

    @property
    def camelCase(self):
        if self._camelCase is None:
            pieces = self.actorKey.split(".")
            self._camelCase = "".join([p.capitalize() for p in pieces])
        return self._camelCase

    def formatOutput(self):
        if "heartbeat" in self.actorKey:
            instring = "at {time}; last seen {diff} sec ago".format(time=self.triggeredTime,
                                                                    diff=int(time.time()-self.lastalive))
        elif "stale" in self.actorKey:
            instring = "at {time}; no change for {diff} sec, with {keyword}".format(time=self.triggeredTime,
                                                                    diff=int(time.time()-self.lastalive),
                                                                    keyword=parseKey(self.keyword))
        else:
            instring = 'at {time}; found {keyword}'.format(keyword=parseKey(self.keyword), time=self.triggeredTime)
        return instring

    @property
    def msg(self):
        # return "alert={actorKey}, {severity}, {value}, {enable}, {acknowledged}, {acknowledger}".format(
        #        actorKey=self.actorKey, value=self.formatOutput(),
        #        severity=self.severity, enable=enabled(self.disabled), acknowledged=ack(self.acknowledged),
        #        acknowledger=self.acknowledger)

        formatted = {"keyword": self.actorKey,
                     "summary": self.formatOutput(),
                     "timeStamp": self.triggeredTime,
                     "severity": self.severity,
                     "disabled": self.disabled,
                     "active": self.active,
                     "acknowledged": self.acknowledged,
                     "acknowledger": self.acknowledger}

        return formatted

    @property
    def instDown(self):
        if self.instruments is None:
            return False

        for i in self.instruments:
            if self.alertsActorReference.instrumentDown[i]:
                return True
        else:
            return False

    def stampTime(self):
        self.triggeredTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    async def setActive(self, severity=None):
        # something cause a problem, do stuff
        self.acknowledged = False  # clear anything from old alert
        self.active = True
        if severity is None:
            self.severity = self.defaultSeverity
        else:
            self.severity = severity
        self.stampTime()
        await self.checkMe.start(self.checkAfter, self.reevaluate)

        if self.instDown:
            await self.disable()
            log.info("NO ALERT: {} instrument down, no alert!!".format(self.actorKey))
            return None

        await self.dispatchAlertMessage()
        # give the alert a chance to clear before emailing everyone
        await self.emailTimer.start(self.emailDelay, self.sendEmail)

    async def clear(self):
        # everything good, back to normal
        self.active = False
        await self.checkMe.cancel()
        # self.checkMe = Timer()
        await self.emailTimer.cancel()
        # self.emailTimer = Timer()
        self.severity = 'ok'
        self.triggeredTime = "not active"
        self.emailSent = False

        await self.alertsActorReference.broadcastActive()
        await self.alertsActorReference.broadcastDisabled()
        await self.alertsActorReference.broadcastAll()

    async def acknowledge(self, msg=None, acknowledgedBy=None, unack=False, command=None):
        if msg is not None:
            self.acknowledgeMsg += msg + ";" # so we can add many... I guess?

        if acknowledgedBy is not None:
            self.acknowledger = acknowledgedBy
        else:
            self.acknowledger = ""

        if unack:
            self.acknowledged = False
        else:
            self.acknowledged = True

        await self.checkKey()

        await self.dispatchAlertMessage(command=command)

    async def reevaluate(self):
        # at some point this will presumably raise alert level?
        # possibly send email? Or only send email for critical? Or...
        # if self.alertsActorReference.hub.didFail:
        #     self.alertsActorReference.reconnect()
        check = await self.checkKey()
        print("evaluated {} found {} default {}".format(self.actorKey, check, self.defaultSeverity))
        if check != self.severity:
            # something changed, treat it like new alert
            self.severity = check
            await self.acknowledge(acknowledgedBy="", unack=True)
            await self.dispatchAlertMessage()
        if not self.active:
            return

        if self.acknowledged:
            # keep checking myself until I go away
            await self.checkMe.start(self.checkAfter, self.reevaluate)
            return

        if self.disabled:
            await self.checkMe.start(self.checkAfter, self.reevaluate)
            return

        await self.dispatchAlertMessage()
        await self.checkMe.start(self.checkAfter, self.reevaluate)

    async def sendEmail(self):
        # notify over email
        if self.emailAddresses is None or self.disabled:
            return

        if self.emailSent:
            # I don't think this should happen but it seems to...
            log.info("Tried to send extra email for {}".format(self.actorKey))
            return

        if not self.active:
            log.warn("Tried to send email after clear for {}".format(self.actorKey))
            return

        await wrapBlocking(mail.sendEmail, self, self.smtpclient)
        # and sms?
        # sms.sendSms(self)  # just a reminder for later , phoneNumbers=["+18177733196"])
        self.emailSent = True

    async def dispatchAlertMessage(self, command=None):
        # write an alert to users

        if self.severity == 'critical':
            broadcastSeverity = 'e'
        elif self.severity == 'warn' or self.severity == 'serious':
            broadcastSeverity = 'w'
        else:
            broadcastSeverity = 'i'

        self.alertsActorReference.write(message_code=broadcastSeverity,
                                        message={"alert" + self.camelCase: self.msg})

        if command:
            command.write(message_code=broadcastSeverity,
                          message={"alert" + self.camelCase: self.msg})

        if self.active:
            log.info("ALERT! " + self.camelCase + " " + self.formatOutput())

    async def checkKey(self):
        # check key, should be called when keyword changes

        check = self.checker(self)

        if check == "ok":
            if self.selfClear:
                await self.clear()
            elif self.acknowledged:
                await self.clear()
            else:
                # self.severity = "ok"
                return self.severity
        else:
            if not self.active:
                await self.setActive(check)

        return check

    async def disable(self, disabledBy=-1):
        self.disabled = True
        self.disabledBy = disabledBy

        # self.active = False

        # probably do some more stuff

    async def enable(self):
        self.disabled = False
        await self.checkKey()
