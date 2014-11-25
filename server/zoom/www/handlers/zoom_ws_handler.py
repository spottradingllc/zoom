import logging
import tornado.websocket

from zoom.common.decorators import TimeThis


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
        logging.debug('Added websocket client {0}. Total clients: {1}'
                      .format(self.request.remote_ip, len(self.socket_clients)))

    @TimeThis(__file__)
    def on_message(self, message):
        logging.debug("[WEBSOCKET] Message: '{0}' for client {1}"
                      .format(message, self.request.remote_ip))

    @TimeThis(__file__)
    def on_close(self):
        self.socket_clients.remove(self)
        logging.debug("[WEBSOCKET] Closed for client {0}.  Total clients: {1}"
                      .format(self.request.remote_ip, len(self.socket_clients)))
