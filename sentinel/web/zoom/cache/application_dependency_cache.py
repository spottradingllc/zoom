import logging
import os.path

import xml.etree.ElementTree as ET
from kazoo.exceptions import NoNodeError
from zoom.entities.types import DependencyType
from zoom.messages.application_dependencies import ApplicationDependenciesMessage


class ApplicationDependencyCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 agent_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        :type agent_cache: zoom.cache.agent_cache.AgentCache
        """
        self._cache = ApplicationDependenciesMessage();
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients

    def load(self):
        """
        :rtype: dict
        """
        try:
            if not len(self._cache):
               self._load()

            return self._cache
        except Exception:
            logging.exception('An unhandled Exception has occurred')

    def reload(self):
        self._cache.clear()
        logging.info("Application dependency cache cleared")
        self._on_update_path(self._configuration.agent_configuration_path)

    def _load(self):
        """
        :rtype: dict
        """
        self._cache.clear()

        self._walk(self._configuration.agent_configuration_path, self._cache)
        logging.info("Application dependency cache loaded from ZooKeeper {0}"
                     .format(self._configuration.agent_configuration_path))

    def _walk(self, path, result_dict):
        """
        :type path: str
        :type result_dict: dict
        """
        try:
            children = self._zoo_keeper.get_children(path, watch=self._on_update)

            if children:
                for child in children:
                    self._walk(os.path.join(path, child), result_dict)
            else:
                depend = self._get_application_dependency(path, result_dict)
        except NoNodeError:
            logging.debug('Node at {0} no longer exists.'.format(path))

    def _get_application_dependency(self, path, result_dict):
        """
        :type path: str
        """
        data = None

        if self._zoo_keeper.exists(path):
            data, stat = self._zoo_keeper.get(path, watch=self._on_update)
            if data is None: return
            if data == "": return

            try:
                root = ET.fromstring(data)

                for node in root.findall('Automation/Component'):

                    result = {}
                    dependencies = []
                    registrationpath = None

                    if node.attrib.get('id') is not None:
                        registrationpath = self._configuration.application_state_path + '/' + node.attrib['id']
                    if node.attrib.get('registrationpath') is not None:
                        registrationpath = node.attrib['registrationpath']

                    if registrationpath is None:
                        logging.error("no entry found!")
                        continue

                    result.update({"configuration_path": registrationpath})

                    start_action = node.find('Actions/Action[@id="start"]')

                    if start_action is None: 
                        logging.warn("No Start Action Found for {}".format(registrationpath))
                        continue

                    for predicate in start_action.iter('Predicate'):
                        if predicate.get('type').lower() == DependencyType.CHILD:
                            dict = {'type' : DependencyType.CHILD, 'path' : predicate.get("path")}
                            dependencies.append(dict)
                        if predicate.get('type').lower() == DependencyType.GRANDCHILD:
                            dict = {'type' : DependencyType.GRANDCHILD, 'path' : predicate.get("path")}
                            dependencies.append(dict)

                    result.update({"dependencies": dependencies})

                    result_dict.update({registrationpath: result})

            except Exception as e:
                logging.exception(e)

        else:
            logging.warn("config path DNE: " + path)

    def _on_update(self, event):
        """
        Callback to send updates via websocket on application state changes.
        :type event: kazoo.protocol.states.WatchedEvent
        """
        self._on_update_path(event.path)

    def _on_update_path(self, path):
        try:
            message = ApplicationDependenciesMessage()

            self._walk(path, message)

            self._cache.update(message.application_dependencies)

            logging.debug('Sending dependency update: {0}'.format(message.to_json()))

            for client in self._web_socket_clients:
                client.write_message(message.to_json())

        except Exception:
            logging.exception('An unhandled Exception has occurred')
