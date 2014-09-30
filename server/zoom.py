import getopt
import logging
import platform
import signal

from spot.zoom.www.cache.data_store import DataStore
from spot.zoom.www.web_server import WebServer
from spot.zoom.www.zoo_keeper import ZooKeeper
from spot.zoom.www.config.configuration import Configuration


class Session(object):
    def __init__(self):
        try:
            signal.signal(signal.SIGINT, self._handle_sig_event)
            signal.signal(signal.SIGTERM, self._handle_sig_event)

            self._zoo_keeper = ZooKeeper()
            self._zoo_keeper.start()
            self._configuration = Configuration(self._zoo_keeper)

            self._data_store = DataStore(self._configuration, self._zoo_keeper)
            self._web_server = WebServer(self._configuration, self._data_store,
                                         self._zoo_keeper)

        except getopt.GetoptError as e:
            print str(e)

    def start(self):
        self._data_store.load()
        self._web_server.start()

    def stop(self):
        self._web_server.stop()
        self._zoo_keeper.stop()

    def _handle_sig_event(self, signum, frame):
        logging.info("Signal handler called with signal {0}".format(signum))
        self.stop()

if __name__ == "__main__":
    try:
        if 'Linux' in platform.platform():
            from setproctitle import setproctitle
            logging.info('Changing the process name to Zoom')
            setproctitle('Zoom')  # Changes process name

        session = Session()
        session.start()

        session.stop()

    except Exception as e:
        print str(e)
