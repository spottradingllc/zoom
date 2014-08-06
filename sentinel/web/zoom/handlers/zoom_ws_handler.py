import logging
import tornado.websocket


class ZoomWSHandler(tornado.websocket.WebSocketHandler):

    @property
    def socket_clients(self):
        return self.application.data_store.web_socket_clients

    def open(self):
        logging.debug("[WEBSOCKET] Opening")
        self.socket_clients.append(self)
        logging.debug('Added websocket client. Total clients: {0}'
                      .format(len(self.socket_clients)))

    def on_message(self, message):
        logging.debug("[WEBSOCKET] Message: '{0}'".format(message))

    def on_close(self):
        logging.debug("[WEBSOCKET] Closing")
        self.socket_clients.remove(self)
