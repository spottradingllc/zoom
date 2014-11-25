import logging
import datetime
from time import sleep
from threading import Thread

from zoom.common.types import Weekdays
from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.entities.thread_safe_object import ThreadSafeObject


class PredicateWeekend(SimplePredicate):
    def __init__(self, comp_name, settings, parent=None, interval=10):
        """
        :type comp_name: str
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type parent: str or None
        :type interval: int or float
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.interval = interval
        self._log = logging.getLogger('sent.{0}.weekend'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._started = False

    @property
    def weekday(self):
        """
        :rtype: int
            0=Sunday, 1=Monday, etc.
        """
        return datetime.date.today().weekday()

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
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

    def _run_loop(self):
        while self._operate == True:
            self._process_met()
            sleep(self.interval)
        self._log.info('Done checking for weekend.')

    def _process_met(self):
        self.set_met(self.weekday in [Weekdays.SATURDAY, Weekdays.SUNDAY])

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, started={3}, met={4})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.started,
                        self._met))

    def __eq__(self, other):
        return type(self) == type(other)

    def __ne__(self, other):
        return type(self) != type(other)
