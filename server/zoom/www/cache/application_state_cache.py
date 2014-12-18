import logging
import os.path
import json

from kazoo.exceptions import NoNodeError

from zoom.common.decorators import connected_with_return
from zoom.common.types import ApplicationStatus
from zoom.www.entities.application_state import ApplicationState
from zoom.www.messages.application_states import ApplicationStatesMessage
from zoom.www.messages.message_throttler import MessageThrottle


class ApplicationStateCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 time_estimate_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        :type time_estimate_cache: zoom.www.cache.time_estimate_cache.TimeEstimateCache
        """
        self._path_to_host_mapping = dict()
        self._configuration = configuration
        self._cache = ApplicationStatesMessage()
        self._cache.set_environment(self._configuration.environment)
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

        self._time_estimate_cache = time_estimate_cache
        self._message_throttle = MessageThrottle(configuration,
                                                 web_socket_clients)

    def start(self):
        self._message_throttle.start()

    def stop(self):
        self._message_throttle.stop()

    def load(self):
        """
        :rtype: zoom.messages.application_states.ApplicationStatesMessage
        """
        if not len(self._cache):
            self._load()

        return self._cache

    def reload(self):
        self._cache.clear()
        self._on_update_path(self._configuration.application_state_path)

    def _load(self):
        self._cache.clear()

        self._walk(self._configuration.application_state_path, self._cache)
        logging.info("Application state cache loaded from ZooKeeper {0}"
                     .format(self._configuration.application_state_path))

        self._time_estimate_cache.update_states(
            self._cache.application_states)
        self._cache.remove_deletes()

    def manual_update(self, path, key, value):
        """
        Manual override from client of specific value
        :type path: str
        :param key: str
        """
        state = self._cache._application_states.get(path, None)
        if state is not None:
            message = ApplicationStatesMessage()
            state[key] = value
            message.update({path: state})
            self._message_throttle.add_message(message)

    @connected_with_return(None)
    def _walk(self, path, result):
        """
        :type path: str
        :type result: zoom.www.messages.application_states.ApplicationStatesMessage
        """
        try:
            children = self._zoo_keeper.get_children(path, watch=self._on_update)

            if children:
                for child in children:
                    self._walk(os.path.join(path, child).replace("\\", "/"), result)
            else:
                app_state = self._get_application_state(path)
                result.update(
                    {app_state.configuration_path: app_state.to_dictionary()}
                )

        except NoNodeError:
            logging.debug('Node at {0} no longer exists.'.format(path))
            result.update({path: ApplicationState(configuration_path=path,
                                                  delete=True).to_dictionary(),
            })

        except Exception:
            logging.exception('An unhandled Exception has occurred while '
                              'running ApplicationStateCache.walk.')

    def _get_app_details(self, path):
        """
        :type path: str
        :rtype: dict, kazoo.protocol.states.ZnodeStat
        """
        rawData, stat = self._zoo_keeper.get(path, watch=self._on_update)

        data = {}

        if rawData != '':
            try:
                data = json.loads(rawData)
            except ValueError:
                pass

        return data, stat

    def _get_application_state(self, path):
        """
        :type path: str
        :rtype: zoom.entities.application_state.ApplicationState
        """
        data, stat = self._get_app_details(path)

        # persistent node
        if stat.ephemeralOwner == 0:
            # watch node to see if children are created
            self._zoo_keeper.get_children(path, watch=self._on_update)
            host = data.get('host', 'Unknown')
            agent_path = os.path.join(self._configuration.agent_state_path,
                                      host).replace("\\", "/")

            # if the agent is down, update state and mode with unknown
            if (host is None or 
                    not self._zoo_keeper.exists(
                            agent_path,
                            watch=self._on_agent_state_update)):
                data['state'] = 'unknown'
                data['mode'] = 'unknown'
            else:
                self._path_to_host_mapping[host] = path

            application_state = ApplicationState(
                application_name=data.get('name', os.path.basename(path)),
                configuration_path=path,
                application_status=ApplicationStatus.STOPPED,
                application_host=host,
                completion_time=stat.last_modified,
                trigger_time=data.get('trigger_time', ''),
                error_state=data.get('state', 'unknown'),
                local_mode=data.get('mode', 'unknown'),
                login_user=data.get('login_user', 'Zoom'),
                fqdn=data.get('fqdn', host),
                last_command=self._get_last_command(data),
                pd_disabled=self._get_existing_attribute(path, 'pd_disabled'),
                grayed=self._get_existing_attribute(path, 'grayed')
            )

        # ephemeral node
        else:
            # watch node to see if it goes away
            self._zoo_keeper.get_children(os.path.dirname(path),
                                          watch=self._on_update)

            host = os.path.basename(path)
            # if it is running, path = /app/path/HOSTNAME
            # need to convert to /app/path to get the app_details
            config_path = os.path.dirname(path)
            parent_data, parent_stat = self._get_app_details(config_path)

            self._path_to_host_mapping[host] = config_path

            application_state = ApplicationState(
                application_name=parent_data.get('name',
                                                 os.path.basename(config_path)),
                configuration_path=config_path,
                application_status=ApplicationStatus.RUNNING,
                application_host=host,
                completion_time=stat.last_modified,
                trigger_time=parent_data.get('trigger_time', ''),
                error_state=parent_data.get('state', 'unknown'),
                local_mode=parent_data.get('mode', 'unknown'),
                login_user=parent_data.get('login_user', 'Zoom'),
                fqdn=parent_data.get('fqdn', host),
                last_command=self._get_last_command(parent_data),
                pd_disabled=self._get_existing_attribute(path, 'pd_disabled'),
                grayed=self._get_existing_attribute(path, 'grayed')
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

            self._cache.update(message.application_states)
            self._cache.remove_deletes()

            self._message_throttle.add_message(message)

            self._time_estimate_cache.update_states(
                self._cache.application_states)

        except Exception:
            logging.exception('An unhandled Exception has occurred')

    def _on_agent_state_update(self, event):
        """
        This is to capture when an agent goes down.
        :type event: kazoo.protocol.states.WatchedEvent
        """
        host = os.path.basename(event.path)
        path = self._path_to_host_mapping.get(host, None)
        if path is not None:  # if data is in the cache
            self._on_update_path(path)

    def _get_last_command(self, data):
        """
        :type data: dict
        :rtype: str
        """
        if data.get('state', 'Unknown') == 'starting':
            return "Start"
        elif data.get('state', 'Unknown') == 'stopping':
            return "Stop"
        else:
            return ''

    def _get_existing_attribute(self, path, attr, default=False):
        """
        Look in the existing cache for an app state dictionary, and check for
        the value of some key (attr), and return it.
        :type path: str
        :type attr: str
        :param default: the default value to return if the state dict or the
            key (attr) does not exist
        """
        existing_obj = self._cache._application_states.get(path, None)
        if existing_obj is None:
            existing = default
        else:
            existing = existing_obj.get(attr, default)

        return existing