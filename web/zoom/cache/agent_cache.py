import logging
import json
import os.path
from kazoo.exceptions import NoNodeError
from collections import namedtuple


class AgentCache(object):
    def __init__(self, configuration, zoo_keeper):
        """
        :type configuration: zoom.config.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._update_callbacks = list()
        self._cache_by_host = dict()
        self._cache_by_path = dict()

    def add_callback(self, cb):
        self._update_callbacks.append(cb)

    def load(self, callback=None):
        """
        :type callback: types.funcType
        """
        self._cache_by_host.clear()
        self._cache_by_path.clear()

        agents = self._zoo_keeper.client.get_children(
            self._configuration.agent_state_path
        )
        for agent in agents:
            self._update_cache(str(agent), send_update=False)


    def get_agent_data(self, agent, callback=None):
        """
        :type agent: str
        :type callback: types.funcType
        :rtype: dict
        """
        result = dict()
        agent_path = os.path.join(self._configuration.agent_state_path, agent)
        try:
            data, stat = self._zoo_keeper.client.get(agent_path, watch=callback)
            result = json.loads(data)
        except ValueError:
            logging.error('Error parsing data at {0}'.format(agent_path))
        except NoNodeError:
            logging.warning('Node does not exist at {0}'.format(agent_path))
        finally:
            return result

    def get_app_data_by_path(self, path, callback=None):
        return self._cache_by_path.get(path, {})

    def get_host_by_path(self, path):
        data = self.get_app_data_by_path(path)
        return data.get('host', None)

    def _update_cache(self, arg, send_update=True):
        """
        :param arg: str or kazoo.protocol.states.WatchedEvent
        :param send_update: bool
        """
        updates_to_send = list()
        if not isinstance(arg, str):
            agent = os.path.basename(arg.path)
        else:
            agent = arg

        data = self.get_agent_data(agent, callback=self._update_cache)
        self._cache_by_host[agent] = data
        for app_data in data.values():
            key = app_data.get('register_path')
            updates_to_send.append(key)
            self._cache_by_path[key] = app_data

        if send_update:
            FakeWatchedEvent = namedtuple('WatchedEvent',
                                          ('type', 'state', 'path'))
            for path in updates_to_send:
                update = FakeWatchedEvent(None, None, path)
                for callback in self._update_callbacks:
                    callback(update)