import logging
import os.path
import json

from kazoo.exceptions import NoNodeError

from zoom.common.decorators import connected_with_return, TimeThis
from zoom.common.types import ApplicationStatus
from zoom.www.entities.application_state import ApplicationState
from zoom.www.messages.application_states import ApplicationStatesMessage
from zoom.www.messages.message_throttler import MessageThrottle
from zoom.agent.util.helpers import zk_path_join


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

    @property
    def host_mapping(self):
        return self._path_to_host_mapping

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

    @TimeThis(__file__)
    def _load(self):
        self._cache.clear()

        self._walk(self._configuration.application_state_path, self._cache)
        logging.info("Application state cache loaded from ZooKeeper {0}"
                     .format(self._configuration.application_state_path))

        self._time_estimate_cache.update_states(
            self._cache.application_states)
        self._cache.remove_deletes()

    def _build_default_override_store(self):
        logging.debug('Override storage node not found, creating')
        _template = {}
        self._zoo_keeper.create(self._configuration.override_node,
                                json.dumps(_template), makepath=True)

    def _update_override_info(self, path, override_key, override_value):
        """
        Update zookeeper with override values passed in
        """
        logging.debug("_update_override_info: path: {0}, override_key: {1} override_value: {2}"
                      .format(path, override_key, override_value))
        try:
            override_str, stat = self._zoo_keeper.get(self._configuration.override_node)
            override_dict = json.loads(override_str)

            update = {override_key: override_value}
            state = override_dict.get(path, {})
            state.update(update)
            override_dict.update({path: state})

            self._zoo_keeper.set(self._configuration.override_node,
                                 json.dumps(override_dict))
        except NoNodeError as err:
            logging.debug('Unable to find {0}, {1}'
                          .format(self._configuration.override_node, err))
            self._build_default_override_store()
            self._update_override_info(path, override_key, override_value)

    def manual_update(self, path, key, value):
        """
        Manual override from client of specific value
        :type path: str
        :param key: str
        """
        # Set the permanent storage

        state = self._cache._application_states.get(path, None)
        if state is not None:
            self._update_override_info(path, key, value)
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
                    self._walk(zk_path_join(path, child), result)
            else:
                app_state = self._get_application_state(path)
                result.update(
                    {app_state.configuration_path: app_state.to_dictionary()}
                )

        except NoNodeError:
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

        if rawData:  # if '' or None
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
            name = data.get('name', os.path.basename(path))
            agent_path = zk_path_join(self._configuration.agent_state_path,
                                      host)

            # if the agent is down, update state and mode with unknown
            agent_up = bool(self._zoo_keeper.exists(
                agent_path,
                watch=self._on_agent_state_update))

            valid = True
            if host in (None, 'Unknown'):
                data['state'] = 'invalid'
                data['mode'] = 'unknown'
                valid = False
            elif not agent_up:
                data['state'] = 'unknown'
                data['mode'] = 'unknown'
                valid = False
            elif agent_up:
                d, s = self._zoo_keeper.get(agent_path)
                registered_comps = json.loads(d).get('components', [])
                if name not in registered_comps:
                    data['state'] = 'invalid'
                    data['mode'] = 'unknown'
                    valid = False

            self._update_mapping(host, {path: valid})

            application_state = ApplicationState(
                application_name=name,
                configuration_path=path,
                application_status=ApplicationStatus.STOPPED,
                application_host=host,
                last_update=stat.last_modified,
                start_stop_time=data.get('start_stop_time', ''),
                error_state=data.get('state', 'unknown'),
                local_mode=data.get('mode', 'unknown'),
                login_user=data.get('login_user', 'Zoom'),
                read_only=data.get('read_only', False),
                last_command=self._get_last_command(data),
                pd_disabled=self._get_existing_attribute(path, 'pd_disabled'),
                grayed=self._get_existing_attribute(path, 'grayed'),
                platform=data.get('platform', 'unknown'),
                restart_count=data.get('restart_count', 0),
                load_times=self._time_estimate_cache.get_graphite_data(path)
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

            self._update_mapping(host, {config_path: True})

            application_state = ApplicationState(
                application_name=parent_data.get('name',
                                                 os.path.basename(config_path)),
                configuration_path=config_path,
                application_status=ApplicationStatus.RUNNING,
                application_host=host,
                last_update=stat.last_modified,
                start_stop_time=parent_data.get('start_stop_time', ''),
                error_state=parent_data.get('state', 'unknown'),
                local_mode=parent_data.get('mode', 'unknown'),
                login_user=parent_data.get('login_user', 'Zoom'),
                read_only=parent_data.get('read_only', False),
                last_command=self._get_last_command(parent_data),
                pd_disabled=self._get_existing_attribute(config_path, 'pd_disabled'),
                grayed=self._get_existing_attribute(config_path, 'grayed'),
                platform=parent_data.get('platform', 'unknown'),
                restart_count=parent_data.get('restart_count', 0),
                load_times=self._time_estimate_cache.get_graphite_data(config_path)
            )

        return application_state

    def _update_mapping(self, host, data):
        """
        :type host: str
        :type data: dict
            {'/some/path', bool}
        """
        d = self._path_to_host_mapping.get(host, {})
        d.update(data)
        self._path_to_host_mapping[host] = d

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
        logging.info('Agent on host {0} has changed up/down state.'.format(host))
        paths = self._path_to_host_mapping.get(host, {})
        for p in paths.keys():
            self._on_update_path(p)

    def _get_last_command(self, data):
        """
        :type data: dict
        :rtype: str
        """
        if data.get('state', 'Unknown') in ['starting', 'started']:
            return "Start"
        elif data.get('state', 'Unknown') in ['stopping', 'stopped']:
            return "Stop"
        else:
            return ''

    def _get_existing_attribute(self, path, attr):
        """
        Look for existing value for some value in the app state cache.
        If there is an override value, use that. Else use the existing state.
        :type path: str
        :type attr: str
        """
        state = self._cache._application_states.get(path, None)
        override = {}

        try:
            data, stat = self._zoo_keeper.get(self._configuration.override_node)
            override = json.loads(data)
        except (TypeError, ValueError) as err:
            logging.critical('There was a problem returning values from the '
                             'override cache: {0}'.format(err))

        setting = override.get(path, {}).get(attr, None)

        if setting is not None:
            return setting
        elif state is None:
            return None
        else:
            return state.get(attr)

