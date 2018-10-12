#!/usr/bin/env python
# encoding: utf-8
#
# alerts_main.py
#



from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import json
import sys
import traceback

import time

from click.testing import CliRunner

from RO.StringUtil import strFromException
from RO.Comm.TwistedTimer import Timer
from twistedActor import BaseActor, CommandError, UserCmd

from alertsActor import __version__
from alertsActor.cmds.cmd_parser import alerts_parser
from alertsActor.logger import log

from alertsActor.rules import callbackWrapper


class alertsActor(BaseActor):
    """the actor"""

    def __init__(self, config, **kwargs):

        self.cmdParser = alerts_parser
        self.config = config

        self.callbacks = callbackWrapper.wrapCallbacks(self, keywords)

        self.connectHub('localhost', datamodel_casts=self.callbacks.datamodel_casts, 
                                     datamodel_callbacks=self.callbacks.datamodel_callbacks)

        log.info('starting alertsActor actor version={!r} in port={}'
                 .format(__version__, kwargs['userPort']))

        super(alertsActor, self).__init__(**kwargs)

        # Sets itself as the default actor to write to when logging.
        log.set_actor(self)

        # might as well just increment it right? 
        self.alertIDcounter = 0
        self.alerts = dict()

        # keep track of heartbeats
        self.heartbeats = dict()


    @property
    def dataModel(self):
        # keeps a running data model of keywords coming from the hub
        # allows callbacks on updates

        # this may need to be more careful... test! 
        if self.hub is None:
            self.connectHub('localhost', datamodel_casts=callbacks.datamodel_casts, 
                                         datamodel_callbacks=callbacks.datamodel_callbacks)

        return self.hub.datamodel


    def raiseAlert(cause, severity):
        # raise an alert and add it to the actors alerts
        self.alerts[self.alertIDcounter] = alert(cause, severity)
        self.alertIDcounter += 1


    def parseAndDispatchCmd(self, cmd):
        """Dispatch the user command."""

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


class alert(object):
    '''The basic alert. It knows when it was created, what triggered it,
    
    whether its been acknowledged, whether the condition that triggered it has gone away, etc.

    '''

    def __init__(self, cause, severity):
        self.triggeredTime = time.time()
        self.causeString = cause 
        self.active = True
        self.acknowledged = False
        self.acknowledgeMsg = None

        self.checkMe = Timer()


    def acknowledge(self, msg=None):
        if msg is not None:
            self.acknowledgeMsg = msg

        self.acknowledged = True

