import logging
import signal

from kazoo.client import KazooState

from zoom.www.cache.data_store import DataStore
from zoom.www.web_server import WebServer
from zoom.www.entities.zoo_keeper import ZooKeeper
from zoom.www.config.configuration import Configuration
from zoom.www.entities.task_server import TaskServer


class Session(object):
    def __init__(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self._handle_sig_event)
        signal.signal(signal.SIGTERM, self._handle_sig_event)

        self._prev_connection_state = None
        self._zoo_keeper = ZooKeeper(self._zk_listener, env=kwargs.get('environment'))
        self._zoo_keeper.start()
        self._configuration = Configuration(self._zoo_keeper, **kwargs)

        self._task_server = TaskServer(self._configuration, self._zoo_keeper)
        self._data_store = DataStore(self._configuration, self._zoo_keeper,
                                     self._task_server)
        self._web_server = WebServer(self._configuration, self._data_store,
                                     self._task_server, self._zoo_keeper)

    def start(self):
        self._data_store.load()
        self._web_server.start()

    def stop(self):
        self._web_server.stop()
        self._zoo_keeper.stop()

    def _handle_sig_event(self, signum, frame):
        logging.info("Signal handler called with signal {0}".format(signum))
        self.stop()

    def _zk_listener(self, state):
        """
        The callback function that runs when the connection state to Zookeeper
        changes.
        Either passes or immediately spawns a new thread that resets any
        watches, etc., so that it can listen to future connection state changes.
        """
        try:
            logging.info('Zookeeper Connection went from {0} to {1}'
                         .format(self._prev_connection_state, state))
            if self._prev_connection_state is None \
                    and state == KazooState.CONNECTED:
                pass
            elif self._prev_connection_state == KazooState.LOST \
                    and state == KazooState.CONNECTED:
                logging.info('Connection restored. Initiating data reload.')
                self._zoo_keeper.kazoo.handler.spawn(self._data_store.reload)
            elif self._prev_connection_state == KazooState.CONNECTED \
                    and state == KazooState.SUSPENDED:
                pass
            elif self._prev_connection_state == KazooState.CONNECTED \
                    and state == KazooState.LOST:
                pass
            elif self._prev_connection_state == KazooState.SUSPENDED \
                    and state == KazooState.LOST:
                pass
            elif self._prev_connection_state == KazooState.SUSPENDED \
                    and state == KazooState.CONNECTED:
                logging.info('Connection restored. Initiating data reload.')
                self._zoo_keeper.kazoo.handler.spawn(self._data_store.reload)
            elif state == KazooState.CONNECTED:
                logging.info('Connection restored. Initiating data reload.')
                self._zoo_keeper.kazoo.handler.spawn(self._data_store.reload)
            else:
                logging.info('Zookeeper Connection in unknown state: {0}'
                             .format(state))
                return
            self._prev_connection_state = state

        except Exception:
            logging.exception('An uncaught exception has occurred')