import httplib
import logging
import requests
import socket

from zoom.common.types import PredicateType
from zoom.common.decorators import TimeThis
from zoom.www.messages.timing_estimate import TimeEstimateMessage
from zoom.www.messages.message_throttler import MessageThrottle


class TimeEstimateCache(object):

    def __init__(self, configuration, web_socket_clients):
        """
        :type configuration: zoom.www.config.configuration.Configuration
        :type web_socket_clients: list
        """
        self.configuration = configuration
        self._web_socket_clients = web_socket_clients
        self._message_throttle = MessageThrottle(configuration,
                                                 web_socket_clients)
        self.graphite_cache = {}
        self.dependencies = {}
        self.states = {}
        self._graphite_available = None

    def start(self):
        self._message_throttle.start()

    def stop(self):
        self._message_throttle.stop()

    def reload(self):
        self.graphite_cache.clear()
        self.load()

    def update_states(self, states):
        """
        :type states: dict
        """
        self.states.update(states)
        self.load(send=True)

    def update_dependencies(self, deps):
        """
        :type deps: dict
        """
        self.dependencies.update(deps)
        self.load(send=True)

    @TimeThis(__file__)
    def load(self, send=False):
        """
        :type send: bool
            Whether to send messages to clients.
        :rtype: zoom.www.messages.global_mode_message.TimeEstimateMessage
        """
        logging.debug("Recomputing Timing Estimates...")
        try:
            if self._graphite_available is None:
                self._check_graphite_available()

            message = TimeEstimateMessage()

            cost = self._get_default_data()
            maxpath = "None"
            searchdata = {}

            if self.states and self._graphite_available:
                for path in self.dependencies.iterkeys():
                    data = self._get_max_cost(path, searchdata)
                    if data['max'] > cost['max']:
                        maxpath = path
                    self._get_greatest_cost(cost, data)

            message.update({
                'maxtime': cost['max'],
                'mintime': cost['min'],
                'avetime': cost['ave'],
                'maxpath': maxpath
            })

            if all((send, self.dependencies, self.states)):
                self._message_throttle.add_message(message)

            return message

        except Exception as e:
            logging.exception(e)

    def _check_graphite_available(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.configuration.graphite_host, 80))
            s.close()
            self._graphite_available = True
        except Exception as ex:
            logging.error('Could not connect to {0}:80. Error: {1}.'
                          .format(self.configuration.graphite_host, ex))
            self._graphite_available = False

    def _get_max_cost(self, path, searchdata):
        """
        :type path: str
        :type searchdata: dict
        :rtype: dict
            Example: {'ave': 0, 'max': 0, 'min': 0}
        """
        # init internal search data
        cached_cost = searchdata.get(path, None)
        if cached_cost is not None:
            return cached_cost

        dep_data = self.dependencies.get(path, None)
        greatest_cost = self._get_default_data()

        # take greatest_cost and record the largest cost from all a path's
        # dependencies.
        if dep_data:
            for i in dep_data['dependencies']:
                # expecting: i = {'path': '/foo/bar', 'type': 'baz'}
                if i.get('type').lower() == PredicateType.ZOOKEEPERHASCHILDREN:
                    cached_cost = self._get_max_cost(i.get("path", None), searchdata)
                    self._get_greatest_cost(greatest_cost, cached_cost)

                elif i.get('type').lower() == PredicateType.ZOOKEEPERHASGRANDCHILDREN:
                    grand_path = i.get("path")
                    for key in self.dependencies.iterkeys():
                        if key.lower().startswith(grand_path) and key.lower() != grand_path:
                            cached_cost = self._get_max_cost(key, searchdata)
                            self._get_greatest_cost(greatest_cost, cached_cost)

        # if application is not running, add its cost (from graphite) to the
        # greatest cost of its dependencies
        if (self.states.get(path, None) is not None and
                self.states[path].get('application_status', None) != "running"):
            graphite_data = self.get_graphite_data(path)
            self._add_data(greatest_cost, graphite_data)

        searchdata.update({path: greatest_cost})
        return greatest_cost

    def _get_default_data(self):
        return {'ave': 0, 'max': 0, 'min': 0}

    def _get_greatest_cost(self, d1, d2):
        """
        Update greatest cost values with the greater between the current value
        and the cached value
        """
        for i in ['ave', 'min', 'max']:
            d1[i] = max(d1[i], d2[i])

    def _add_data(self, d1, d2):
        """
        Add an apps own startup time (from graphite) to greatest cost if it is
        not running.
        """
        for i in ['ave', 'min', 'max']:
            d1[i] += d2[i]

    def get_graphite_data(self, path):
        """
        Grab startup times from graphite for a path.
        :type path: str
        :rtype: dict
            Example: {'min': 0, 'max': 0, 'ave': 0}
        """
        if self.graphite_cache.get(path, None) is not None:
            return self.graphite_cache[path]

        try:
            app_path = path.split('/spot/software/state/')[1]
            app_path = app_path.replace('/', '.')
            url = ("http://{0}/render?format=json&from=-7d"
                   "&target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'max'),'max')"
                   "&target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'min'),'min')"
                   "&target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'avg'),'avg')"
                   .format(self.configuration.graphite_host, app_path))

            response = requests.post(url, timeout=5.0)

            self.graphite_cache[path] = self._get_default_data()

            if response.status_code == httplib.OK:
                for data in response.json():
                    if "avg" in data['target']:
                        self.graphite_cache[path]['ave'] = data['datapoints'][0][0]
                    elif "max" in data['target']:
                        self.graphite_cache[path]['max'] = data['datapoints'][-1][0]
                    elif "min" in data['target']:
                        self.graphite_cache[path]['min'] = data['datapoints'][0][0]
                    else:
                        logging.warn("Received graphite data {} with unknown "
                                     "target".format(data))

            return self.graphite_cache[path]

        except Exception:
            logging.exception('Error getting startup data from graphite for '
                              'path: {0}'.format(path))
            return self._get_default_data()
