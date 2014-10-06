import logging
import tornado.websocket

from spot.zoom.common.decorators import TimeThis


class ZoomWSHandler(tornado.websocket.WebSocketHandler):

    @property
    def socket_clients(self):
        """
        :rtype: list
        """
        return self.application.data_store.web_socket_clients

    @TimeThis(__file__)
    def open(self):
        logging.debug("[WEBSOCKET] Opening")
        self.socket_clients.append(self)
        logging.debug('Added websocket client. Total clients: {0}'
                      .format(len(self.socket_clients)))

    @TimeThis(__file__)
    def on_message(self, message):
        logging.debug("[WEBSOCKET] Message: '{0}'".format(message))

    @TimeThis(__file__)
    def on_close(self):
        self.socket_clients.remove(self)
        logging.debug("[WEBSOCKET] Closed.  Total clients: {0}"
                      .format(len(self.socket_clients)))
