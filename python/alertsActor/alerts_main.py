#!/usr/bin/env python
# encoding: utf-8
#
# alerts_main.py
#


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import json
import yaml
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

from alertsActor.rules import callbackWrapper


class alertsActor(BaseActor):
    """the actor"""

    def __init__(self, config, **kwargs):

        self.cmdParser = alerts_parser
        self.config = config

        super(alertsActor, self).__init__(**kwargs)

        # a dictionary of actor keys we're watching
        self.monitoring = dict()

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
    def hubModel(self):
        # keeps a running data model of keywords coming from the hub
        # allows callbacks on updates

        # this may need to be more careful... test! 
        if self.hub is None:
            print("no hub connection, reconnecting!")
            self.connectHub('localhost', datamodel_casts=self.callbacks.datamodel_casts, 
                                         datamodel_callbacks=self.callbacks.datamodel_callbacks)

        return self.hub.datamodel


    def checkKey(self, actorKey):
        # update to datamodel, what do?
        actor, keyword = actorKey.split('.')
        key = self.hubModel[actor][keyword]
        if key == self.monitoring[actorKey].dangerVal:
            if self.monitoring[actorKey].active:
                # we already know
                return None
            else:
                self.monitoring[actorKey].setActive()
        else:
            # if they changed and its good, then the alert is gone, right?
            self.monitoring[actorKey].resolve()


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
            result = test_cmd(cmd.cmdBody.split())
            if result is False:
                return
            alerts_parser(cmd.cmdBody.split(), obj=dict(actor=self, cmd=cmd))
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


class keyState(object):
    '''Keep track of the state of each actor.key'''

    def __init__(self, alertsActor, actorKey='oop.forgot', severity='info', dangerVal=None,
                 defaultMsg=''):
        self.alertsActorReference = alertsActor
        self.triggeredTime = None
        self.actorKey = actorKey
        self.active = False
        self.defaultSeverity = severity
        self.severity = 'info'
        self.acknowledged = False
        self.acknowledgeMsg = None
        self.dangerVal = dangerVal  # value on which to raise alert
        self.checkMe = Timer()
        self.defaultMsg = defaultMsg  # message to send user with alert
        self.msg = "all good"  # formatted message, "all good" should never be sent


    def setActive(self):
        # something cause a problem, do stuff
        self.active = True
        self.severity = self.defaultSeverity
        self.triggeredTime = time.time()
        self.checkMe.start(600, self.reevaluate)

        self.msg = "alert={actorKey}, {severity}, {other}".format(actorKey=self.actorKey,
                    severity=self.severity, other='otherstuff')

        self.dispatchAlertMessage(self.msg, severity=self.severity)


    def resolve(self):
        # everything good, back to normal
        self.active = False
        self.checkMe = Timer()
        self.severity = 'info'


    def acknowledge(self, msg=None):
        if msg is not None:
            self.acknowledgeMsg += msg + "\n" # so we can add many... I guess?

        self.acknowledged = True


    def reevaluate(self):
        if not self.acknowledged:
            self.dispatchAlertMessage(self.msg, severity=self.severity)
            self.checkMe.start(600, self.reevaluate)


    def dispatchAlertMessage(self, msg, severity='info'):
        # write an alert to users
        if severity == 'critical':
            broadcastSeverity = 'e'
        elif severity == 'warning' or severity == 'serious':
            broadcastSeverity = 'w'
        else:
            broadcastSeverity = 'i'

        self.alertsActorReference.writeToUsers(broadcastSeverity, msg)
