import logging
from threading import Thread
from time import sleep
from multiprocessing import Lock

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate
from spot.zoom.agent.sentinel.common.thread_safe_object import ThreadSafeObject
from spot.zoom.common.decorators import synchronous


class PredicateProcess(SimplePredicate):
    def __init__(self, comp_name, settings, proc_client, interval, parent=None):
        """
        :type comp_name: str
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        :type proc_client: spot.zoom.agent.sentinel.client.process_client.ProcessClient
        :type interval: int or float
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self._log = logging.getLogger('sent.{0}.pred.process'.format(comp_name))
        self._proc_client = proc_client

        # lock for synchronous decorator
        if proc_client:
            self.process_client_lock = proc_client.process_client_lock
        else:
            self.process_client_lock = Lock()

        self.interval = interval
        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._started = False

    @synchronous('process_client_lock')  # shares lock with ProcessClient
    def running(self):
        """
        With the synchronous decorator, this shares a Lock object with the
        ProcessClient. While ProcessClient.start is running, this will not
        return.
        :rtype: bool
        """
        return self._proc_client.running()

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
            self.set_met(self.running())
            sleep(self.interval)
        self._log.info('Done watching process.')

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, interval={3}, met={4})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.interval,
                        self._met)
                )

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.interval == getattr(other, 'interval', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.interval != getattr(other, 'interval', None)
        ])
