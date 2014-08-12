import logging
import platform
import time

from kazoo.client import KazooClient
from threading import Thread

from spot.zoom.agent.sentinel.config.constants import ZK_CONN_STRING


class StaggerLock(object):
    def __init__(self, temp_path, timeout):
        """
        :type temp_path: str
        :type timeout: int
        """
        self._path = temp_path
        self._timeout = timeout
        self._thread = None
        self._zk = KazooClient(hosts=ZK_CONN_STRING)
        self._log = logging.getLogger('sent.sl')
        self._counter = 0

    def join(self):
        if self._thread is not None:
            self._thread.join()
            self._zk.stop()
            self._zk.close()
            self._thread = None
        else:
            return

    def start(self):
        """
        This method is to implement a staggered startup.
        A new KazooClient is instantiated b/c of thread-safety issues with the
        election.
        """
        self._zk.start()
        self._log.info('Attempting to acquire stagger lock.')
        lock = self._zk.Lock(self._path, identifier=platform.node())
        lock.acquire(blocking=True)
        self._thread = Thread(target=self._sleep_and_unlock,
                              args=(lock,),
                              name=str(self))
        self._thread.daemon = True
        self._thread.start()

    def _sleep_and_unlock(self, lck):
        self._log.info('Got stagger lock. Sleeping for {0} seconds.'
                       .format(self._timeout))
        time.sleep(self._timeout)
        lck.release()
        self._log.info('Released stagger lock.')

    def __repr__(self):
        return 'StaggerLock(path={0}, timeout={1})'.format(self._path,
                                                           self._timeout)

    def __str__(self):
        return self.__repr__()