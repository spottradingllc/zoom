import logging
import requests
from time import sleep
from threading import Thread
from zoom.agent.entities.thread_safe_object import ThreadSafeObject
from zoom.agent.predicate.simple import SimplePredicate


class APIPredicate(SimplePredicate):
    """
    Predicate that polls a url for a specific code.
    """
    def __init__(self, comp_name, url, verb='GET', expected_code=200,
                 interval=5.0, operational=False, parent=None):
        """
        :type comp_name: str
        :type url: str
        :type verb: str
        :type expected_code: int
        :type interval: int or float
        :type operational: bool
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, operational=operational, parent=parent)
        self._log = logging.getLogger('sent.{0}.pred.api'.format(comp_name))
        logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
        self.url = url
        self.verb = verb
        self.expected_code = expected_code
        self.interval = interval

        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._log.info('Registered {0}'.format(self))
        self._started = False

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._thread.start()
            self._block_until_started()
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

    def _run(self):
        """
        Query the given url, and report whether we get the expected code.
        """
        try:
            r = requests.request(self.verb, self.url, timeout=2)
            self.set_met(r.status_code == self.expected_code)
        except requests.ConnectionError:
            self._log.debug('URL {0} is not available.'.format(self.url))
            self.set_met(False)
        except requests.Timeout:
            self._log.debug('Timed out to URL {0}.'.format(self.url))
            self.set_met(False)

    def _run_loop(self):
        while self._operate == True:
            self._run()
            sleep(self.interval)
        self._log.info('Done querying {0}'.format(self.url))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, url="{3}", verb={4}, '
                'interval={5} started={6}, operational={7}, met={8})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.url,
                        self.verb,
                        self.interval,
                        self.started,
                        self._operational,
                        self._met))

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.url == getattr(other, 'url', None),
            self.verb == getattr(other, 'verb', None),
            self.interval == getattr(other, 'interval', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.url != getattr(other, 'url', None),
            self.verb != getattr(other, 'verb', None),
            self.interval != getattr(other, 'interval', None)
        ])
