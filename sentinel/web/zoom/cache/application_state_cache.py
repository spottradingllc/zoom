import logging
import os.path

from kazoo.exceptions import NoNodeError
from zoom.entities.application_state import ApplicationState
from zoom.entities.types import ApplicationStatus, OperationType
from zoom.messages.application_states import ApplicationStatesMessage


class ApplicationStateCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 agent_cache, time_estimate_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        :type agent_cache: zoom.cache.agent_cache.AgentCache
        """
        self._configuration = configuration
        self._cache = ApplicationStatesMessage()
        self._cache.set_environment(self._configuration.environment)
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

        self._agent_cache = agent_cache
        self._agent_cache.add_callback(self._on_update)

        self._time_estimate_cache = time_estimate_cache;

    def load(self):
        """
        :rtype: dict
        """
        if not len(self._cache):
           self._load()

        return self._cache

    def reload(self):
        self._cache.clear()
        self._on_update_path(self._configuration.application_state_path)

    def _load(self):
        """
        :rtype: dict
        """
        self._agent_cache.load()
        self._cache.clear()

        self._walk(self._configuration.application_state_path, self._cache)
        logging.info("Application state cache loaded from ZooKeeper {0}"
                     .format(self._configuration.application_state_path))

        self._time_estimate_cache.update_appplication_states(self._cache.application_states)

    def _walk(self, path, result):
        """
        :type path: str
        :type result: zoom.messages.application_states.ApplicationStatesMessage
        """
        try:
            children = self._zoo_keeper.get_children(path)

            if children:
                for child in children:
                    self._walk(os.path.join(path, child), result)
            else:
                app_state = self._get_application_state(path)
                result.set_operation_type(OperationType.ADD)
                result.update({app_state.configuration_path : app_state.to_dictionary()})

        except NoNodeError:
            logging.debug('Node at {0} no longer exists.'.format(path))
            result.set_operation_type(OperationType.REMOVE)
            result.update({
                path: ApplicationState(configuration_path=path).to_dictionary(),
            })

        except Exception:
            logging.exception('An unhandled Exception has occurred while '
                              'running ApplicationStateCache.walk.')

    def _get_application_state(self, path):
        """
        :type path: str
        :rtype: zoom.entities.application_state.ApplicationState
        """
        data, stat = self._zoo_keeper.get(path)

        # persistent node
        if stat.ephemeralOwner == 0:
            # watch node to see if children are created
            self._zoo_keeper.get_children(path, watch=self._on_update)

            agent_data = self._agent_cache.get_app_data_by_path(path)

            application_state = ApplicationState(
                application_name=agent_data.get('name', os.path.basename(path)),
                configuration_path=path,
                application_status=ApplicationStatus.STOPPED,
                application_host=self._agent_cache.get_host_by_path(path),
                error_state=agent_data.get('state', 'unknown'),
                local_mode=agent_data.get('mode', 'unknown')
            )

        # ephemeral node
        else:
            # watch node to see if it goes away
            self._zoo_keeper.get_children(os.path.dirname(path),
                                          watch=self._on_update)

            config_path = os.path.dirname(path)
            host = os.path.basename(path)
            agent_data = self._agent_cache.get_app_data_by_path(config_path)

            application_state = ApplicationState(
                application_name=agent_data.get('name',
                                                os.path.basename(config_path)),
                configuration_path=config_path,
                application_status=ApplicationStatus.RUNNING,
                application_host=host,
                start_time=stat.created,
                error_state=agent_data.get('state', 'unknown'),
                local_mode=agent_data.get('mode', 'unknown')
            )

        return application_state

    def _on_update(self, event):
        """
        Callback to send updates via websocket on application state changes.
        :type event: kazoo.protocol.states.WatchedEvent
        """
        self._on_update_path(event.path)

    def _on_update_path(self, path):
        try:
            message = ApplicationStatesMessage()

            self._walk(path, message)

            # remove non-existent zookeeper paths
            if message.operation_type == OperationType.REMOVE:
                self._cache.remove(message.application_states)
            # update cache with any zookeper changes
            elif message.operation_type == OperationType.ADD:
                self._cache.update(message.application_states)

            logging.debug('Sending state update: {0}'.format(message.to_json()))

            for client in self._web_socket_clients:
                client.write_message(message.to_json())

            self._time_estimate_cache.update_appplication_states(self._cache.application_states)

        except Exception:
            logging.exception('An unhandled Exception has occurred')
