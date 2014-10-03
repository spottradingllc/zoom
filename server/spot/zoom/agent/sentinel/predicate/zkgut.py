import logging
import datetime
from time import sleep
from threading import Thread
import json
import re

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate
from spot.zoom.agent.sentinel.common.thread_safe_object import ThreadSafeObject
from spot.zoom.common.decorators import connected


class ZookeeperGoodUntilTime(SimplePredicate):
    def __init__(self, comp_name, settings, zkclient, nodepath, parent=None, interval=5):
        """
        :type comp_name: str
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type parent: str or None
        :type interval: int or float
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self.interval = interval
        self._start = None
        self._stop = None
        self._log = logging.getLogger('sent.{0}.pred.gut'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._started = False

        self._datetime_regex = (
            "^((?P<year>\d{4})\-(?P<month>\d{2})\-(?P<day>\d{2})\s)?"
            "(?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2}))?"
        )

    @property
    def current_time(self):
        return datetime.datetime.now().time()

    @property
    def current_datetime(self):
        return datetime.datetime.now()

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._watch_node()
            self._thread.start()
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.info('Stopping {0}'.format(self))
            self._started = False
            self._operate.set_value(False)
            self._thread.join()
            self._log.info('{0} stopped'.format(self))
        else:
            self._log.debug('Already stopped {0}'.format(self))

    def _run_loop(self):
        while self._operate == True:
            self._process_met()
            sleep(self.interval)
        self._log.info('Done comparing guts.')

    def _process_met(self):
        results = []
        if self._start is not None:
            compare_to_start = self._get_comparison(self._start)
            results.append(self._start < compare_to_start)

        if self._stop is not None:
            compare_to_stop = self._get_comparison(self._stop)
            results.append(compare_to_stop < self._stop)

        if not results:
            results.append(False)

        self.set_met(all(results))  # every comparison returned True

    def _create_dt_dict(self, datetime_string):
        """
        :type datetime_string: str
        :rtype: dict
        """
        regex_dict = dict()
        match = re.search(self._datetime_regex, datetime_string)
        if match:
            regex_dict = dict(year=match.group('year'),
                              month=match.group('month'),
                              day=match.group('day'),
                              hour=match.group('hour'),
                              minute=match.group('minute'),
                              second=match.group('second'))

        for k, v in regex_dict.iteritems():
            if v is not None:
                regex_dict[k] = int(v)

        self._log.debug('dt_dict returning {0}'.format(regex_dict))
        return regex_dict

    def _get_comparison(self, obj):
        if isinstance(obj, datetime.datetime):
            return self.current_datetime
        elif isinstance(obj, datetime.time):
            return self.current_time

    def _get_datetime_object(self, data):
        """
        :type data: str
        :rtype: datetime.datetime or datetime.time or None
        """
        dt_object = None
        dt_dict = self._create_dt_dict(data)
        try:
            # All of year, month and day are not None
            if all([dt_dict.get(i, None) is not None
                    for i in ('year', 'month', 'day')]):
                dt_object = datetime.datetime(year=dt_dict['year'],
                                              month=dt_dict['month'],
                                              day=dt_dict['day'],
                                              hour=dt_dict['hour'],
                                              minute=dt_dict['minute'],
                                              microsecond=0)

                if dt_dict.get('second', None) is not None:
                    dt_object.replace(second=dt_dict['second'])

            # both hour and minute are not None
            elif all([dt_dict.get(i, None) is not None
                      for i in ('hour', 'minute')]):
                dt_object = datetime.time(hour=dt_dict['hour'],
                                          minute=dt_dict['minute'],
                                          microsecond=0)
                if dt_dict.get('second', None) is not None:
                    dt_object.replace(second=dt_dict['second'])
            else:
                self._log.error('data "{0}" did not match regex'.format(data))

        except (ValueError, TypeError) as ex:
            self._log.error('Problem with parsing data "{0}": {1}'
                            .format(data, ex))
        finally:
            return dt_object

    def _parse_data(self, gut_data):
        """
        :type gut_data: dict
        """
        start_data = gut_data.get(u'start', None)
        self._log.debug('raw start from zk is "{0}"'.format(start_data))
        if start_data is not None:
            self._start = self._get_datetime_object(start_data)
            
        stop_data = gut_data.get(u'stop', None)
        self._log.debug('raw stop from zk is "{0}"'.format(stop_data))

        if stop_data is not None:
            self._stop = self._get_datetime_object(stop_data)

        if start_data is None and stop_data is None:
            self._log.error('Start and Stop time not specified!')
        
        self._log.info('The current time is: {0}. Start time is: {1}. '
                       'Stop time is: {2}'
                       .format(self.current_time, self._start, self._stop))
    
    @connected
    def _watch_node(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        try:
            exists = self.zkclient.exists(self.node, watch=self._watch_node)
            if exists:
                data, stat = self.zkclient.get(self.node,
                                               watch=self._watch_node)
                j = json.loads(data)
                self._parse_data(j)
            else:
                self._log.info('No gut node was found. Watcher is set at {0}'
                               .format(self.node))
        except ValueError as ex:
            self._log.error('Invalid GUT JSON object: {0}'.format(ex))
        finally:
            self._process_met()

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, start="{3}", stop="{4}", '
                'zkpath={5}, met={6})'.format(self.__class__.__name__,
                                              self._comp_name,
                                              self._parent,
                                              self._start,
                                              self._stop,
                                              self.node,
                                              self._met)
                )
    
    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.node == getattr(other, 'node', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.node != getattr(other, 'node', None)
        ])
