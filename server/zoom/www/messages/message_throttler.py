import logging
import time
from multiprocessing import Lock
from threading import Thread


class MessageThrottle(object):
    '''
    Send at most throttle_interval message per second to zoom clients
    '''
    def __init__(self, configuration, clients):
        self._interval = configuration.throttle_interval
        self._lock = Lock()
        self._clients = clients
        self._message = None
        self._thread = Thread(target=self._run,
                              name='message_throttler')
        self._running = True

    def start(self):
        self._thread.start()

    def add_message(self, message):
        self._lock.acquire()
        try:
            if self._message is None:
                self._message = message
            else:
                self._message.combine(message)
        finally:
            self._lock.release()

    def _run(self):
    
        while self._running:
            self._lock.acquire()
            try:
                if self._message is not None:
                    logging.debug('Sending message: {0}'
                                  .format(self._message.to_json()))
                    for client in self._clients:
                        try:
                            client.write_message(self._message.to_json())
                        except IndexError:
                            logging.debug('Client closed when trying to send '
                                          'update.')
                            continue
                    self._message = None
            except AttributeError as e:
                logging.exception('Exception in MessageThrottle: {0}'.format(e))
            finally:
                self._lock.release()
            
            time.sleep(float(self._interval))

    def stop(self):
        if self._thread.is_alive():
            self._running = False
            self._thread.join()
