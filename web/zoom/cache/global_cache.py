import logging
from zoom.entities.types import UpdateType


class GlobalCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients):
        """
        :type configuration: zoom.config.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

    def get_mode(self):
        data, stat = self._zoo_keeper.client.get(
            self._configuration.global_mode_path, watch=self._send_update)

        logging.info("Global Mode retrieved from ZooKeeper {0}"
                     .format(self._configuration.global_mode_path))
        return data

    def _send_update(self, event):
        """
        :type event: kazoo.protocol.states.WatchedEvent
        """
        try:
            data = self.get_mode()

            message = dict(
                type=UpdateType.GLOBAL_MODE_UPDATE,
                payload=data
            )
            logging.debug('Sending update: {0}'.format(message))

            for client in self._web_socket_clients:
                client.write_message(message)
        except Exception:
            logging.exception('An unhandled Exception has occurred')
