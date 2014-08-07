import logging
import time
from multiprocessing import Lock
from threading import Thread


class MessageThrottle(object):
    def __init__(self, configuration, clients):
        self._changed = False
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
        logging.debug('Adding message: {0}'.format(message))
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
                    logging.debug('Sending message: {0}'.format(self._message.to_json()))
                    for client in self._clients:
                        client.write_message(self._message.to_json())
                    self._message = None
                    logging.debug('Sent')
            
            finally:
                self._lock.release()
            
            time.sleep(float(self._interval))


    def stop(self):
        self._running = False
        self._thread.join()
            
            
