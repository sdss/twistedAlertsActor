#!/usr/bin/env python
# encoding: utf-8
#
# alerts_main.py
#

import time

from clu.actor import AMQPActor
from clu.client import AMQPClient

from alertsActor import __version__, alertActions
import alertsActor.cmds.parser as alerts_parser
from alertsActor import log
from alertsActor.rules import callbackWrapper, mail, dangerKey
from alertsActor.tools import Timer, wrapBlocking


class alertsActor(AMQPActor):
    """the actor"""

    parser = alerts_parser

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # a dictionary of actor keys we're watching
        self.monitoring = dict()

        # keep track of downed instruments
        # since its either up or down, make boolean
        # UP = False, DOWN = True
        self.instrumentDown = dict()

        # keep track of heartbeats
        self.heartbeats = dict()

        self.callbacks = callbackWrapper.wrapCallbacks(self, alertActions)

        monitoredClients = list()
        for key in self.callbacks.datamodel_callbacks:
            actor = key.split(".")[0]
            if actor not in monitoredClients:
                monitoredClients.append(actor)

        self.client = AMQPClient('alerts', host='localhost', port=5672,
                                 models=monitoredClients)
        await self.client.start()

        for key, value in self.callbacks.datamodel_callbacks.items():
            actor, keyword = key.split(".")
            self.client[actor][keyword].register_callback(value)

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

    async def broadcastActive(self):
        for a in self.activeAlerts:
            await a.dispatchAlertMessage()

    async def broadcastDisabled(self):
        for a in self.disabledAlerts:
            await a.dispatchAlertMessage()

    async def broadcastInstruments(self):
        for name, down in self.instrumentDown:
            self.write(message_code="i",
                       message={"instrumentStatus": {"name": name,
                                                     "disabled": down}})

    @property
    def hubModel(self):
        # keeps a running data model of keywords coming from the hub
        # allows callbacks on updates

        return self.client.models


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
        self.triggeredTime = None
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
        self.smtpclient = alertsActor.config["email"]["mailClient"]

        # kwargs, second argument is the default
        self.defaultSeverity = kwargs.get("severity", "info")
        self.dangerVal = kwargs.get("dangerVal", None)
        self.selfClear = kwargs.get("selfClear", False)
        self.instruments = kwargs.get("instruments", None)
        self.checkAfter = kwargs.get("checkAfter", 120)
        self.checker = kwargs.get("checker", dangerKey.default())
        self.emailDelay = kwargs.get("emailDelay", self.checkAfter)

        assert self.severity in ['ok', 'info', 'apogeediskwarn', 'warn', 'serious', 'critical'], "severity level not allowed"

    def keywordFmt(self):
        if "heartbeat" in self.actorKey:
            instring = "at {time}; last seen {diff} sec ago".format(time=self.triggeredTime,
                                                                    diff=int(time.time()-self.lastalive))
        elif "stale" in self.actorKey:
            instring = "at {time}; no change for {diff} sec, with {keyword}".format(time=self.triggeredTime,
                                                                    diff=int(time.time()-self.lastalive),
                                                                    keyword=parseKey(self.keyword))
        else:
            instring = 'at {time}; found {keyword}'.format(keyword=parseKey(self.keyword), time=self.triggeredTime)
        return qstr(instring)

    @property
    def msg(self):
        # return "alert={actorKey}, {severity}, {value}, {enable}, {acknowledged}, {acknowledger}".format(
        #        actorKey=self.actorKey, value=self.keywordFmt(),
        #        severity=self.severity, enable=enabled(self.disabled), acknowledged=ack(self.acknowledged),
        #        acknowledger=self.acknowledger)

        formatted = {"keyword": self.actorKey,
                     "value": self.keywordFmt(),
                     "timeStamp": self.triggeredTime,
                     "severity": self.severity,
                     "disabled": self.disabled,
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

    def setActive(self, severity=None):
        # something cause a problem, do stuff
        self.acknowledged = False  # clear anything from old alert
        self.active = True
        if severity is None:
            self.severity = self.defaultSeverity
        else:
            self.severity = severity
        self.stampTime()
        self.checkMe.start(self.checkAfter, self.reevaluate)

        if self.instDown:
            self.disable(0)
            log.info("NO ALERT: {} instrument down, no alert!!".format(self.actorKey))
            return None

        await self.dispatchAlertMessage()
        # give the alert a chance to clear before emailing everyone
        self.emailTimer.start(self.emailDelay, self.sendEmail)

    async def clear(self):
        # everything good, back to normal
        self.active = False
        self.checkMe.cancel()
        self.checkMe = Timer()
        self.emailTimer.cancel()
        self.emailTimer = Timer()
        self.severity = 'ok'
        self.triggeredTime = None
        self.emailSent = False

        await self.alertsActorReference.broadcastActive()
        await self.alertsActorReference.broadcastDisabled()
        await self.alertsActorReference.broadcastAll()

    async def acknowledge(self, msg=None, acknowledgedBy=None, unack=False):
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

        await self.dispatchAlertMessage()

    async def reevaluate(self):
        # at some point this will presumably raise alert level?
        # possibly send email? Or only send email for critical? Or...
        # if self.alertsActorReference.hub.didFail:
        #     self.alertsActorReference.reconnect()
        await check = self.checkKey()
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
            self.checkMe.start(self.checkAfter, self.reevaluate)
            return

        if self.disabled:
            self.checkMe.start(self.checkAfter, self.reevaluate)
            return

        await self.dispatchAlertMessage()
        self.checkMe.start(self.checkAfter, self.reevaluate)

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

    async def dispatchAlertMessage(self):
        # write an alert to users

        if self.severity == 'critical':
            broadcastSeverity = 'e'
        elif self.severity == 'warn' or self.severity == 'serious':
            broadcastSeverity = 'w'
        else:
            broadcastSeverity = 'i'

        await self.alertsActorReference.write(message_code=broadcastSeverity,
                                              message={"alert": self.msg})

        log.info("ALERT! " + self.msg)

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

    async def disable(self, disabledBy):
        self.disabled = True
        self.disabledBy = disabledBy

        # self.active = False

        # probably do some more stuff

    async def enable(self):
        self.disabled = False
        await self.checkKey()
