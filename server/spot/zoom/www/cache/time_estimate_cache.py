import httplib
import logging
import requests

from spot.zoom.common.types import PredicateType
from spot.zoom.www.messages.timing_estimate import TimeEstimateMessage
from spot.zoom.www.messages.message_throttler import MessageThrottle


class TimeEstimateCache(object):

    def __init__(self, configuration, web_socket_clients):

        self.graphite_cache = {}
        self.configuration = configuration
        self._web_socket_clients = web_socket_clients
        self.deps = {}
        self.states = {}
        self._message_throttle = MessageThrottle(configuration,
                                                 web_socket_clients)

    def start(self):
        self._message_throttle.start()

    def stop(self):
        self._message_throttle.stop()

    def reload(self):
        self.graphite_cache.clear()
        self.recompute()

    def update_appplication_states(self, states):
        self.states.update(states)
        self.recompute(send=True)

    def update_appplication_deps(self, deps):
        self.deps.update(deps)
        self.recompute(send=True)

    def load(self):
        ret = self.recompute()
        return ret
   
    def recompute(self, send=False):
        logging.info("Recomputing Timing Estimates...")
        try:
            message = TimeEstimateMessage()
            maxtime = 0
            mintime = 0
            avetime = 0
            maxpath = "None"
            searchdata = {} 

            if self.states != {}:
                for path in self.deps.iterkeys():
                    data = self.rec_fn(path, searchdata) 
                    if data['max'] > maxtime:
                        maxtime = data['max']
                        maxpath = path
                    if data['min'] > mintime:
                        mintime = data['min']
                    if data['ave'] > avetime:
                        avetime = data['ave']

            message.update({
                'maxtime': maxtime,
                'mintime': mintime,
                'avetime': avetime,
                'maxpath': maxpath
            })

            if send and self.deps != {} and self.states != {}:
                self._message_throttle.add_message(message)

            return message

        except Exception as e:
            logging.exception(e)

    def rec_fn(self, path, searchdata):
        # init internal search data
        data = searchdata.get(path, None)
        if data is None:
            data = {'time': None, 'cost': None}
            searchdata.update({path: data})

        if data.get('cost', None) is not None:
            return data['cost']

        data['cost'] = {}
        data['cost']['ave'] = 0; 
        data['cost']['min'] = 0; 
        data['cost']['max'] = 0; 

        data['time'] = self.get_graphtite_data(path)

        # recurse into deps
        dep_data = self.deps.get(path, None)
        avet = 0
        mint = 0
        maxt = 0
        if dep_data and \
           len(dep_data['dependencies']) != 0:
            for i in dep_data['dependencies']:
                if i.get('type').lower() == PredicateType.ZOOKEEPERHASCHILDREN:
                    avet = max(avet, self.rec_fn(i.get("path", None),
                                                 searchdata)['ave'])
                    mint = max(mint, self.rec_fn(i.get("path", None),
                                                 searchdata)['min'])
                    maxt = max(maxt, self.rec_fn(i.get("path", None),
                                                 searchdata)['max'])
                if i.get('type').lower() == PredicateType.ZOOKEEPERHASGRANDCHILDREN:
                    grand_path = i.get("path")
                    for key in self.deps.iterkeys():
                        if key.lower().startswith(grand_path) \
                                and key.lower() != grand_path:

                            avet = max(avet, self.rec_fn(key,
                                                         searchdata)['ave'])
                            mint = max(mint, self.rec_fn(key,
                                                         searchdata)['min'])
                            maxt = max(maxt, self.rec_fn(key,
                                                         searchdata)['max'])

        data['cost'] = {}
        # look up running or graphite time
        if(self.states.get(path, None) is not None
           and self.states[path].get('application_status', None) == "running"):
            data['cost']['ave'] = avet 
            data['cost']['min'] = mint 
            data['cost']['max'] = maxt 
        else:  # not running, fetch graphite
            data['cost']['ave'] = avet + data['time']['ave']
            data['cost']['min'] = mint + data['time']['min']
            data['cost']['max'] = maxt + data['time']['max']

        return data['cost']

    def get_graphtite_data(self, path):
        if self.graphite_cache.get(path, None) is not None:
            return self.graphite_cache[path]

        try:
            url = path.split('/spot/software/state/')[1]
            url = url.replace('/', '.')
            url = "http://{0}/render?target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'max'),'max')&target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'min'),'min')&target=alias(aggregateLine(Infrastructure.startup.{1}.runtime,'avg'),'avg')&format=json&from=-5d".format(self.configuration.graphite_host, url)
            response = requests.post(url, timeout=5.0)

            self.graphite_cache[path] = {'min': 0, 'max': 0, 'ave': 0}

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

        except Exception as e:
            logging.exception(e)
            return 0
