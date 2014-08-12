import logging
import os.path

from xml.etree import ElementTree

from kazoo.exceptions import NoNodeError

from spot.zoom.core.entities.types import DependencyType
from spot.zoom.core.messages.application_dependencies import ApplicationDependenciesMessage
from spot.zoom.core.messages.message_throttler import MessageThrottle


class ApplicationDependencyCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 time_estimate_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        """
        self._cache = ApplicationDependenciesMessage()
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._web_socket_clients = web_socket_clients
        self._time_estimate_cache = time_estimate_cache;
        self._message_throttle = MessageThrottle(configuration, web_socket_clients)

    def start(self):
        self._message_throttle.start()

    def stop(self):
        self._message_throttle.stop()

    def load(self):
        """
        :rtype: ApplicationDependenciesMessage
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

        self._time_estimate_cache.update_appplication_deps(self._cache.application_dependencies)

    def _walk(self, path, result_dict):
        """
        :type path: str
        :type result_dict: ApplicationDependenciesMessage
        """
        try:
            children = self._zoo_keeper.get_children(path, watch=self._on_update)

            if children:
                for child in children:
                    self._walk(os.path.join(path, child), result_dict)
            else:
                # are we not doing anything with this?
                depend = self._get_application_dependency(path, result_dict)
        except NoNodeError:
            logging.debug('Node at {0} no longer exists.'.format(path))

    def _get_application_dependency(self, path, result_dict):
        """
        :type path: str
        """
        if self._zoo_keeper.exists(path):
            data, stat = self._zoo_keeper.get(path, watch=self._on_update)
            if data is None:
                return
            if data == "":
                return

            try:
                root = ElementTree.fromstring(data)

                for node in root.findall('Automation/Component'):

                    result = {}
                    dependencies = []
                    registrationpath = None

                    if node.attrib.get('id') is not None:
                        registrationpath = os.path.join(self._configuration.application_state_path, node.attrib['id'])
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
                            d = {'type': DependencyType.CHILD, 'path': predicate.get("path")}
                            dependencies.append(d)
                        if predicate.get('type').lower() == DependencyType.GRANDCHILD:
                            d = {'type': DependencyType.GRANDCHILD, 'path': predicate.get("path")}
                            dependencies.append(d)

                    result.update({"dependencies": dependencies})

                    result_dict.update({registrationpath: result})

            except Exception as e:
                logging.exception(e)

        else:
            logging.warn("config path DNE: {0}".format(path))

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

            self._message_throttle.add_message(message)

            self._time_estimate_cache.update_appplication_deps(self._cache.application_dependencies)

        except Exception:
            logging.exception('An unhandled Exception has occurred')
