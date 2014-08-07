import logging
from zoom.cache.application_state_cache import ApplicationStateCache
from zoom.cache.application_dependency_cache import ApplicationDependencyCache
from zoom.cache.time_estimate_cache import TimeEstimateCache
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

        self._time_estimate_cache = TimeEstimateCache(
                                         self._configuration,
                                         self._web_socket_clients)

        self._application_dependency_cache = \
            ApplicationDependencyCache(self._configuration,
                                       self._zoo_keeper,
                                       self._web_socket_clients,
                                       self._agent_cache,
                                       self._time_estimate_cache)

        self._application_state_cache = \
            ApplicationStateCache(self._configuration,
                                  self._zoo_keeper,
                                  self._web_socket_clients,
                                  self._agent_cache,
                                  self._time_estimate_cache)

        self._global_cache = GlobalCache(self._configuration,
                                         self._zoo_keeper,
                                         self._web_socket_clients)



    def load_application_state_cache(self):
        """
        :rtype: from zoom.messages.application_states.ApplicationStatesMessage
        """
        return self._application_state_cache.load()

    def load_application_dependency_cache(self):
        """
        :rtype: dict
        """
        return self._application_dependency_cache.load()

    def load_time_estimate_cache(self):
        """
        :rtype: dict
        """
        return self._time_estimate_cache.load()

    def get_global_mode(self):
        """
        :rtype: from zoom.messages.global_mode_message.GlobalModeMessage
        """
        return self._global_cache.get_mode()

    def reload(self):
        """
        Clear all cache objects and send reloaded data as updates.
        """
        self._zoo_keeper.restart()  # restart client to destroy any existing watches
        self._global_cache.on_update(None)
        self._agent_cache.reload()
        self._application_state_cache.reload()
        self._application_dependency_cache.reload()
        self._time_estimate_cache.reload()
        return {'cache_clear': 'okay'}

    def load(self):
        """
        Clear all cache objects and send reloaded data as updates.
        """
        self._global_cache.on_update(None)
        self._agent_cache.load()
        self._time_estimate_cache.load()
        self._application_state_cache.load()
        self._application_dependency_cache.load()
        return {'cache_load': 'okay'}

    @property
    def web_socket_clients(self):
        """
        :rtype: list
        """
        return self._web_socket_clients
