import logging
import os.path

from zoom.entities.application_state import ApplicationState
from zoom.entities.types import ApplicationStatus, UpdateType


class ApplicationStateCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 agent_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        :type agent_cache: zoom.cache.agent_cache.AgentCache
        """
        self._cache = dict()
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

        self._agent_cache = agent_cache
        self._agent_cache.add_callback(self._send_update)

    def load(self):
        """
        :rtype: dict
        """
        self._agent_cache.load()
        result = dict(application_states=list())

        self._walk(self._configuration.application_state_path, result)
        logging.info("Application state cache loaded from ZooKeeper {0}"
                     .format(self._configuration.application_state_path))
        logging.info(result['application_states'][0])
        return result

    def _walk(self, path, result_dict):
        """
        :type path: str
        :type result_dict: dict
        """
        try:
            children = self._zoo_keeper.client.get_children(path)

            if children:
                for child in children:
                    self._walk(os.path.join(path, child), result_dict)
            else:
                app_state = self._get_application_state(path)
                result_dict['application_states'].append(
                    app_state.to_dictionary())
        except Exception:
            logging.exception('An unhandled Exception has occurred while '
                              'running ApplicationStateCache.walk.')

    def _get_application_state(self, path):
        """
        :type path: str
        :rtype: zoom.entities.application_state.ApplicationState
        """
        data, stat = self._zoo_keeper.client.get(path)

        # persistent node
        if stat.ephemeralOwner == 0:
            # watch node to see if children are created
            self._zoo_keeper.client.get_children(path, watch=self._send_update)

            agent_data = self._agent_cache.get_app_data_by_path(path)

            application_state = ApplicationState(
                application_name=os.path.basename(path),
                configuration_path=path,
                application_status=ApplicationStatus.STOPPED,
                application_host=self._agent_cache.get_host_by_path(path),
                error_state=agent_data.get('state', 'unknown'),
                local_mode=agent_data.get('mode', 'unknown')
            )

        # ephemeral node
        else:
            # watch node to see if it goes away
            self._zoo_keeper.client.get_children(os.path.dirname(path),
                                                 watch=self._send_update)

            config_path = os.path.dirname(path)
            host = os.path.basename(path)
            name = os.path.basename(config_path)
            agent_data = self._agent_cache.get_app_data_by_path(config_path)

            application_state = ApplicationState(
                application_name=name,
                configuration_path=config_path,
                application_status=ApplicationStatus.RUNNING,
                application_host=host,
                start_time=stat.created,
                error_state=agent_data.get('state', 'unknown'),
                local_mode=agent_data.get('mode', 'unknown')
            )

        return application_state

    def _send_update(self, event):
        """
        Callback to send updates via websocket on application state changes.
        :type event: kazoo.protocol.states.WatchedEvent
        """
        try:
            result = dict(
                application_states=list()
            )

            self._walk(event.path, result)

            message = dict(
                type=UpdateType.APPLICATION_STATE_UPDATE,
                payload=result
            )
            logging.debug('Sending update: {0}'.format(message))

            for client in self._web_socket_clients:
                client.write_message(message)
        except Exception:
            logging.exception('An unhandled Exception has occurred')