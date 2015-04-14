import logging
import time

from xml.etree import ElementTree
from kazoo.exceptions import NoNodeError

from zoom.agent.predicate.time_window import TimeWindow
from zoom.agent.util.helpers import verify_attribute
from zoom.common.decorators import connected_with_return, TimeThis
from zoom.common.types import PredicateType, Weekdays
from zoom.www.messages.application_dependencies \
    import ApplicationDependenciesMessage
from zoom.www.messages.message_throttler import MessageThrottle
from zoom.agent.util.helpers import zk_path_join


class ApplicationDependencyCache(object):
    def __init__(self, configuration, zoo_keeper, web_socket_clients,
                 time_estimate_cache):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type zoo_keeper: zoom.www.zoo_keeper.ZooKeeper
        :type web_socket_clients: list
        """
        self._cache = ApplicationDependenciesMessage()
        self._configuration = configuration
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
        :rtype: ApplicationDependenciesMessage
        """
        try:
            if not self._cache.application_dependencies:
                self._load()

            return self._cache
        except Exception:
            logging.exception('An unhandled Exception has occurred')

    def reload(self):
        """
        Clear cache, and re-walk agent config path.
        """
        self._cache.clear()
        logging.info("Application dependency cache cleared")
        self._on_update_path(self._configuration.agent_configuration_path)

    @TimeThis(__file__)
    def _load(self):
        """
        Walk full agent config path to get data. Load self._cache object
        """
        self._cache.clear()

        self._walk(self._configuration.agent_configuration_path, self._cache)
        logging.info("Application dependency cache loaded from ZooKeeper {0}"
                     .format(self._configuration.agent_configuration_path))

        self._recalc_downstream_dependencies()

        self._time_estimate_cache.update_dependencies(
            self._cache.application_dependencies)

    @connected_with_return(None)
    def _walk(self, path, result):
        """
        :type path: str
        :type result: ApplicationDependenciesMessage
        """
        try:
            children = self._zoo_keeper.get_children(path,
                                                     watch=self._on_update)

            if children:
                for child in children:
                    self._walk(zk_path_join(path, child), result)
            else:
                self._get_application_dependency(path, result)
        except NoNodeError:
            logging.debug('Node at {0} no longer exists.'.format(path))

    def _get_application_dependency(self, path, result):
        """
        Load result object with application dependencies
        :type path: str
        :type result: ApplicationDependenciesMessage
        """
        if self._zoo_keeper.exists(path):
            data, stat = self._zoo_keeper.get(path, watch=self._on_update)
            if not data:
                return

            try:
                root = ElementTree.fromstring(data)

                for node in root.findall('Automation/Component'):

                    app_id = node.attrib.get('id')
                    registrationpath = node.attrib.get('registrationpath', None)

                    if registrationpath is None:
                        registrationpath = zk_path_join(
                            self._configuration.application_state_path, app_id)

                    start_action = node.find('Actions/Action[@id="start"]')

                    if start_action is None:
                        logging.warn("No Start Action Found for {0}"
                                     .format(registrationpath))
                        continue

                    dependencies = self._parse_dependencies(start_action)

                    data = {
                        "configuration_path": registrationpath,
                        "dependencies": dependencies,
                        "downstream": list()
                    }

                    result.update({registrationpath: data})

            except Exception:
                logging.exception('An unhandled exception occurred')

        else:
            logging.warn("config path does not exist: {0}".format(path))

    def _parse_dependencies(self, action):
        """
        Parse dependencies out of XML
        :type action: xml.etree.ElementTree.Element
        :rtype: list
        """
        # TODO: rename 'path' when it really isn't a path. this is a hack...
        # prev_was_not keeps track of whether the outer class was 'not'
        dependencies = []
        prev_was_not = False
        for predicate in action.iter('Predicate'):
            pred_type = predicate.get('type').lower()
            pred_path = predicate.get('path', None)
            # pred_oper = predicate.get('operational', False)
            pred_oper = bool(verify_attribute(predicate, 'operational',
                                              none_allowed=True))
            if pred_type == PredicateType.ZOOKEEPERHASCHILDREN:
                dependencies.append({'type': pred_type,
                                     'path': pred_path,
                                     'operational': pred_oper})
                prev_was_not = False
            elif pred_type == PredicateType.ZOOKEEPERHASGRANDCHILDREN:
                dependencies.append({'type': pred_type,
                                     'path': pred_path,
                                     'operational': pred_oper})
                prev_was_not = False
            elif pred_type == PredicateType.ZOOKEEPERGOODUNTILTIME:
                if len(pred_path.split('gut/')) > 1:
                    dependencies.append(
                        {'type': pred_type,
                         'path': ("I should be up between: {0}"
                                  .format(pred_path.split("gut/")[1])),
                         'operational': pred_oper})
                else:
                    logging.debug('Invalid GUT path: {0}'.format(pred_path))
                prev_was_not = False
            elif pred_type == PredicateType.HOLIDAY:
                dependencies.append(
                    {'type': pred_type,
                     'path': ("Does NOT run on holidays" if prev_was_not
                              else "Runs on holidays"),
                     'operational': pred_oper})
                prev_was_not = False
            elif pred_type == PredicateType.WEEKEND:
                dependencies.append(
                    {'type': pred_type,
                     'path': ("Does NOT run on weekends" if prev_was_not
                              else "Runs on weekends"),
                     'operational': pred_oper})
                prev_was_not = False
            elif pred_type == PredicateType.TIMEWINDOW:
                begin = predicate.get('begin', None)
                end = predicate.get('end', None)
                weekdays = predicate.get('weekdays', None)
                msg = 'I should be up '
                if begin is not None:
                    msg += 'after: {0} '.format(begin)
                if end is not None:
                    msg += 'until: {0}'.format(end)
                # only send dependency if there is something to send
                if begin is not None or end is not None:
                    dependencies.append({'type': pred_type, 'path': msg,
                                         'operational': pred_oper})

                # pretend this is a weekend predicate for convenience
                if weekdays is not None:
                    day_range = TimeWindow.parse_range(weekdays)
                    if Weekdays.SATURDAY in day_range or \
                                    Weekdays.SUNDAY in day_range:
                        wk_msg = 'Runs on weekends'
                    else:
                        wk_msg = 'Does NOT run on weekends'

                    dependencies.append({'type': PredicateType.WEEKEND,
                                         'path': wk_msg,
                                         'operational': pred_oper})

            elif pred_type == PredicateType.NOT:
                prev_was_not = True

        return dependencies

    @TimeThis(__file__)
    def _recalc_downstream_dependencies(self, tries=0):
        """
        Loop over existing cache and link upstream with downstream elements
        """
        # clear existing downstream
        try:
            for data in self._cache.application_dependencies.itervalues():
                downstream = data.get('downstream')
                del downstream[:]

            dep_copy = self._cache.application_dependencies.copy()
            for path, data in dep_copy.iteritems():
                for key, value in self._cache.application_dependencies.iteritems():
                    for dep in data.get('dependencies'):
                        if dep['type'] == PredicateType.ZOOKEEPERHASGRANDCHILDREN:
                            if key.startswith(dep['path']):
                                value.get('downstream').append(path)
                        elif dep['type'] == PredicateType.ZOOKEEPERHASCHILDREN:
                            if dep['path'] == key:
                                value.get('downstream').append(path)
        except RuntimeError:
            time.sleep(1)
            tries += 1
            if tries < 3:
                self._recalc_downstream_dependencies(tries=tries)

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
            self._recalc_downstream_dependencies()

            self._cache.update(message.application_dependencies)

            self._message_throttle.add_message(message)

            self._time_estimate_cache.update_dependencies(
                self._cache.application_dependencies)

        except Exception:
            logging.exception('An unhandled Exception has occurred')
