import logging

import tornado.websocket

from spot.zoom.core.utils.decorators import timethis


class ZoomWSHandler(tornado.websocket.WebSocketHandler):

    @property
    def socket_clients(self):
        return self.application.data_store.web_socket_clients

    @timethis(__file__)
    def open(self):
        logging.debug("[WEBSOCKET] Opening")
        self.socket_clients.append(self)
        logging.debug('Added websocket client. Total clients: {0}'
                      .format(len(self.socket_clients)))

    @timethis(__file__)
    def on_message(self, message):
        logging.debug("[WEBSOCKET] Message: '{0}'".format(message))

    @timethis(__file__)
    def on_close(self):
        self.socket_clients.remove(self)
        logging.debug("[WEBSOCKET] Closed.  Total clients: {0}"
                      .format(len(self.socket_clients)))

