import logging

from spot.zoom.www.messages.global_mode_message import GlobalModeMessage


class GlobalCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients):
        """
        :type configuration: spot.zoom.www.config.configuration.Configuration
        :type zoo_keeper: spot.zoom.www.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

    def start(self):
        pass

    def stop(self):
        pass

    def get_mode(self):
        data, stat = self._zoo_keeper.get(
            self._configuration.global_mode_path, watch=self.on_update)

        logging.info("Global Mode retrieved from ZooKeeper {0}"
                     .format(self._configuration.global_mode_path))
        return GlobalModeMessage(data)

    def on_update(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        try:
            message = self.get_mode()
            logging.debug('Sending update: {0}'.format(message.to_json()))

            for client in self._web_socket_clients:
                client.write_message(message.to_json())

        except Exception:
            logging.exception('An unhandled Exception has occurred')
