import httplib
import logging
import requests
from zoom.entities.types import DependencyType
from zoom.messages.timing_estimate import TimeEstimateMessage
from zoom.messages.message_throttler import MessageThrottle


class TimeEstimateCache(object):

    def __init__(self, configuration, web_socket_clients):

        self.graphite_cache = {}
        self.configuration = configuration
        self._web_socket_clients = web_socket_clients
        self.deps = {}
        self.states = {}
        self._message_throttle = MessageThrottle(configuration, web_socket_clients)

    def start(self):
        self._message_throttle.start()

    def stop(self):
        self._message_throttle.stop()

    def reload(self):
        self.graphite_cache.clear()
        self.recompute()

    def update_appplication_states(self, states):
        self.states = states
        self._message_throttle.add_message(self.recompute())

    def update_appplication_deps(self, deps):
        self.deps = deps
        self._message_throttle.add_message(self.recompute())

    def load(self):
        logging.info("Loading Timing Estimates...")
        ret = self.recompute()
        return ret
   
    def recompute(self):
        try:
            message = TimeEstimateMessage()
            maxcost = 0
            maxpath = "None"
            searchdata = {} 

            if self.states != {}:
                for path in self.deps.iterkeys():
                    if self.rec_fn(path, searchdata) > maxcost:
                        maxcost = self.rec_fn(path, searchdata)
                        maxpath = path

            message.update({
                'maxtime' : maxcost,
                'maxpath' : maxpath
            })

            return message

        except Exception as e:
            logging.exception(e)

    def rec_fn(self, path, searchdata):
        #init internal search data
        data = searchdata.get(path, None)
        if data is None:
            data = {'time': None, 'cost': None}
            searchdata.update({path: data})

        if data.get('cost', None) is not None:
            return data['cost']

        #look up running or graphite time
        if(self.states.get(path, None) is not None
           and self.states[path].get('application_status', None) is not None
           and self.states[path]['application_status'] == "running"):
            data['time'] = 0
        else:  # not running, fetch graphite
            data['time'] = self.get_graphtite_data(path)

        #recurse into deps
        dep_data = self.deps.get(path, None)
        if dep_data is None:
            ret = 0
        elif len(dep_data['dependencies']) == 0:
            ret = 0
        else:
            ret = 0
            for i in dep_data['dependencies']:
                if i.get('type').lower() == DependencyType.CHILD:
                    ret = max(ret, self.rec_fn(i.get("path", None), searchdata))
                if i.get('type').lower() == DependencyType.GRANDCHILD:
                    grand_path = i.get("path")
                    for key in self.deps.iterkeys():
                        if key.lower().startswith(grand_path) \
                                and key.lower() != grand_path:
                            ret = max(ret, self.rec_fn(key, searchdata))

        data['cost'] = ret + data['time']

        return data['cost']

    def get_graphtite_data(self, path):
        if self.graphite_cache.get(path, None) is not None:
            return self.graphite_cache[path]

        try:
            url = path.split('/spot/software/state/')[1]
            url = url.replace('/', '.')
            url = 'http://{0}/render?target=aggregateLine(Infrastructure.startup.{1}.runtime)&format=json&from=-5d'.format(self.configuration.graphite_host, url)
            response = requests.post(url, timeout=5.0)
            if response.status_code != httplib.OK:
                self.graphite_cache[path] = 0
                return 0
            else:
                #first and only entry, it's first and only data point,
                # and formatted as [ data, time ]
                self.graphite_cache[path] = response.json()[0]['datapoints'][0][0]

            return self.graphite_cache[path]

        except Exception as e:
            logging.exception(e)
            return 0
