import logging
import os.path
import shlex
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

from spot.zoom.common.types import PlatformType
from spot.zoom.agent.sentinel.common.thread_safe_object import ThreadSafeObject
from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate


class PredicateHealth(SimplePredicate):
    def __init__(self, comp_name, settings, command, interval, system, parent=None):
        """
        :type comp_name: str
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        :type command: str
        :type interval: int or float
        :type system: spot.zoom.common.types.PlatformType
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self._log = logging.getLogger('sent.{0}.pred.health'.format(comp_name))
        self.interval = interval
        self.rawcmd = command
        self._runcmd = str()
        self._system = system
        self._verify()

        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._log.info('Registered {0}'.format(self))
        self._started = False

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._log.info('Starting {0}'.format(self))
            self._thread.start()
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.info('Stopping {0}'.format(self))
            self._started = False
            self._operate.set_value(False)
            self._thread.join()
            self._log.info('{0} stopped'.format(self))
        else:
            self._log.debug('Already stopped {0}'.format(self))

    def _verify(self):
        if self._system == PlatformType.LINUX:
            self._runcmd = shlex.split(self.rawcmd)
        elif self._system == PlatformType.WINDOWS:
            self._runcmd = self.rawcmd
        else:
            self._runcmd = ""

        exe = shlex.split(self.rawcmd)[0]
        exists = os.path.exists(exe)
        if not exists:
            searchpath = os.environ['PATH']
            for i in searchpath.split(':'):
                newpath = os.path.join(i, exe)
                if os.path.exists(newpath):
                    exists = True
                    break

        if not exists:
            err = ('Cannot register check "{0}". The path does not exist.'
                   .format(exe))
            self._log.error(err)
            raise OSError(err)

    def _run(self):
        """
        Run the check as a subprocess and return the results as a bool based on
        return code. (Non-zero equals failure)
        :rtype: bool
        """
        p = Popen(self._runcmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if err:
            self._log.error('There was some error with the check "{0}"\n{1}'
                            .format(self.rawcmd, err))
            self.set_met(False)
        if p.returncode != 0:
            self._log.error('Check "{0}" has failed.'.format(self.rawcmd))
            self.set_met(False)
        else:
            self._log.debug('Check "{0}" has succeeded.'.format(self.rawcmd))
            self.set_met(True)

    def _run_loop(self):
        while self._operate == True:
            self._run()
            sleep(self.interval)
        self._log.info('Done running {0}'.format(self))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, cmd="{3}", interval={4} '
                'started={5}, met={6})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.rawcmd,
                        self.interval,
                        self.started,
                        self._met))
    
    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.rawcmd == getattr(other, 'rawcmd', None),
            self.interval == getattr(other, 'interval', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.rawcmd != getattr(other, 'rawcmd', None),
            self.interval != getattr(other, 'interval', None)
        ])
