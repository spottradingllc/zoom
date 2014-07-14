from zoom.cache.application_state_cache import ApplicationStateCache
from zoom.cache.global_cache import GlobalCache
from zoom.cache.agent_cache import AgentCache


class DataStore(object):
    def __init__(self, configuration, zoo_keeper):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = list()

        self._agent_cache = AgentCache(self._configuration, self._zoo_keeper)
        self._application_state_cache = ApplicationStateCache(self._configuration,
                                                              self._zoo_keeper,
                                                              self._web_socket_clients,
                                                              self._agent_cache)
        self._global_cache = GlobalCache(self._configuration,
                                         self._zoo_keeper,
                                         self._web_socket_clients)

    def load_application_state_cache(self):
        """
        :rtype: dict
        """
        return self._application_state_cache.load()

    def get_global_mode(self):
        return self._global_cache.get_mode()

    @property
    def web_socket_clients(self):
        """
        :rtype: list
        """
        return self._web_socket_clients