import logging
import datetime
from time import sleep
from threading import Thread

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate
from spot.zoom.common.types import SimpleObject
from spot.zoom.agent.sentinel.util.decorators import connected
from spot.zoom.agent.sentinel.config.constants import ZK_HOLIDAY_PATH


class PredicateHoliday(SimplePredicate):
    def __init__(self, comp_name, zkclient, parent=None, interval=10):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type parent: str or None
        :type interval: int or float
        """
        SimplePredicate.__init__(self, comp_name, parent=parent)
        self.zkclient = zkclient
        self.interval = interval
        self._log = logging.getLogger('sent.{0}.holiday'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

        self._operate = SimpleObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._started = False
        self._holidays = list()

    @property
    def date_string(self):
        """
        :rtype: str
            Example: 20140101
        """
        return datetime.date.today().strftime('%Y%m%d')

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._watch_node()
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
        self._log.info('Done checking for holiday.')

    def _process_met(self):
        self.set_met(self.date_string in self._holidays)

    @connected
    def _watch_node(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        exists = self.zkclient.exists(ZK_HOLIDAY_PATH, watch=self._watch_node)
        if exists:
            self._holidays = self.zkclient.get_children(ZK_HOLIDAY_PATH,
                                                        watch=self._watch_node)
            self._log.info('Got holidays {0}'.format(self._holidays))
            self._process_met()
        else:
            self._log.info('No gut node was found. Watcher is set at {0}'
                           .format(ZK_HOLIDAY_PATH))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, met={3})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self._met)
                )

    def __eq__(self, other):
        return type(self) == type(other)

    def __ne__(self, other):
        return type(self) != type(other)
