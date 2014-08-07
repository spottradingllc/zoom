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
        self._cache_by_path = dict()
        self._cache_by_host = dict()

    def start(self):
        pass

    def stop(self):
        pass

    def add_callback(self, cb):
        self._update_callbacks.append(cb)

    def load(self):
        """
        Get agent data from Zookeeper
        """
        agents = self._zoo_keeper.get_children(
            self._configuration.agent_state_path,
            watch=self._identify_change
        )

        for agent in agents:
            self._update_cache(str(agent), run_callbacks=False)

    def reload(self):
        """
        Clear existing and query for new data.
        """
        self._cache_by_path.clear()
        self._cache_by_host.clear()
        self.load()

    def get_agent_data(self, agent, callback=None):
        """
        Get agent data from Zookeeper
        :type agent: str
        :type callback: types.funcType or None
        :rtype: dict
        """
        result = None
        agent_path = os.path.join(self._configuration.agent_state_path, agent)
        try:
            data, stat = self._zoo_keeper.get(agent_path, watch=callback)
            result = json.loads(data)

        except ValueError:
            logging.error('Error parsing data at {0}'.format(agent_path))
        except NoNodeError:
            logging.info('Node does not exist at {0}'.format(agent_path))
        finally:
            return result

    def get_app_data_by_path(self, path):
        """
        :rtype: dict
        """
        return self._cache_by_path.get(path, {})

    def get_host_by_path(self, path):
        """
        :rtype: str or None
        """
        data = self.get_app_data_by_path(path)
        return data.get('host', None)

    def get_paths_by_host(self, host):
        """
        :rtype: list
        """
        data = self._cache_by_host.get(host, {})
        return [app_data.get('register_path') for app_data in data.values()]

    def _identify_change(self, event):
        """
        Watch callback for the agent state path to catch when agents are added
        and deleted. This is a supplement to the existing data watches.

        :type event: kazoo.protocol.states.WatchedEvent
        """
        agents = self._zoo_keeper.get_children(event.path,
                                               watch=self._identify_change)
        changes = set(agents).symmetric_difference(set(self._cache_by_host.keys()))

        for agent in changes:
            self._update_cache(str(agent), run_callbacks=True)

    def _update_cache(self, arg, run_callbacks=True):
        """
        :type arg: str or kazoo.protocol.states.WatchedEvent
        :type run_callbacks: bool
        """
        updates_to_send = list()
        if not isinstance(arg, str):
            agent = os.path.basename(arg.path)
        else:
            agent = arg

        data = self.get_agent_data(agent, callback=self._update_cache)

        if data:
            self._cache_by_host[agent] = data
            for app_data in data.values():
                path = app_data.get('register_path')
                updates_to_send.append(path)
                self._cache_by_path[path] = app_data

        else:
            # find paths to update from cached data
            for path in self.get_paths_by_host(agent):
                updates_to_send.append(path)
                self._cache_by_path[path]['mode'] = "unknown"
                self._cache_by_path[path]['state'] = "unknown"

        if run_callbacks:
            self._run_update_callbacks(updates_to_send)

    def _run_update_callbacks(self, updates):
        """
        Run update callback for each item in update list
        :type updates: list of str
        """
        FakeWatchedEvent = namedtuple('WatchedEvent',
                                      ('type', 'state', 'path'))
        for path in updates:
            update = FakeWatchedEvent(None, None, path)
            for callback in self._update_callbacks:
                callback(update)
