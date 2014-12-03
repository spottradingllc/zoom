import logging
import datetime
from time import sleep
from threading import Thread
import re

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.entities.thread_safe_object import ThreadSafeObject


class PredicateTime(SimplePredicate):
    """
    Predicate for comparing current time to start/stop times.
    It will set the 'met' value based on start > current_time > stop.
    """
    def __init__(self, comp_name, settings,
                 start=None, stop=None, weekdays=None, parent=None, interval=5):
        """
        :type comp_name: str
        :type settings: ThreadSafeObject
        :type start: str or None
        :type stop: str or None
        :type weekdays: str or None
        :type parent: str or None
        :type interval: int or float
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.start_time = self._get_datetime_object(start)
        self.stop_time = self._get_datetime_object(stop)
        self.day_range = self._parse_range(weekdays)
        self.interval = interval
        self._log = logging.getLogger('sent.{0}.pred.time'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run_loop, name=str(self))
        self._thread.daemon = True
        self._started = False

    def weekday(self):
        """
        :rtype: int
            0=Monday, 1=Tuesday, etc.
        """
        return datetime.date.today().weekday()

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
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
        self._log.info('Done comparing times.')

    def _process_met(self):
        results = []
        if self.start_time is not None:
            compare_to_start = self._get_comparison(self.start_time)
            results.append(self.start_time < compare_to_start)

        if self.stop_time is not None:
            compare_to_stop = self._get_comparison(self.stop_time)
            results.append(compare_to_stop < self.stop_time)

        if self.day_range is not None:
            results.append(self.weekday() in self.day_range)

        if not results:
            results.append(False)

        self.set_met(all(results))  # every comparison returned True

    def _create_dt_dict(self, datetime_string):
        """

        :type datetime_string: str
        :rtype: dict
        """
        datetime_regex = (
            "^((?P<year>\d{4})\-(?P<month>\d{2})\-(?P<day>\d{2})\s)?"
            "(?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2}))?"
        )
        regex_dict = dict()
        match = re.search(datetime_regex, datetime_string)
        if match:
            regex_dict = dict(year=match.group('year'),
                              month=match.group('month'),
                              day=match.group('day'),
                              hour=match.group('hour'),
                              minute=match.group('minute'),
                              second=match.group('second'))

        # convert all values to integers
        for k, v in regex_dict.iteritems():
            if v is not None:
                regex_dict[k] = int(v)

        self._log.debug('dt_dict returning {0}'.format(regex_dict))
        return regex_dict

    def _get_comparison(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime.datetime.now()
        elif isinstance(obj, datetime.time):
            return datetime.datetime.now().time()

    def _get_datetime_object(self, data):
        """
        Create datetime object from string value
        :type data: str or None
        :rtype: datetime.datetime or datetime.time or None
        """
        if data is None:
            return

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
                self._log.error(
                    'data "{0}" did not match regex. This will result in the '
                    'paramter returning as None. The predicate will never be '
                    'met for this parameter. '.format(data))

        except (ValueError, TypeError) as ex:
            self._log.error('Problem with parsing data "{0}": {1}'
                            .format(data, ex))
        finally:
            return dt_object

    def _parse_range(self, astr):
        """
        https://www.darklaunch.com/2012/11/05/python-parse-range-and-parse-group-range
        Return a range list given a string.
        As this is for weekdays, only return 0-6

        :type astr: str or None
        :rtype: list or None
        """
        if astr is None:
            return None

        try:
            result = set()
            for part in astr.split(','):
                x = part.split('-')
                result.update(range(int(x[0]), int(x[-1]) + 1))

            # only accept 0-6
            return [i for i in sorted(result) if 0 <= i <= 6]
        except ValueError:
            self._log.warning('Error parsing day range. Returning [].')
            return None

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, start="{3}", '
                'stop="{4}", days={5}, started={6}, met={7})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.start_time,
                        self.stop_time,
                        self.day_range,
                        self.started,
                        self._met))

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.start_time == getattr(other, 'start_time', None),
            self.stop_time == getattr(other, 'stop_time', None),
            self.day_range == getattr(other, 'day_range', None),
            self.interval == getattr(other, 'interval', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.start_time != getattr(other, 'start_time', None),
            self.stop_time != getattr(other, 'stop_time', None),
            self.day_range != getattr(other, 'day_range', None),
            self.interval != getattr(other, 'interval', None)
        ])
